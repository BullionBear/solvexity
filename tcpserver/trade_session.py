import socketserver
import argparse
from binance.client import Client  # Replace with the actual module for Client

# Initialize your Client instance
c = Client(
    '',
    ''
)

# Function to handle commands using argparse
def handle_command(command):
    # Set up the argument parser
    parser = argparse.ArgumentParser(prog="CommandParser", add_help=False)
    subparsers = parser.add_subparsers(dest="action")

    # Add 'account' command
    account_parser = subparsers.add_parser("account")
    account_parser.add_argument(
        "type", nargs="?", default="SPOT", help="Account type (default: SPOT)"
    )

    # Add 'help' command
    subparsers.add_parser("help")

    # Parse the command
    try:
        args = parser.parse_args(command.split())
        if args.action == "account":
            # Handle 'account' command
            return str(c.get_account_snapshot(type=args.type.upper()))
        elif args.action == "help":
            # Provide a help message
            return (
                "Available commands:\n"
                "  account [type] - Get account snapshot. Default type is SPOT.\n"
                "  help           - Show this help message.\n"
                "  exit           - Close the session."
            )
        else:
            return "Unknown command. Type 'help' for a list of available commands."
    except SystemExit:
        # Catch argparse's built-in exit when invalid arguments are provided
        return "Invalid command. Type 'help' for a list of available commands."

class MyTCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # Welcome message
        self.wfile.write(b"Welcome to the server. Type 'help' for commands. Type 'exit' to quit.\n")
        while True:
            # Prompt for input
            self.wfile.write(b"> ")
            self.wfile.flush()

            # Read client input
            data = self.rfile.readline().strip().decode()
            if not data:
                break

            print(f"Received command: {data}")
            if data.lower() in ["exit", "quit"]:
                self.wfile.write(b"Goodbye!\n")
                break

            # Process the command
            response = handle_command(data)
            self.wfile.write(f"{response}\n".encode())

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9000
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        print(f"Server started on {HOST}:{PORT}")
        server.serve_forever()
