import time
import subprocess
import serial

BAUD = 115200
SERIAL_PORT = "/dev/ttyAMA0"
TRIGGER_LINE = "YOLO_TRIGGER"
STOP_LINE = "YOLO_STOP"

# Prevent spawning multiple YOLO runs at once
proc = None
file = None


def start_yolo():
    global proc, file
    if proc is not None and proc.poll() is None:
        print("YOLO already running -> ignoring trigger")
        return
    print("Launching YOLO...")

    if file is not None:
        file.close()
        file = None

    file = open("yolo.log", "wb")
    proc = subprocess.Popen(
        ["python3", "run_yolo.py"],
        stdout=file,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )


def stop_yolo():
    global proc, file
    if proc is None or proc.poll() is not None:
        print("YOLO not running -> ignoring stop")
        return

    print("Stopping YOLO...")
    proc.terminate()

    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    if file is not None:
        file.close()
        file = None

    proc = None
    print("YOLO stopped.")


def main():
    print(f"Listening on {SERIAL_PORT} @ {BAUD}")

    with serial.Serial(SERIAL_PORT, BAUD, timeout=1) as ser:
        time.sleep(0.5)

        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            if line == TRIGGER_LINE:
                print("RX: YOLO_TRIGGER")
                start_yolo()
            elif line == STOP_LINE:
                print("RX: YOLO_STOP")
                stop_yolo()


if __name__ == "__main__":
    main()