"""
python main.py --camera /dev/video0 --resolution 1280x720 --fps 30 --mode thread
python main.py --camera /dev/video0 --resolution 640x480  --fps 15 --mode process
"""

import argparse
import logging
import os
import queue
import signal
import sys
import threading
import time
import multiprocessing as mp

import cv2
import numpy as np

os.makedirs("log", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("log", "app.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")


class Sensor:
    def get(self):
        raise NotImplementedError("Subclasses must implement method get()")


class SensorX(Sensor):
    def __init__(self, delay: float):
        self._delay = delay
        self._data = 0

    def get(self) -> int:
        time.sleep(self._delay)
        self._data += 1
        return self._data


class SensorCam(Sensor):
    """camera sensor wrapper (OpenCV)"""

    def __init__(self, camera_name: str, resolution: str):
        self._log = logging.getLogger("SensorCam")
        self._cam = None

        # resolution string e.g. "1280x720"
        try:
            width_str, height_str = resolution.lower().split("x")
            self._width = int(width_str)
            self._height = int(height_str)
        except ValueError:
            self._log.error("Invalid resolution format '%s'. Expected WxH.", resolution)
            sys.exit(1)

        index = self._parse_camera_name(camera_name)
        self._log.info("Opening camera '%s' (index %s) at %dx%d …",
                       camera_name, index, self._width, self._height)

        self._cam = cv2.VideoCapture(index)
        if not self._cam.isOpened():
            self._log.error("Camera '%s' not found in the system.", camera_name)
            sys.exit(1)

        self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._log.info("Camera opened successfully.")

    def _parse_camera_name(self, name: str):
        """accept /dev/video0, or a bare integer string."""
        if name.startswith("/dev/video"):
            try:
                return int(name.replace("/dev/video", ""))
            except ValueError:
                pass
        try:
            return int(name)
        except ValueError:
            return name  # let OpenCV try as a path

    def get(self):
        """return the latest frame, or none on failure."""
        if self._cam is None or not self._cam.isOpened():
            self._log.error("Camera is not available (disconnected?).")
            return None
        ret, frame = self._cam.read()
        if not ret:
            self._log.warning("Failed to read frame from camera.")
            return None
        return frame

    def __del__(self):
        if self._cam is not None and self._cam.isOpened():
            self._cam.release()
            logging.getLogger("SensorCam").info("Camera released.")


class WindowImage:
    """displays the composed image in an OpenCV window"""

    WINDOW_NAME = "Sensor View"

    def __init__(self, fps: float):
        self._log = logging.getLogger("WindowImage")
        if fps <= 0:
            self._log.error("FPS must be positive, got %s.", fps)
            sys.exit(1)
        self._fps = fps
        self._delay_ms = max(1, int(1000 / fps))
        try:
            cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
            self._log.info("Window '%s' created (%.1f fps, %d ms delay).",
                           self.WINDOW_NAME, fps, self._delay_ms)
        except Exception as exc:
            self._log.error("Failed to create window: %s", exc)
            sys.exit(1)

    def show(self, img: np.ndarray) -> bool:
        """
        display img.  Returns false if the user pressed 'q' or closed
        the window, true otherwise.
        """
        try:
            cv2.imshow(self.WINDOW_NAME, img)
        except Exception as exc:
            self._log.error("Failed to display image: %s", exc)
            return False
        key = cv2.waitKey(self._delay_ms) & 0xFF
        return key != ord("q")

    def __del__(self):
        try:
            cv2.destroyWindow(self.WINDOW_NAME)
            logging.getLogger("WindowImage").info("Window destroyed.")
        except Exception:
            pass


def sensor_x_worker(sensor: SensorX, out_queue, stop_event):
    """
    continuously reads from a SensorX and puts the latest value into
    out_queue. Keeps only the most recent reading (drain old values first).
    """
    while not stop_event.is_set():
        value = sensor.get()
        # drain stale values so the main thread always gets the freshest one
        while not out_queue.empty():
            try:
                out_queue.get_nowait()
            except Exception:
                break
        out_queue.put(value)


def sensor_cam_worker(sensor: SensorCam, out_queue, stop_event):
    """
    continuously reads frames from SensorCam and puts them into out_queue.
    """
    while not stop_event.is_set():
        frame = sensor.get()
        if frame is not None:
            while not out_queue.empty():
                try:
                    out_queue.get_nowait()
                except Exception:
                    break
            out_queue.put(frame)
        else:
            time.sleep(0.01)   # short back-off on read failure


def _sensor_x_process_target(delay: float, out_queue: mp.Queue,
                              stop_event: mp.Event):
    """process target for SensorX (cannot pickle the object, recreate it)"""
    sensor = SensorX(delay)
    while not stop_event.is_set():
        value = sensor.get()
        while not out_queue.empty():
            try:
                out_queue.get_nowait()
            except Exception:
                break
        out_queue.put(value)


def _sensor_cam_process_target(camera_name: str, resolution: str,
                                out_queue: mp.Queue, stop_event: mp.Event):
    """process target for SensorCam"""
    sensor = SensorCam(camera_name, resolution)
    while not stop_event.is_set():
        frame = sensor.get()
        if frame is not None:
            while not out_queue.empty():
                try:
                    out_queue.get_nowait()
                except Exception:
                    break
            out_queue.put(frame)
        else:
            time.sleep(0.01)


def compose_frame(frame: np.ndarray, sensor_values: dict) -> np.ndarray:
    """
    overlay sensor readings on the camera frame
    a semi-transparent black box is drawn in the bottom-right corner
    """
    img = frame.copy()
    h, w = img.shape[:2]

    # overlay box
    box_w, box_h = 200, 20 + 25 * len(sensor_values)
    x1, y1 = w - box_w - 10, h - box_h - 10
    x2, y2 = w - 10, h - 10

    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

    # text
    for i, (name, val) in enumerate(sensor_values.items()):
        text = f"{name}: {val}"
        cv2.putText(img, text,
                    (x1 + 8, y1 + 20 + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 1, cv2.LINE_AA)
    return img


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sensor data acquisition and display (threads vs processes)."
    )
    parser.add_argument(
        "--camera", default="0",
        help="Camera name in the system, e.g. /dev/video0 or 0  (default: 0)"
    )
    parser.add_argument(
        "--resolution", default="640x480",
        help="Desired camera resolution, e.g. 1280x720  (default: 640x480)"
    )
    parser.add_argument(
        "--fps", type=float, default=30.0,
        help="Display frame rate in Hz  (default: 30)"
    )
    parser.add_argument(
        "--mode", choices=["thread", "process"], default="thread",
        help="Concurrency mode: 'thread' (default) or 'process'"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("Starting — camera=%s  resolution=%s  fps=%.1f  mode=%s",
                args.camera, args.resolution, args.fps, args.mode)

    # SensorX delays: 100, 10 or 1 Hz
    sensor_delays = [0.01, 0.1, 1.0]
    sensor_names  = ["Sensor0", "Sensor1", "Sensor2"]

    use_processes = (args.mode == "process")

    if use_processes:
        QueueCls = mp.Queue
        EventCls = mp.Event
    else:
        QueueCls = queue.Queue
        EventCls = threading.Event

    stop_event   = EventCls()
    cam_queue    = QueueCls(maxsize=2)
    sensor_queues = [QueueCls(maxsize=2) for _ in sensor_delays]

    workers = []  # list of Thread or Process objects

    if use_processes:
        # camera process
        p = mp.Process(
            target=_sensor_cam_process_target,
            args=(args.camera, args.resolution, cam_queue, stop_event),
            daemon=True,
        )
        p.start()
        workers.append(p)

        # SensorX processes
        for delay, sq in zip(sensor_delays, sensor_queues):
            p = mp.Process(
                target=_sensor_x_process_target,
                args=(delay, sq, stop_event),
                daemon=True,
            )
            p.start()
            workers.append(p)

    else:  # threads
        cam_sensor = SensorCam(args.camera, args.resolution)

        t = threading.Thread(
            target=sensor_cam_worker,
            args=(cam_sensor, cam_queue, stop_event),
            daemon=True,
        )
        t.start()
        workers.append(t)

        for delay, sq in zip(sensor_delays, sensor_queues):
            sensor = SensorX(delay)
            t = threading.Thread(
                target=sensor_x_worker,
                args=(sensor, sq, stop_event),
                daemon=True,
            )
            t.start()
            workers.append(t)

    window = WindowImage(args.fps)

    # last known values (used when no new data arrived yet)
    last_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    last_sensor_vals = {name: 0 for name in sensor_names}

    # graceful ctrl c shutdown
    def _sigint_handler(sig, frame):
        logger.info("SIGINT received — shutting down …")
        stop_event.set()

    signal.signal(signal.SIGINT, _sigint_handler)

    running = True
    while running and not stop_event.is_set():
        t0 = time.perf_counter()

        # camera frame
        try:
            last_frame = cam_queue.get_nowait()
        except Exception:
            pass  # keep previous frame

        # sensor values
        for name, sq in zip(sensor_names, sensor_queues):
            try:
                last_sensor_vals[name] = sq.get_nowait()
            except Exception:
                pass  # keep previous value

        # compose and display
        img = compose_frame(last_frame, last_sensor_vals)
        running = window.show(img)

        # timing info
        elapsed = time.perf_counter() - t0
        logger.debug("Frame loop %.1f ms", elapsed * 1000)

    logger.info("Stopping all workers …")
    stop_event.set()

    for w in workers:
        w.join(timeout=2.0)

    del window  # destroys the OpenCV window
    logger.info("Clean exit.")


if __name__ == "__main__":
    main()