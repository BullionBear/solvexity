from flask import Flask
import atexit

app = Flask(__name__)

with app.app_context():
    # Code to run during app context
    print("Application context is created.")
    

@atexit.register
def shutdown_session():
    # Code to run during app teardown
    print("Application context is shutting down.")

@app.route('/')
def hello_world():
    return 'Hello, World!'