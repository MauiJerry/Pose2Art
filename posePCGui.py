import tkinter as tk

import sys
import cv2
from tkinter import Tk, filedialog, Menu
import os
import threading
import zmq
from pythonosc import udp_client

# define global strings for set/compare
g_webcam ="Webcam"
g_file = "File"
g_looping_prefix = "Loop Video:"
g_videoWindowName = "VideoStream"

"""
PoseApp class is a tkinter GUI for selecting video input and output
input can be the webcam or a file
"""
class PoseApp:
    def __init__(self, pose_detector):
        global g_webcam, g_file
        self.pose_detector = pose_detector

        self.root = tk.Tk()
        self.root.title("Video App")
        self.root.geometry("300x300")
        #self.root.bind('<Key>', self.check_key)  # Bind the check_key function to handle all key events

        self.video_input_source = tk.StringVar(value=g_webcam)
        self.video_looping = tk.BooleanVar(value=False)
        self.video_isWebcam = True

        self.video_input_file = tk.StringVar()
        self.video_output_ip = tk.StringVar(value="127.0.0.1")
        self.video_output_port = tk.StringVar(value="5555")
        self.osc_output_ip = tk.StringVar(value="127.0.0.1")
        self.osc_output_port = tk.StringVar(value="5005")

        # a few local var to hold cv2 stuff
        self.cap = None
        self.cv2_window = None
        self.zmq_socket = None
        self_osc_client = None

        self.running = False

    def run(self):
        self.build_gui()
        self.root.mainloop()

    def check_key(self,event):
        if event.char == 'q':
            self.on_closing()
        return

    def set_video_input_file(self):
        file_path = filedialog.askopenfilename(
            initialdir= '.',
            title = "Select Video File",
            filetypes = [("Video Files", "*.mp4;*.avi;*.mov"), ("All Files", "*.*")]
        )
        self.video_input_file.set(file_path)
        self.video_input_source.set(g_file)

    def build_gui(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)
        file_menu = Menu(menu, tearoff=False)
        file_menu.add_command(label="Exit", command=self.on_closing)  # Call on_closing function when selecting "Exit"
        menu.add_cascade(label="File", menu=file_menu)

        video_input_label = tk.Label(self.root, text="Video Input:")
        video_input_label.pack()

        video_input_radio_frame = tk.Frame(self.root)
        video_input_radio_frame.pack()

        video_input_webcam_radio = tk.Radiobutton(video_input_radio_frame, text=g_webcam,
                                                  variable=self.video_input_source, value=g_webcam)
        video_input_webcam_radio.pack(side="left")

        video_input_file_radio = tk.Radiobutton(video_input_radio_frame, text=g_file,
                                                variable=self.video_input_source, value=g_file)
        video_input_file_radio.pack(side="left")

        video_input_file_entry = tk.Entry(self.root, textvariable=self.video_input_file, state="readonly")
        video_input_file_entry.pack()

        video_input_file_button = tk.Button(self.root, text="Browse",
                                            command=self.set_video_input_file)
        video_input_file_button.pack()

        self.looping_button = tk.Button(self.root,
                text=f"{g_looping_prefix} {'ON' if self.video_looping.get() else 'OFF'}",
                command=self.toggle_looping)
        self.looping_button.pack()

        video_output_label = tk.Label(self.root, text="Video Output URL:")
        video_output_label.pack()

        video_output_ip_entry = tk.Entry(self.root, textvariable=self.video_output_ip)
        video_output_ip_entry.pack()

        video_output_port_entry = tk.Entry(self.root, textvariable=self.video_output_port)
        video_output_port_entry.pack()

        osc_output_label = tk.Label(self.root, text="OSC Output URL:")
        osc_output_label.pack()

        osc_output_ip_entry = tk.Entry(self.root, textvariable=self.osc_output_ip)
        osc_output_ip_entry.pack()

        osc_output_port_entry = tk.Entry(self.root, textvariable=self.osc_output_port)
        osc_output_port_entry.pack()

        self.start_button = tk.Button(self.root, text="Start", command=self.start_video_loop)
        self.start_button.pack()

        self.stop_button = tk.Button(self.root, text="Stop",
                                command=self.stop_video_loop, state=tk.DISABLED)
        self.stop_button.pack()

    def toggle_looping(self):
        self.video_looping.set(not self.video_looping.get())
        self.looping_button["text"] = \
            f"{g_looping_prefix} {'ON' if self.video_looping.get() else 'OFF'}"
        print("Var is now", self.video_looping.get(), "and button text is", self.looping_button["text"])

    def open_zmq(self):
        zmq_url = "tcp://{}:{}".format(self.video_output_ip.get(), self.video_output_port.get())
        print("ZMQ URL: {}".format(zmq_url))
        try:
            self.zmq_context = zmq.Context()
            self.zmq_socket = self.zmq_context.socket(zmq.PUB)
            self.zmq_socket.bind(zmq_url)
            print("ZMQ socket opened")
        except Exception as e:
            print("Error opening ZMQ socket: {}".format(e))
            self.zmq_terminate()

    def zmq_terminate(self):
        if self.zmq_socket is not None:
            self.zmq_socket.close()
            self.zmq_socket = None
        if self.zmq_context is not None:
            self.zmq_context.term()
            self.zmq_context = None

    def open_osc(self):
        osc_ip= self.osc_output_ip.get()
        osc_port = self.osc_output_port.get()
        print("try open OSC URL: ",osc_ip,osc_port)
        try:
            self.osc_client = udp_client.SimpleUDPClient(osc_ip,osc_port)
            print("OSC socket opened")
        except Exception as e:
            print("Error opening OSC socket: {}".format(e))
            self.osc_terminate()

    def osc_terminate(self):
        if self.osc_client is not None:
            self.osc_client = None

    def open_cvWindow(self):
        if self.video_input_source.get() == g_webcam:
            print("try open webcam")
            self.cap = cv2.VideoCapture(0)
        elif self.video_input_source.get() == g_file:
            file_path = self.video_input_file.get()
            csv_file_path = self.video_input_file.get()
            print("try open CSV file: {}".format(csv_file_path))
            try:
                self.cap = cv2.VideoCapture(file_path)
            except Exception as e:
                print("Error opening CSV file: {}".format(e))
                self.csv_terminate()
        else:
            # Handle the case where no input source is selected
            self.cap = None
            print("No input source selected")
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Failed to open the webcam.")
            return
        self.cv2_window = cv2.namedWindow(g_videoWindowName, cv2.WINDOW_NORMAL)

    def cv2_terminate(self):
        print("cv2_terminate")
        # terminate the OpenCV stuff
        if self.cap is not None:
            print("cv2_terminate: cap is not None, release")
            self.cap.release()
            self.cap = None
        else:
            print("cv2_terminate: cap is already None")

        print("terminate here")
        cv2.destroyAllWindows()
        self.cv2_window = None
#        if self.video_thread:
#            self.video_thread.join()

    def start_video_loop(self):
        print("start_video_loop")
        # Code to start reading the input and calling pose_detector.process_frame() for each frame
        print("video_input_source: {}".format(self.video_input_source.get()))
        print("video_input_file: {}".format(self.video_input_file.get()))

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.open_zmq()
        self.open_osc()
        self.open_cvWindow()

        if not self.cap.isOpened():
            print("Video capture is NOT opened")
            return
        self.display_frames()
        #self.video_thread = threading.Thread(target=self.display_frames)
        #self.video_thread.start()

    def display_frames(self):
        print("display_frames()")
        self.running = True
        frameCount = 0
        loopcount = 1
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Calculate the delay based on the frame rate
        delay = int(1000 / fps)  # Delay in milliseconds

        while self.running:
            # Code to read the input and process frames using pose_detector.process_frame()
            ret, frame = self.cap.read()
            if not ret:
                print("Video capture read failed")
                if self.video_looping.get():
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    loopcount += 1
                    frameCount = 0
                    print("looping video, so retry)")
                    continue
                else:
                    print("not looping video, so break from running loop")
                    self.running = False
                    break
            frameCount += 1
            print("frameCount: {}".format(frameCount),"loopcount: {}".format(loopcount))
            height, width, channels = frame.shape
            #print('Frame size: {}x{}'.format(height, width))
            #print('Number of channels: {}'.format(channels))
            # here we process the frame, display and share it
            cv2.imshow(g_videoWindowName, frame)
            #print("shown frame")

            # Wait for the specified delay and check for key press
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                print("key pressed: q")
                break
        print("video loop ended, exit thread")
        self.stop_video_loop()

    def stop_video_loop(self):
        print("stop video loop")
        self.running = False
        self.zmq_terminate()
        self.osc_terminate()
        self.cv2_terminate()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)


    def on_closing(self):
        print("on_closing")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.cv2_window is not None:
            self.cv2.destroyAllWindows()
            self.cv2_window = None
        if self.root is not None:
            self.root.quit()
        self.root.destroy()
        self.root = None

# Create an instance of PoseDetector
pose_detector = None# PoseDetectorMediapipe()

# Create an instance of VideoApp and pass the PoseDetector instance
app = PoseApp(pose_detector)

# Run the application
app.run()
