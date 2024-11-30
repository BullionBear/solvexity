import redis
import json
import os
import gzip
import shutil
import argparse
from datetime import datetime

class LogAggregator:
    """
    Log aggregator to consume logs from a Redis PubSub channel and manage log files with batch writing.
    """
    def __init__(self, redis_host='localhost', redis_port=6379, channel='log_channel', log_dir='/var/log', batch_size=100):
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
        self.channel = channel
        self.log_dir = log_dir
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.batch_size = batch_size
        self.log_batches = {}  # Dictionary to store logs by file

    def start(self):
        """
        Starts listening to the Redis PubSub channel for logs.
        """
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channel)

        print(f"Listening for logs on Redis channel: {self.channel}")
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    log_data = message['data']
                    self.process_log(log_data)
                self.check_date_rollover()
        except KeyboardInterrupt:
            print("\nLog aggregator stopped.")
        finally:
            pubsub.close()
            self.flush_all_batches()  # Ensure all remaining logs are written

    def process_log(self, log_data):
        """
        Processes and batches the log data.
        """
        try:
            log_record = json.loads(log_data)
            log_time = log_record.get('time', datetime.now().isoformat())
            
            # Preprocess the timestamp to replace ',' with '.' for compatibility
            log_time = log_time.replace(',', '.')
            log_date = datetime.fromisoformat(log_time).strftime('%Y%m%d')
            
            logger_name = log_record.get('name', 'unknown')
            process_id = log_record.get('process_id', 'unknown')

            log_file_name = f"{logger_name}_{log_date}_{process_id}.log"
            log_file_path = os.path.join(self.log_dir, log_file_name)

            # Add the log record to the batch
            if log_file_path not in self.log_batches:
                self.log_batches[log_file_path] = []

            self.log_batches[log_file_path].append(json.dumps(log_record))

            # Flush the batch to file if it exceeds the batch size
            if len(self.log_batches[log_file_path]) >= self.batch_size:
                self.flush_batch(log_file_path)
        except json.JSONDecodeError:
            print(f"Invalid log data received: {log_data}")
        except ValueError as e:
            print(f"Error processing log timestamp: {e}. Log data: {log_data}")

    def flush_batch(self, file_path):
        """
        Flushes a batch of logs to the specified file.
        """
        try:
            logs = self.log_batches.get(file_path, [])
            if logs:
                os.makedirs(self.log_dir, exist_ok=True)  # Ensure the log directory exists
                with open(file_path, 'a') as log_file:
                    log_file.write("\n".join(logs) + "\n")
                self.log_batches[file_path] = []  # Clear the batch after writing
        except Exception as e:
            print(f"Failed to write logs to {file_path}: {e}")

    def flush_all_batches(self):
        """
        Flushes all remaining log batches to their respective files.
        """
        for file_path in list(self.log_batches.keys()):
            self.flush_batch(file_path)

    def check_date_rollover(self):
        """
        Checks if the date has changed and handles log rotation.
        """
        new_date = datetime.now().strftime('%Y%m%d')
        if new_date != self.current_date:
            print(f"Date rollover detected: {self.current_date} -> {new_date}")
            self.flush_all_batches()
            self.compress_logs(self.current_date)
            self.current_date = new_date

    def compress_logs(self, date):
        """
        Compresses all log files for the specified date into a single .gz archive.
        """
        archive_name = os.path.join(self.log_dir, f"{date}.gz")
        with gzip.open(archive_name, 'wb') as archive:
            for file_name in os.listdir(self.log_dir):
                if file_name.endswith(f"_{date}.log"):
                    file_path = os.path.join(self.log_dir, file_name)
                    print(f"Adding {file_path} to {archive_name}")
                    with open(file_path, 'rb') as log_file:
                        shutil.copyfileobj(log_file, archive)
                    os.remove(file_path)  # Remove the original log file
        print(f"Compressed logs into {archive_name}")

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
    aggregator.start()