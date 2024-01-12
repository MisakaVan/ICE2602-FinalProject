import queue
import threading
import time
import FileSet
import numpy as np


class Printer:
    """
    a thread-safe printer
    """

    def __init__(self):
        self.lock = threading.Lock()

    def log(self, *args, **kwargs):
        with self.lock:
            print(*args, **kwargs)


class CrawlerLike:
    """
    Simulates the behavior of Crawler.

    each sub-thread gets a string from the queue, and prints it. then adds 2 random strings to the queue. delays randomly.

    stops when total count hits threshold.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.queue = queue.Queue(maxsize=1000)
        self.printer = Printer()
        self.counter = 0
        self.workers = []

    def worker(self, ):
        worker_name = threading.current_thread().name
        self.printer.log(f"{worker_name} started.")
        while not self.stop_event.is_set():
            try:
                s = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            with self.lock:
                self.counter += 1
                num = self.counter

            self.printer.log(f"{worker_name} : {num:5d} : {s}")

            self.queue.put(FileSet.random_string(10))
            self.queue.put(FileSet.random_string(10))
            time.sleep(0.6 + np.random.uniform(-0.05, 0.05))
        else:
            self.printer.log(f"{worker_name} stopped.")

    def run(self, secs=5):
        start_time = time.time()
        for i in range(4):
            t = threading.Thread(target=self.worker, name=f"worker-{i}")
            t.start()
            self.workers.append(t)

        while True:
            cur_time = time.time()
            self.printer.log(f"MainThread : Tick: {cur_time - start_time:.5f} seconds passed.")
            if cur_time - start_time > secs:
                break
            time.sleep(1)

        self.printer.log(f"MainThread : set the Stopping flag...")
        self.stop_event.set()
        for t in self.workers:
            t.join()


if __name__ == '__main__':
    crawler = CrawlerLike()
    for _ in range(5):
        crawler.queue.put(FileSet.random_string(10))
    crawler.run(2)
