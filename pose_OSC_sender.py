# modified from pose_PC_MediaPipe.py to be generic OSC message testbed
import random
import numpy as np
import time
from pythonosc import udp_client

# Create our UDP client which we'll send OSC through
# Change the URL and port to whatever fits your needs
UDP_URL = "10.10.10.10" #"127.0.0.1"
UDP_PORT = 5005
client = udp_client.SimpleUDPClient(UDP_URL, UDP_PORT)

# some bits to characterize our ML models
tflite_numMarks = 17
mediapipe_numMarks = 33

# OSC Frame info variables
num_landmarks = tflite_numMarks
image_height = 480
image_width = 640

def sendPoseFrameInfo():
    client.send_message(f"/image-height", image_height)
    client.send_message(f"/image-width", image_width)
    client.send_message(f"/numLandmarks", num_landmarks)
    print("frame height, width, num marks", image_height, image_width, num_landmarks)

# a 3d point for landmark xy 0-1.0 location and z= confidence -10.0:10.0
class Point3D:
    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        self.x, self.y, self.z = x, y, z

    def __repr__(self):
        return f'Point3D({self.x:.2f},{self.y:.2f},{self.z:.2f})'

def randomPt3D():
    # generate a Point3d with random in range values
    x = random.random()
    y = random.random()
    z = random.uniform(-5.0,5.0)
    pt =Point3D(x,y,z)
    return pt


landmarks = [] # array of numLandmarks with of 3 float values (xyz) each

def initialLandmarks():
    global landmarks
    landmarks=[]
    for i in range(0,num_landmarks):
        landmarks.append(randomPt3D())
    print("Initial Landmarks ",landmarks)

def sendPoseLandmarks():
    global landmarks
    for idx, pt in enumerate(landmarks):
        # Send our values over OSC
        client.send_message(f"/landmark-{idx}-x", pt.x)
        client.send_message(f"/landmark-{idx}-y", pt.y)
        client.send_message(f"/landmark-{idx}-z", pt.z)
        print("osc /landmark ", idx, pt)

def moveLandmarks():
    global landmarks
    xRange = 10.0 / image_width
    yRange = 10.0 / image_height
    zRange = 1.0
    for idx, pt in enumerate(landmarks):
        pt.x = pt.x + random.uniform(-xRange,xRange)
        pt.y = pt.y + random.uniform(-yRange, yRange)
        pt.z = pt.z + random.uniform(-zRange, zRange)

#def sendBundle():

# main loop
initialLandmarks()
step =0
while True:
    step = step+1
    print("Step ", step, landmarks)
    moveLandmarks()
    sendPoseFrameInfo()
    sendPoseLandmarks()
    time.sleep(1)
