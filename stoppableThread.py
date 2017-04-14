import threading


class StoppableThread(threading.Thread):
    """
    Thread class that is used by the client to allow both threads, listening and writing, to be stopped by
     the main thread when the server is shutting down 
    """

    def __init__(self, target_function, sock):
        super(StoppableThread, self).__init__(target=target_function, args=(sock,))
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()