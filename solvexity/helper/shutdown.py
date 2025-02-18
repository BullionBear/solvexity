import signal
import threading
import logging

logger = logging.get_logger()

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
        logger.info(f"Signal received: {signum}. Number of callbacks: {len(self.callbacks)} is executing.")
        # Print out all alive threads
        current_threads = threading.enumerate()
        logger.info("Currently alive threads:")
        for th in current_threads:
            logger.info(f"Thread Name: {th.name}, Is Alive: {th.is_alive()}")
        with self.lock:
            for callback in reversed(self.callbacks):  # Execute in LIFO order
                try:
                    callback(signum)
                except Exception as e:
                    logger.error(f"Error invoking shutdown callback: {e}", exc_info=True)
            self.callbacks.clear()
        logger.info("All callbacks executed.")
        self.shutdown_event.set()  # Signal that shutdown is complete

    def register(self, callback):
        """
        Register a callback to be executed on shutdown.

        :param callback: A callable that accepts a signal number as an argument.
        """
        with self.lock:
            self.callbacks.append(callback)
        logger.info("Callback registered.")

    def wait_for_shutdown(self):
        """
        Block the main thread until a shutdown signal is received and callbacks complete.
        """
        logger.info("Waiting for shutdown signal...")
        self.shutdown_event.wait()
        logger.info("Shutdown signal received, proceeding with shutdown.")

    def is_set(self):
        """
        Check if the shutdown process has been triggered.

        :return: True if shutdown has been triggered, False otherwise.
        """
        return self.shutdown_event.is_set()
    
    def set(self):
        """
        Trigger the shutdown process.
        """
        self.shutdown_event.set()
        logger.info("Shutdown event set.")
        self._trigger_callbacks()

    def _trigger_callbacks(self):
        """
        Trigger registered callbacks manually, useful for programmatic shutdowns.
        """
        logger.info("Triggering shutdown callbacks explicitly.")
        with self.lock:
            for callback in reversed(self.callbacks):
                try:
                    callback(None)
                except Exception as e:
                    logger.error(f"Error invoking manual shutdown callback: {e}", exc_info=True)
            self.callbacks.clear()
