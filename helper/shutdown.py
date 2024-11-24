import signal
import threading

from . import logging

logger = logging.getLogger()

class Shutdown:
    def __init__(self, *signals):
        """
        Initialize the Shutdown instance and register signal handlers.

        :param signals: Signals to listen for (e.g., signal.SIGINT, signal.SIGTERM)
        """
        self.callbacks = []
        self.lock = threading.Lock()  # To ensure thread-safe callback execution
        self.shutdown_event = threading.Event()  # Event to manage shutdown state

        # Register the dispatcher for each signal
        for sig in signals:
            signal.signal(sig, self._signal_dispatcher)

    def _signal_dispatcher(self, signum, frame):
        """
        Dispatcher function that is called when a signal is received.
        Executes all registered callbacks in a thread-safe manner.

        :param signum: The signal number received.
        :param frame: The current stack frame (unused here).
        """
        logger.info(f"Signal received: {signum}. Executing shutdown callbacks.")
        with self.lock:
            for callback in self.callbacks:
                try:
                    callback(signum)
                except Exception as e:
                    import traceback
                    full_traceback = traceback.format_exc()
                    logger.error(f"Error invoking strategy: {e}\n{full_traceback}")
        self.shutdown_event.set()  # Signal that shutdown is complete

    def register(self, callback):
        """
        Register a callback to be executed on shutdown.

        :param callback: A callable that accepts a signal number as an argument.
        """
        with self.lock:
            self.callbacks.append(callback)

    def wait_for_shutdown(self):
        """
        Block the main thread until a shutdown signal is received and callbacks complete.
        """
        self.shutdown_event.wait()

    def is_set(self):
        """
        Check if the shutdown process has been triggered.

        :return: True if shutdown has been triggered, False otherwise.
        """
        return self.shutdown_event.is_set()

