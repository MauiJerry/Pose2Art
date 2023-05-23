import tkinter as tk

import cv2
import tkinter as tk
from tkinter import filedialog, Menu
from PIL import ImageTk, Image
import zmq
from pythonosc import udp_client
import time

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
        self.root.title("Pose App")
        self.root.geometry("640x480")

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
        self.zmq_socket = None
        self.osc_client = None

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

        # Create the upper canvas
        self.upper_canvas = tk.Canvas(self.root, width=400, height=50)
        self.upper_canvas.pack()

        #############################################
        video_input_label = tk.Label(self.upper_canvas, text="Video Input:")
        video_input_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        video_input_radio_frame = tk.Frame(self.upper_canvas)
        video_input_webcam_radio = tk.Radiobutton(video_input_radio_frame, text=g_webcam,
                                                  variable=self.video_input_source, value=g_webcam)
        video_input_file_radio = tk.Radiobutton(video_input_radio_frame, text=g_file,
                                                variable=self.video_input_source, value=g_file)
        video_input_webcam_radio.pack(side="left")
        video_input_file_radio.pack(side="left")
        video_input_radio_frame.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        video_input_file_button = tk.Button(self.upper_canvas, text="Browse", command=self.set_video_input_file)
        video_input_file_entry = tk.Entry(self.upper_canvas, textvariable=self.video_input_file, state="readonly")
        video_input_file_button.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        video_input_file_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

        self.looping_button = tk.Button(self.upper_canvas,
                text=f"{g_looping_prefix} {'ON' if self.video_looping.get() else 'OFF'}",
                command=self.toggle_looping)
        self.looping_button.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        video_output_label = tk.Label(self.upper_canvas, text="Video ZMQ Output URL:")
        video_output_ip_entry = tk.Entry(self.upper_canvas, textvariable=self.video_output_ip)
        video_output_port_entry = tk.Entry(self.upper_canvas, textvariable=self.video_output_port)
        #
        video_output_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        video_output_ip_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        video_output_port_entry.grid(row=4, column=2, sticky="w", padx=5, pady=5)

        self.start_zmq_button = tk.Button(self.upper_canvas, text="Start", command=self.start_zmq)
        self.stop_zmq_button = tk.Button(self.upper_canvas, text="Stop ZMQ", command=self.stop_zmq, state=tk.DISABLED)
        #
        self.start_zmq_button.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.stop_zmq_button.grid(row=5, column=2, sticky="w", padx=5, pady=5)

        osc_output_label = tk.Label(self.upper_canvas, text="OSC Output URL:")
        osc_output_ip_entry = tk.Entry(self.upper_canvas, textvariable=self.osc_output_ip)
        osc_output_port_entry = tk.Entry(self.upper_canvas, textvariable=self.osc_output_port)
        #
        osc_output_label.grid(row=6, column=0, sticky="w", padx=5, pady=5)
        osc_output_ip_entry.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        osc_output_port_entry.grid(row=6, column=2, sticky="w", padx=5, pady=5)

        self.start_osc_button = tk.Button(self.upper_canvas, text="Start OSC", command=self.start_osc)
        self.stop_osc_button = tk.Button(self.upper_canvas, text="Stop OSC", command=self.stop_osc, state=tk.DISABLED)
        #
        self.start_osc_button.grid(row=7, column=1, sticky="w", padx=5, pady=5)
        self.stop_osc_button.grid(row=7, column=2, sticky="w", padx=5, pady=5)

        self.start_video_button = tk.Button(self.upper_canvas, text="Play Video", command=self.play_video)
        self.stop_video_button = tk.Button(self.upper_canvas, text="Stop Video", command=self.stop_video, state=tk.DISABLED)
        self.start_video_button.grid(row=8, column=0, sticky="w", padx=5, pady=5)
        self.stop_video_button.grid(row=8, column=1, sticky="w", padx=5, pady=5)

        self.height_upper = self.upper_canvas.winfo_height()
        # Create the bottom canvas
        self.bottom_canvas = tk.Canvas(self.root, width=100, height=100)
        self.bottom_canvas.pack(side=tk.LEFT, padx=5)
        self.bottom_canvas.configure(relief="raised")

    def toggle_looping(self):
        self.video_looping.set(not self.video_looping.get())
        self.looping_button["text"] = \
            f"{g_looping_prefix} {'ON' if self.video_looping.get() else 'OFF'}"
        print("Var is now", self.video_looping.get(), "and button text is", self.looping_button["text"])

    def start_zmq(self):
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
        self.start_zmq_button.config(state=tk.DISABLED)
        self.stop_zmq_button.config(state=tk.NORMAL)
    def stop_zmq(self):
        if self.zmq_socket is not None:
            self.zmq_socket.close()
            self.zmq_socket = None
        if self.zmq_context is not None:
            self.zmq_context.term()
            self.zmq_context = None
        self.start_zmq_button.config(state=tk.NORMAL)
        self.stop_zmq_button.config(state=tk.DISABLED)

    def start_osc(self):
        osc_ip= self.osc_output_ip.get()
        osc_port = self.osc_output_port.get()
        print("try open OSC URL: ",osc_ip,osc_port)
        try:
            self.osc_client = udp_client.SimpleUDPClient(osc_ip,osc_port)
            print("OSC socket opened")
        except Exception as e:
            print("Error opening OSC socket: {}".format(e))
            self.osc_terminate()
        self.start_osc_button.config(state=tk.DISABLED)
        self.stop_osc_button.config(state=tk.NORMAL)

    def stop_osc(self):
        if self.osc_client is not None:
            self.osc_client = None
        self.start_osc_button.config(state=tk.NORMAL)
        self.stop_osc_button.config(state=tk.DISABLED)

    #  def cv2_terminate(self):
    #    print("cv2_terminate")
    #    # terminate the OpenCV stuff
    #    if self.cap is not None:
    #        print("cv2_terminate: cap is not None, release")
    #        self.cap.release()
    #        self.cap = None
    #    else:
    #        print("cv2_terminate: cap is already None")
    def play_video(self):
        self.height_upper = self.upper_canvas.winfo_height()
        print("Upper canvas height:", self.height_upper)
        print("Source:", self.video_input_source.get())
        try:
            if self.video_input_source.get() == g_webcam:
                print("try open webcam")
                self.cap = cv2.VideoCapture(0)
            elif self.video_input_source.get() == g_file:
                file_path = self.video_input_file.get()
                print("try open video file: {}".format(file_path))
                try:
                    self.cap = cv2.VideoCapture(file_path)
                except Exception as e:
                    print("Error opening video file: {}".format(e))
                    return
            else:
                # Handle the case where no input source is selected
                self.cap = None
                print("No input source selected")

        except Exception as e:
            print("Error opening video capture: {}".format(e))
            return
        if self.cap is None:
            print("cap is None")
            return
        if not self.cap.isOpened():
            print("Failed to open file.")
            return

        print("start_video_loop")
        # Code to start reading the input and calling pose_detector.process_frame() for each frame
        print("video_input_source: {}".format(self.video_input_source.get()))
        print("video_input_file: {}".format(self.video_input_file.get()))

        self.start_video_button.config(state=tk.DISABLED)
        self.stop_video_button.config(state=tk.NORMAL)

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Calculate the delay based on the frame rate
        self.video_delay = int(1000 / fps)  # Delay in milliseconds

        # Resize the app window to match the video size
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("video size: {} x {}".format(frame_width, frame_height))
        self.root.geometry(f"{frame_width}x{frame_height + self.height_upper}")
        self.bottom_canvas.configure(width=frame_width, height=frame_height)
        self.running = True
        self.frameCount = 0
        self.loopcount = 1
        print("running is", self.running)

        def display_frame():
            print("display_frame {} {} {}".format(self.running, self.frameCount, self.loopcount))
            start_time = time.time()
            if not self.running:
                print("display_frame: not running, so return")
                return

            # Code to read the input and process frames using pose_detector.process_frame()
            ret, frame = self.cap.read()
            if not ret:
                print("Video capture read failed")
                if self.video_looping.get():
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.loopcount += 1
                    self.frameCount = 0
                    print("looping video, so retry)")
                    ret, frame = self.cap.read()
                else:
                    print("not looping video, so break from running loop")
                    self.running = False
                    return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


            # send the raw image to the ZMQ socket
            # process the frame with PoseDetector
            # overlay the pose on copy of the image
            # convert pose+frame image to TK format and display
            # Create a PIL ImageTk object

            tkimage = ImageTk.PhotoImage(image=Image.fromarray(frame))
            #print("created tkimage : {}x{}".format(tkimage.width(), tkimage.height()))
            #image = tk.PhotoImage(master=self.bottom_canvas, width=frame_width, height=frame_height)                # Display the frame on the bottom canvas
            self.bottom_canvas.create_image(0, 0, anchor=tk.NW, image=tkimage, state="normal")
            self.bottom_canvas.image = tkimage  # Save a reference to prevent garbage collection
            self.bottom_canvas.update()

            self.frameCount += 1
            #print("frameCount: {}".format(frameCount), "loopcount: {}".format(loopcount))
            #height, width, channels = frame.shape
            # print('Frame size: {}x{}'.format(height, width))
            # print('Number of channels: {}'.format(channels))
            # here we process the frame, display and share it
            # self.pose_detector.process_frame(frame)
            # frame_copy,draw into frame_copy, set canvas image to frame_copy
            # send original frame to ZMQ socket
            # send landmarks via OSC

            # calculate the remaining frame delay to match the video frame rate
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            delay = max(self.video_delay - int(execution_time), 1)
            print("actual delay: {}".format(delay))
            self.root.after(delay, display_frame)

        display_frame()

    def stop_video(self):
        print("stop video loop")
        self.running = False
        if self.cap is not None:
            print("stop_video: cap is not None, release")
            self.cap.release()
        self.cap = None
        self.start_video_button.config(state=tk.NORMAL)
        self.stop_video_button.config(state=tk.DISABLED)

    def on_closing(self):
        print("on_closing")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
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
