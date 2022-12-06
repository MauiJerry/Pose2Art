# modified from orig: new URL, added OSC msgs for image h,w, numchannels
# forked from https://github.com/cronin4392/TouchDesigner-OpenCV-OSC
import cv2
import mediapipe as mp
from pythonosc import udp_client

# Create our UDP client which we'll send OSC through
# Change the URL and port to whatever fits your needs
# mauiJerry: use our PC's static ip in prep for running on Raspberry Pi
UDP_URL = "10.10.10.10" #"127.0.0.1"
UDP_PORT = 5005
client = udp_client.SimpleUDPClient(UDP_URL, UDP_PORT)

# Initialize some mediapipe stuff
mpPose = mp.solutions.pose
pose = mpPose.Pose()
mpDraw = mp.solutions.drawing_utils

# Initialize our video source. It can be a file or a webcam.
cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture('dancing.mp4')

# Helper function to normalize direction and scale of y axis for TouchDesigner
def adjustY(y, w, h):
    return (1 - y) * (h / w)

num_landmarks =0
while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    image_height, image_width, _ = imgRGB.shape
    results = pose.process(imgRGB)

    if results.pose_landmarks:
        # first time, count number of landmarks pose model finds
        if num_landmarks < 1:
            # how do we get len/size of landmarks?
            for id, lm in enumerate(results.pose_landmarks.landmark):
                num_landmarks = num_landmarks+1
        # draw landmark connection lines (skeleton)
        mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)

        client.send_message(f"/image-height", image_height)
        client.send_message(f"/image-width", image_width)
        client.send_message(f"/numLandmarks", num_landmarks)
        print("height, width, num marks", image_height, image_width,num_landmarks)

        for id, lm in enumerate(results.pose_landmarks.landmark):
            x = lm.x
            y = lm.y
            z = lm.z

            # Send our values over OSC
            client.send_message(f"/landmark-{id}-x", x)
            client.send_message(f"/landmark-{id}-y", adjustY(y, image_width, image_height))
            client.send_message(f"/landmark-{id}-z", z)

            # Draw circles on the pose areas. This is purely for debugging
            cx, cy = int(x * image_width), int(y * image_height)
            cv2.circle(img, (cx, cy), 5, (255,0,0), cv2.FILLED)

    cv2.imshow("Image", img)
    cv2.waitKey(1)