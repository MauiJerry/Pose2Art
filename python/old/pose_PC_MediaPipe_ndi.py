# modified from orig: new URL, added OSC msgs for image h,w, numchannels
# forked from https://github.com/cronin4392/TouchDesigner-OpenCV-OSC
import time
import cv2
import mediapipe as mp
from pythonosc import udp_client
import NDIlib as ndi

# Create our UDP client which we'll send OSC through
# Change the URL and port to whatever fits your needs
# mauiJerry: use our PC's static ip in prep for running on Raspberry Pi
#UDP_URL = "10.10.10.10" #"127.0.0.1"
UDP_URL = "127.0.0.1"
UDP_PORT = 5005
client = udp_client.SimpleUDPClient(UDP_URL, UDP_PORT)


if not ndi.initialize():
   print("Error: Cannot run NDI")
   exit()

send_settings = ndi.SendCreate()
send_settings.ndi_name = 'ndi-python'
ndi_send = ndi.send_create(send_settings)
video_frame = ndi.VideoFrameV2()
print("ndi setup done")

# Initialize some mediapipe pose stuff
# the static_image_mode=False tells it to track across vid frames
mpPose = mp.solutions.pose
pose = mpPose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils

# names of kinect and mediapipe landmarks
landmarkNames = [
    'head',
    'mp_eye_inner_l',
    'eye_l',
    'mp_eye_outer_l',
    'mp_eye_inner_r',
    'eye_r',
    'mp_eye_outer_e',
    'mp_ear_l',
    'mp_ear_r',
    'mp_mouth_l',
    'mp_mouth_r',
    'shoulder_l',
    'shoulder_r',
    'elbow_l',
    'elbow_r',
    'wrist_l',
    'wrist_r',
    'mp_pinky_l',
    'mp_pinky_r',
    'handtip_l',
    'handtip_r',
    'thumb_l',
    'thumb_r',
    'hip_l',
    'hip_r',
    'knee_l',
    'knee_r',
    'ankle_l',
    'ankle_r',
    'mp_heel_l',
    'mp_heel_r',
    'foot_l',
    'foot_r',
 #   'shoulder_c',
 #   'spine'
]

# Create a map to look up name given id
pose_id_to_name = {i: name for i, name in enumerate(landmarkNames)}

def test_name_map(id=6):
    name = pose_id_to_name.get(id)
    if name:
        print(f"The name for ID {id} is '{name}'.")
    else:
        print(f"No name found for ID {id}.")
test_name_map()

# Helper function to normalize direction and scale of y axis for TouchDesigner
def adjustY(y, w, h):
    return (1 - y) * (h / w)

num_landmarks =0
loopCount = 0
while True:
    #now doing this in a loop so we replay video indefintely
    # Initialize our video source. It can be a file or a webcam.
    # cap = cv2.VideoCapture(0)
    #cap = cv2.VideoCapture('videos/BakingBrains_a.mp4')
    #cap = cv2.VideoCapture('videos/JustSomeMotion.mov')
    #cap = cv2.VideoCapture('videos/body made of water.mov')
    #cap = cv2.VideoCapture('videos/Coreografia.mov')
    cap = cv2.VideoCapture('videos/Fred Astaire Oscars.mov')
    frameCount = 0
    loopCount = loopCount + 1

    # Create an RTSP stream output
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print("Stream width, height, fps", width, height, fps)

    while True:
        startTime = time.time()
        success, img = cap.read()
        if success != True:
            print("Read Failed,End of File?")
            break # end of file, reload/repeat
        frameCount = frameCount + 1

        #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        imgRGBA = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)

        image_height, image_width, _ = img.shape

        video_frame.data = imgRGBA
        video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX
        ndi.send_send_video_v2(ndi_send, video_frame)
        print("ndi send done")

        results = pose.process(img)

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
            #print("height, width, num marks", image_height, image_width,num_landmarks)

            for id, lm in enumerate(results.pose_landmarks.landmark):
                # Draw circles on the pose areas. This is purely for debugging
                cx, cy = int(lm.x * image_width), int(lm.y * image_height)
                cv2.circle(img, (cx, cy), 5, (255,0,0), cv2.FILLED)

                point_name = pose_id_to_name.get(id)
                # Send our values over OSC once w/all 3 values in one msg
                # this saves in the comm layers at expense of parsing in TD
                # note using uv screen space soords rather than xyz
                # and z is actually Confidence
                client.send_message(f"/p1/{point_name}", [lm.x,lm.y,lm.z])
                # could send as 3 OSC msgs to better match kinect names
                #client.send_message(f"/p1/{point_name}:u", lm.x)
                #client.send_message(f"/p1/{point_name}:v", lm.y)#adjustY(lm.y, image_width, image_height))
                #client.send_message(f"/p1/{point_name}:tz", lm.z)

        endTime = time.time()
        elapsedTime = endTime - startTime
        fps = 1.0/elapsedTime
        print("Loop %d Frame %d Rate %.2f Elapsed %.2f" %
              (loopCount,frameCount,fps,elapsedTime))
        cv2.imshow("Image", img)
        cv2.waitKey(1)
    print("Loop Video")