import time
import subprocess
import serial
from serial.tools import list_ports

BAUD = 115200
TRIGGER_LINE = "YOLO_TRIGGER"
STOP_LINE = "YOLO_STOP" 

# Prevent spawning multiple YOLO runs at once
proc = None
file = None


# this is subject to change, this is based off mac needs
# when running on pi you will have to update accordingly
def find_pico_port() -> str | None:
    ports = [p.device for p in list_ports.comports()]
    # Prefer usbmodem (common for Pico)
    for dev in ports:
        if dev.startswith("/dev/cu.usbmodem"):
            return dev
    for dev in ports:
        if dev.startswith("/dev/cu.usb"):
            return dev
    return None

def start_yolo():
    global proc, file
    if proc is not None and proc.poll() is None:
        print("YOLO already running -> ignoring trigger")
        return
    print("Launching YOLO...")

    #dont have many files so if exists then close it
    if file is not None:
        file.close()
        file = None
    #over write the file in binary 
    file = open("yolo.log", "wb")
    #stdout will be log (file) which says everything goes to the file not TERMINAL
    proc = subprocess.Popen(["python3", "run_yolo.py"], stdout=file, stderr=subprocess.STDOUT, start_new_session=True)

def stop_yolo():
    global proc, file
    # nothing to stop if process isn't running
    if proc is None or proc.poll() is not None:
        print("YOLO not running -> ignoring stop")
        return
 
    print("Stopping YOLO...")
    proc.terminate()            # sends SIGTERM, lets run_yolo.py clean up gracefully
 
    # give it 3 seconds to exit cleanly before forcing it
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()             # SIGKILL if it didn't respond to SIGTERM
        proc.wait()
 
    # close the log file now that the process is done
    if file is not None:
        file.close()
        file = None
 
    proc = None
    print("YOLO stopped.")


def main():
    port = find_pico_port()
    if not port:
        raise RuntimeError("Could not find Pico serial port. Unplug/replug and retry.")

    print(f"Listening on {port} @ {BAUD}")
    with serial.Serial(port, BAUD, timeout=1) as ser:
        # Give MicroPython a moment; some setups print boot text
        time.sleep(0.5)

        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            # Uncomment if you want to see everything coming from Pico:
            # print("RX:", line)

            if line == TRIGGER_LINE:
                print("RX: YOLO_TRIGGER")
                start_yolo()
            elif line == STOP_LINE:
                print("RX: YOLO_STOP")
                stop_yolo()


if __name__ == "__main__":
    main()