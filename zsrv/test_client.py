import zmq
import json

def test_zmq_server():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:8819")

    message = {"test": "data"}
    socket.send_string(json.dumps(message))

    response = socket.recv_string()
    print(f"Response: {response}")

if __name__ == "__main__":
    test_zmq_server()