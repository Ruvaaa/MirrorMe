import time
import threading

remaining_time = 0
is_running = False

def start_timer(seconds):
    global remaining_time, is_running
    remaining_time = seconds
    is_running = True

    def countdown():
        global remaining_time, is_running
        while remaining_time > 0 and is_running:
            time.sleep(1)
            remaining_time -= 1
        is_running = False

    thread = threading.Thread(target=countdown)
    thread.start()

def get_remaining_time():
    return remaining_time

def stop_timer():
    global is_running
    is_running = False
