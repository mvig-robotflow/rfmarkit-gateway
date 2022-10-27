import logging
import multiprocessing as mp

logging.basicConfig(level=logging.INFO)


def imu_render_ui_task(stop_ev: mp.Event, finish_ev: mp.Event, in_queue: mp.Queue):
    x = None
    try:
        while True:
            if stop_ev.is_set():
                break
            try:
                x = None
                x = in_queue.get(timeout=1)
            except Exception as e:
                pass
            if x is not None:
                print(x)
    except KeyboardInterrupt:
        logging.debug(f"imu_render_ui exitting")
        finish_ev.set()

    finish_ev.set()
