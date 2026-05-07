import argparse
import subprocess

import time


parser = argparse.ArgumentParser(
                    prog='main.py',
                    description='test your bubble sorting skills',
                    epilog='let the best ai-bot win')

parser.add_argument('exe', help='your ./bubble executable')

def update_table():
    pass

def main():
    args = parser.parse_args()
    # print(args.exe, args.count, args.verbose)
    time_start = time.time()

    result = subprocess.run([f'./{args.exe}', '1 2 3 4'], capture_output=True)

    time_end = time.time()

    print(time_end-time_start, result)

    print(result.stdout.split())

if __name__ == "__main__":
    main()