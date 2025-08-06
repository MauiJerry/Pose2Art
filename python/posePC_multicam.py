"""
PoseApp class is a tkinter GUI for selecting video input and output
input can be the webcam or a file
send to ndi, and use PoseDetector to collect Pose and send via osc
"""

import cv2, os, time
import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk
from pythonosc import udp_client
import NDIlib as ndi
from pose_detector import PoseDetectorMediapipe
from getCamNames import  get_available_cameras

# define global strings for set/compare
g_webcam ="Webcam"
g_file = "File"
g_looping_prefix = "Loop Video:"
g_videoWindowName = "VideoStream"

class PoseApp:
    def __init__(self, pose_detector):
        global g_webcam, g_file
        self.pose_detector = pose_detector

        self.last_directory ='.'

        self.root = tk.Tk()
        self.root.title("Pose App")
        self.root.geometry("640x480")

        self.video_input_source = tk.StringVar(value=g_webcam)
        self.camId = 0
        self.video_cam_name = tk.StringVar(value='Select Camera')
        self.video_isWebcam = True

        self.video_looping = tk.BooleanVar(value=False)
        self.video_input_file = tk.StringVar()

        self.ndi_out_name = tk.StringVar(value="posePC")
        self.osc_output_ip = tk.StringVar(value="127.0.0.1")
        self.osc_output_port = tk.StringVar(value="5005")

        # a few local var to hold cv2 stuff
        self.cap = None

        self.osc_client = None

        result = ndi.initialize()
        assert result is True, "NDI Initialization failed"

        self.cameraNames = get_available_cameras()
        print("Camera Names", self.cameraNames)

        self.ndi_send = None
        self.video_frame = None

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
            initialdir= self.last_directory,
            title = "Select Video File",
            filetypes = [("Video Files", "*.mp4;*.avi;*.mov"), ("All Files", "*.*")]
        )
        if file_path:
            self.last_directory = os.path.dirname(file_path)
            self.video_input_file.set(file_path)
            self.video_input_source.set(g_file)

    def updateCamId(self, *args):
        # get the newly selected camera ID/Name
        # use those to update the dropDown label AND self.camId
        selected_item = self.video_cam_name.get()
        print("selected item=", selected_item)
        index = [key for key, value in self.cameraNames.items() if value == selected_item][0]
        self.camId = index
        print(f"Selected Cam Index:{index}=> {self.camId}, Selected Item: {selected_item}")

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

        #self.video_cam_name = self.cameraNames[self.camId]
        camDropDown = tk.OptionMenu(video_input_radio_frame, self.video_cam_name,
                                    *self.cameraNames.values(),
                                     command=self.updateCamId)
        camDropDown.pack(side='left')

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

        ndi_output_label = tk.Label(self.upper_canvas, text="NDI Video Out Name:")
        ndi_out_name_entry = tk.Entry(self.upper_canvas, textvariable=self.ndi_out_name)
        #
        ndi_output_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ndi_out_name_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        self.start_ndi_button = tk.Button(self.upper_canvas, text="Start NDI", command=self.start_ndi)
        self.stop_ndi_button = tk.Button(self.upper_canvas, text="Stop NDI", command=self.stop_ndi, state=tk.DISABLED)
        #
        self.start_ndi_button.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.stop_ndi_button.grid(row=5, column=2, sticky="w", padx=5, pady=5)

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
        print("looping is now", self.video_looping.get(), "and button text is", self.looping_button["text"])

    def start_ndi(self):
        send_settings = ndi.SendCreate()
        send_settings.ndi_name =  self.ndi_out_name.get()
        self.ndi_send = ndi.send_create(send_settings)
        self.video_frame = ndi.VideoFrameV2()

        self.start_ndi_button.config(state=tk.DISABLED)
        self.stop_ndi_button.config(state=tk.NORMAL)
    def stop_ndi(self):
        ndi.send_destroy(self.ndi_send)
        ndi.destroy()
        self.ndi_send = None
        self.video_frame = None

        self.start_ndi_button.config(state=tk.NORMAL)
        self.stop_ndi_button.config(state=tk.DISABLED)

    def start_osc(self):
        osc_ip= self.osc_output_ip.get()
        osc_port = int(self.osc_output_port.get())
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
                # find the web cam number
                self.cap = cv2.VideoCapture(self.camId, cv2.CAP_DSHOW)

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
        #print("Initial FPS", fps)
        # fps for webcam may be 0, so set to something useful
        if fps < 1:
            fps = 30
            #print("FPS too small", fps)
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
                    print("looping video, so retry)")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.loopcount += 1
                    self.frameCount = 0
                    ret, frame = self.cap.read()
                else:
                    print("not looping video, so break from running loop")
                    print("GUI should give error dialog here, update ui")
                    self.stop_video()
                    return

            if self.frameCount % 30:
                frame_height, frame_width, _  = frame.shape
                frame_width = int(frame_width)
                frame_height = int(frame_height)
                print("video size: {} x {}".format(frame_width, frame_height))

            # send the image via NDI
            if self.ndi_send is not None:
                frame_rgbA = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                self.video_frame.data = frame_rgbA
                self.video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_RGBX
                #self.video_frame.frame_rate_D = 1
                #self.video_frame.frame_rate_N = 120
                ndi.send_send_video_v2(self.ndi_send,self.video_frame)
            else:
                print("ndi_send is None")

            # process the frame with PoseDetector
            results = pose_detector.process_image(frame)
            if results and self.osc_client is not None:
                pose_detector.send_landmarks_via_osc(self.osc_client)
                pose_detector.draw_landmarks(frame)
            else:
                print("No pose detected")
                #return

            # convert pose+frame image to TK format and display
            # Create a PIL ImageTk object
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tkimage = ImageTk.PhotoImage(image=Image.fromarray(frame))
            #print("created tkimage : {}x{}".format(tkimage.width(), tkimage.height()))
            #image = tk.PhotoImage(master=self.bottom_canvas, width=frame_width, height=frame_height)                # Display the frame on the bottom canvas
            self.bottom_canvas.create_image(0, 0, anchor=tk.NW, image=tkimage, state="normal")
            self.bottom_canvas.image = tkimage  # Save a reference to prevent garbage collection
            self.bottom_canvas.update()

            self.frameCount += 1
            #print("frameCount: {}".format(frameCount), "loopcount: {}".format(loopcount))
            # calculate the remaining frame delay to match the video frame rate
            end_time = time.time()
            elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds
            delay = max(self.video_delay - int(elapsed_time), 1)
            print("elapsed_time {} vidDelay {} remaining delay: {}".format(elapsed_time, self.video_delay,delay))
            self.root.after(delay, display_frame)
            print("after root delay", delay)

        display_frame()
        print("End Video")

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
pose_detector = PoseDetectorMediapipe()

# Create an instance of VideoApp and pass the PoseDetector instance
app = PoseApp(pose_detector)

# Run the application
app.run()
