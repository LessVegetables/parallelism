"""
Real-time (camera):
    python main.py                        # camera 0, default thread count
    python main.py --camera 1             # different camera index
    python main.py --threads 4            # fixed thread count
    python main.py --threads 4 --save out.mp4

Offline (video file) – used for benchmarking, processes every frame:
    python main.py --input test.mp4 --threads 4 --save out_multi.mp4
"""

import argparse
import time
import threading
import queue
from collections import OrderedDict

import cv2
import torch
from ultralytics import YOLO



# RAII wrappers
class CameraCapture:
    """RAII wrapper around cv2.VideoCapture for a live camera."""

    def __init__(self, index: int = 0):
        self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {index}")
        # Request 640×480 from the driver (best-effort)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    @property
    def width(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def fps(self):
        return self._cap.get(cv2.CAP_PROP_FPS) or 30.0

    def read(self):
        return self._cap.read()

    def __del__(self):
        self._cap.release()


class VideoWriter:
    """RAII wrapper around cv2.VideoWriter."""

    def __init__(self, path: str, fps: float, width: int, height: int):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
        if not self._writer.isOpened():
            raise RuntimeError(f"Cannot open VideoWriter at: {path}")

    def write(self, frame):
        self._writer.write(frame)

    def __del__(self):
        self._writer.release()



# Worker thread
def worker(input_q: queue.Queue, output_q: queue.Queue, stop_event: threading.Event,
           ready_barrier: threading.Barrier | None = None):
    """
    Each worker owns its own YOLO instance (thread-safe per ultralytics docs).
    Reads  (seq_id, frame)   from input_q.
    Writes (seq_id, annotated) to output_q.

    If a ready_barrier is given, the worker loads its model and then waits on the
    barrier before processing.  This lets the caller exclude (one-off) model-load
    time from a timed run, so benchmark numbers reflect inference only.
    """
    torch.set_num_threads(1)
    model = YOLO("yolov8s-pose.pt")
    if ready_barrier is not None:
        ready_barrier.wait()
    while not stop_event.is_set():
        try:
            item = input_q.get(timeout=0.1)
        except queue.Empty:
            continue
        if item is None:
            input_q.task_done()
            break
        seq_id, frame = item
        results = model(frame, verbose=False) # allegadly spawns abt 4 threads to compute one frame —> which is why on my 8core cpu setting --thread 2 is the fastest option
        annotated = results[0].plot()
        output_q.put((seq_id, annotated))
        input_q.task_done()



# Real-time pipeline
def run_realtime(camera_index: int, num_threads: int, save_path: str | None):
    cam = CameraCapture(camera_index)
    width, height, fps = cam.width, cam.height, cam.fps
    print(f"Camera: {width}x{height} @ {fps:.1f} fps  |  Workers: {num_threads}")

    writer = VideoWriter(save_path, fps, width, height) if save_path else None

    input_q: queue.Queue  = queue.Queue(maxsize=num_threads * 4)
    output_q: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    # Start worker threads
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(
            target=worker, args=(input_q, output_q, stop_event), daemon=True
        )
        t.start()
        threads.append(t)

    # display / stats state
    pending: OrderedDict = OrderedDict()   # seq_id, annotated frame (reorder buffer)
    next_display_id = 0                    # next frame index to show

    seq_counter = 0
    frame_times = []
    t_last_fps = time.perf_counter()
    display_fps = 0.0

    print("Press Q or ESC to quit.")

    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                break

            # Push to workers (drop frame if queue is full — keeps latency low)
            try:
                input_q.put_nowait((seq_counter, frame))
                seq_counter += 1
            except queue.Full:
                pass  # skip this frame rather than stall

            # Drain output queue into reorder buffer
            while not output_q.empty():
                sid, ann = output_q.get_nowait()
                pending[sid] = ann

            # Display frames in order
            while next_display_id in pending:
                ann = pending.pop(next_display_id)
                next_display_id += 1

                # FPS overlay
                now = time.perf_counter()
                frame_times.append(now)
                frame_times = [t for t in frame_times if now - t <= 1.0]
                display_fps = len(frame_times)

                cv2.putText(
                    ann,
                    f"FPS: {display_fps}  Threads: {num_threads}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("YOLOv8s-pose  (Q to quit)", ann)

                if writer:
                    writer.write(ann)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):  # Q or ESC
                break

    finally:
        stop_event.set()
        # send poison pills
        for _ in threads:
            try:
                input_q.put_nowait(None)
            except queue.Full:
                pass
        for t in threads:
            t.join(timeout=2.0)

        cv2.destroyAllWindows()
        del cam
        del writer  # flushes & releases VideoWriter (RAII)

    print(f"\nFinal display FPS: {display_fps}")


# offline pipeline (video file) for benchmarking
def run_file(input_path: str, num_threads: int, save_path: str | None):
    """
    Process every frame of a video file with `num_threads` workers.

    Same pipeline as the realtime path (input buffer, workers, output buffer,
    reorder), but nothing is dropped: a producer thread feeds frames with a
    blocking put, so the result is deterministic regardless of thread count.
    Prints the pure inference time as `Time elapsed: <sec> seconds` for the
    benchmark script to parse.
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file: {input_path}")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print(f"Input: {input_path}  {width}x{height} @ {fps:.1f} fps  |  Workers: {num_threads}")

    writer = VideoWriter(save_path, fps, width, height) if save_path else None

    input_q: queue.Queue  = queue.Queue(maxsize=num_threads * 4)
    output_q: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    ready_barrier = threading.Barrier(num_threads + 1)  # workers + main

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(
            target=worker,
            args=(input_q, output_q, stop_event, ready_barrier),
            daemon=True,
        )
        t.start()
        threads.append(t)

    # Wait until every worker has loaded its model, then start the clock.
    ready_barrier.wait()
    t_start = time.perf_counter()

    # Producer: read the whole file and feed the workers (blocking, no drops).
    produced = {"count": 0}
    done_reading = threading.Event()

    def producer():
        idx = 0
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break
            input_q.put((idx, frame))
            idx += 1
        produced["count"] = idx
        done_reading.set()

    prod_thread = threading.Thread(target=producer, daemon=True)
    prod_thread.start()

    # Consumer: reorder by seq_id and write in original order.
    pending: dict = {}
    next_id = 0
    written = 0
    while True:
        if done_reading.is_set() and written >= produced["count"]:
            break
        try:
            sid, ann = output_q.get(timeout=0.1)
        except queue.Empty:
            continue
        pending[sid] = ann
        while next_id in pending:
            ann = pending.pop(next_id)
            if writer:
                writer.write(ann)
            next_id += 1
            written += 1

    elapsed = time.perf_counter() - t_start

    # Teardown
    stop_event.set()
    prod_thread.join(timeout=2.0)
    for t in threads:
        t.join(timeout=2.0)
    cap.release()
    del writer  # flush & release (RAII)

    eff_fps = written / elapsed if elapsed > 0 else 0.0
    print(f"Frames processed: {written}")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print(f"Throughput: {eff_fps:.2f} fps")


# CLI
def parse_args():
    p = argparse.ArgumentParser(
        description="Real-time YOLOv8s-pose from webcam (multi-threaded)"
    )
    p.add_argument("--camera",  type=int, default=0,
                   help="Camera device index (default: 0)")
    p.add_argument("--input",   default=None,
                   help="Process a video file instead of the camera (offline mode)")
    p.add_argument("--threads", type=int, default=4,
                   help="Number of inference worker threads (default: 4)")
    p.add_argument("--save",    default=None,
                   help="Optional path to save the annotated video (e.g. out.mp4)")
    return p.parse_args()


def main():
    args = parse_args()
    if args.input:
        run_file(
            input_path=args.input,
            num_threads=args.threads,
            save_path=args.save,
        )
    else:
        run_realtime(
            camera_index=args.camera,
            num_threads=args.threads,
            save_path=args.save,
        )


if __name__ == "__main__":
    main()