from pythonosc import osc_server
from pythonosc.dispatcher import Dispatcher

UDP_URL = "127.0.0.1"
UDP_PORT = 5005

# Define a callback function to handle incoming messages
def message_handler(address, *args):
    converted_args = [str(arg) for arg in args]
    print(f"Received message from {address}: {', '.join(converted_args)}")

# Create dispatcher and register the callback function
dispatcher = Dispatcher()
dispatcher.set_default_handler(message_handler)

# Create UDP server
server = osc_server.ThreadingOSCUDPServer((UDP_URL, UDP_PORT), dispatcher)

# Start the server to listen for incoming messages
print(f"Server listening on {UDP_URL}:{UDP_PORT}...")
server.serve_forever()

