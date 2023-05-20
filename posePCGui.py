"""
PosePCGui.py wraps the basics of the basics of PosePC in a TK GUI.
The gui selects a video file or webcam, and loops the video.
the gui also has a button to start the posePC loop.
it quits when the video ends or the user presses q.
video frames area also sent by ZMQ, allowing TouchDesigner to receive them.
"""
import sys
import cv2
from tkinter import Tk, filedialog, Menu
import os
import threading
import zmq

from pythonosc import udp_client
from .pose_detector import PoseDetectorMediapipe


cap = None
loop_video = False
cv2_window = None
root = None

zmq_context = zmq.Context()
zmq_socket = zmq_context.socket(zmq.PUB)
zmq_socket.bind("tcp://127.0.0.1:5555")

OSC_URL = "127.0.0.1"
OSC_PORT = 5005
client = udp_client.SimpleUDPClient(OSC_URL, OSC_PORT)

def set_webcam():
    global cap
    cap = cv2.VideoCapture(0)

def set_file_dialog():
    global cap
    file_path = filedialog.askopenfilename(
        initialdir=os.getcwd(),
        filetypes=[("Video Files", "*.mp4;*.avi;*.mov")]
    )
    if file_path:
        cap = cv2.VideoCapture(file_path)

def toggle_loop():
    global loop_video
    loop_video = not loop_video

def start_reading():
    global cap
    if cap is None:
        print("no file selected, using webcam")
        set_webcam()  # Open the webcam if cap is None

    def display_frames():
        global cv2_window
        cv2_window = cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)

        while True:
            ret, frame = cap.read()
            if not ret:
                if loop_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            cv2.imshow("Video Stream", frame)


            # Send the frame as a video stream via ZMQ socket
            # Convert the frame to a format suitable for streaming
            frame_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
            zmq_socket.send(frame_bytes)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        on_closing()

    # Start the display_frames function in a separate thread
    threading.Thread(target=display_frames).start()

def on_closing():
    global cap, cv2_window, root
    if zmq_context is not None:
        zmq_socket.close()
        zmq_context.term()
    if cap is not None:
        cap.release()
    if cv2_window is not None:
        cv2.destroyAllWindows()
    if root is not None:
        root.quit()

# Create the main window
root = Tk()

# Create the menu
menu = Menu(root)
root.config(menu=menu)

file_menu = Menu(menu, tearoff=False)
file_menu.add_command(label="Set Webcam", command=set_webcam)
file_menu.add_command(label="Set Video File", command=set_file_dialog)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_closing)  # Call on_closing function when selecting "Exit"
menu.add_cascade(label="File", menu=file_menu)

options_menu = Menu(menu, tearoff=False)
options_menu.add_checkbutton(label="Loop Video", command=toggle_loop)
menu.add_cascade(label="Options", menu=options_menu)

menu.add_command(label="Start Reading", command=start_reading)

root.config(menu=menu)

def check_key(event):
    if event.char == 'q':
        on_closing()

root.bind('<Key>', check_key)  # Bind the check_key function to handle all key events

root.mainloop()
sys.exit()
