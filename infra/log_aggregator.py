import argparse
import redis
import os
import gzip
import json
import datetime
import threading

class LogAggregator:
    def __init__(self, redis_host, redis_port, channel, log_dir):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.channel = channel
        self.log_dir = log_dir
        self.running = True

        # Ensure the log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

        # Redis connection
        self.redis_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()

        # Subscribe to the channel
        self.pubsub.subscribe(self.channel)

        # Current date for tracking log file rotation
        self.current_date = datetime.date.today()

    def start(self):
        print(f"Starting log aggregator for channel: {self.channel}")
        threading.Thread(target=self._compress_logs_daily, daemon=True).start()
        self._process_logs()

    def _process_logs(self):
        for message in self.pubsub.listen():
            if not self.running:
                break

            if message["type"] == "message":
                log_data = message["data"]
                self._write_log(log_data)

    def _write_log(self, log_data):
        """
        Write the log data (JSON format) to a file.
        """
        try:
            # Parse the JSON log data
            log_record = json.loads(log_data)

            logger_name = log_record.get("name", "unknown_logger")
            process_id = log_record.get("process_id", "unknown_process")
            log_date = datetime.date.today().strftime("%Y_%m_%d")
            log_filename = f"{logger_name}_{log_date}_{process_id}.log"
            log_filepath = os.path.join(self.log_dir, log_filename)

            # Write the log message to the file
            with open(log_filepath, 'a') as log_file:
                log_file.write(json.dumps(log_record) + "\n")

        except Exception as e:
            print(f"Error writing log: {e}")

    def _compress_logs_daily(self):
        """
        Compress all log files of the day at the end of the day.
        """
        while self.running:
            now = datetime.datetime.now()
            midnight = datetime.datetime.combine(now.date(), datetime.time.min) + datetime.timedelta(days=1)
            seconds_until_midnight = (midnight - now).total_seconds()

            threading.Event().wait(seconds_until_midnight)  # Wait until the end of the day

            self._compress_logs_for_date(self.current_date)
            self.current_date = datetime.date.today()

    def _compress_logs_for_date(self, log_date):
        """
        Compress all log files for the given date into a .gz file.
        """
        date_str = log_date.strftime("%Y_%m_%d")
        compressed_filename = os.path.join(self.log_dir, f"{date_str}.gz")

        with gzip.open(compressed_filename, 'wb') as compressed_file:
            for log_file in os.listdir(self.log_dir):
                if log_file.endswith(".log") and date_str in log_file:
                    log_file_path = os.path.join(self.log_dir, log_file)
                    with open(log_file_path, 'rb') as f:
                        compressed_file.write(f.read())
                    os.remove(log_file_path)  # Delete the original log file

    def stop(self):
        """
        Gracefully stop the log aggregator.
        """
        self.running = False
        self.pubsub.close()

def parse_arguments():
    """
    Parses command-line arguments for the log aggregator.
    """
    parser = argparse.ArgumentParser(description="Redis Log Aggregator")
    parser.add_argument('--log-dir', type=str, default='/var/log', help="Directory to store logs")
    parser.add_argument('--redis-host', type=str, default='localhost', help="Redis host")
    parser.add_argument('--redis-port', type=int, default=6379, help="Redis port")
    parser.add_argument('--channel', type=str, default='log_channel', help="Redis PubSub channel")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    aggregator = LogAggregator(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        channel=args.channel,
        log_dir=args.log_dir
    )
    try:
        aggregator.start()
    except KeyboardInterrupt:
        aggregator.stop()
