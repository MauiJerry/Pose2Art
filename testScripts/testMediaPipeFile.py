import sys
import time, os
import numpy as np
import cv2
import NDIlib as ndi
from pythonosc import udp_client
from pose_detector import PoseDetectorMediapipe

def main():
    UDP_URL = "127.0.0.1"
    UDP_PORT = 5005
    client = udp_client.SimpleUDPClient(UDP_URL, UDP_PORT)
    try:
        client.send_message("/test", 1.0)
    except Exception as e:
        print("Error: Cannot send OSC message", e)


    # Open file
    #cap = cv2.VideoCapture(0)
    filename = 'videos/Fred Astaire Oscars.mov'
    #filename = 'videos/BakingBrains_a.mp4'

    try:
        cap = cv2.VideoCapture(filename)
        if cap is None or not cap.isOpened():
            print("Video capture failed")
            exit()
    except Exception as e:
        print("Video capture exception ", e)
        exit()
    print("Opened ",filename)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("video size: {} x {}".format(frame_width, frame_height))
    fps = cap.get(cv2.CAP_PROP_FPS)
    # Calculate the delay based on the frame rate
    video_delay = int(1000 / fps)  # Delay in milliseconds
    print("fps {} video delay: {} ms".format(fps, video_delay))

    if not ndi.initialize():
       print("Error: Cannot run NDI")
       exit()

    send_settings = ndi.SendCreate()
    send_settings.ndi_name = 'posePC'
    ndi_send = ndi.send_create(send_settings)
    video_frame = ndi.VideoFrameV2()

    pose_detector = PoseDetectorMediapipe()

    frameNum =0
    loopcount = 0

    while True:
        start_time = time.time()
        ret, frame = cap.read()  # Read a frame from the video

        if not ret:
            print("Video capture read failed")
            if True:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                loopcount += 1
                frameCount = 0
                print("looping video, so retry)")
                ret, frame = cap.read()
        frameNum = frameNum +1

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        video_frame.data = img
        video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX

        ndi.send_send_video_v2(ndi_send, video_frame)

        # Process the frame
        results = pose_detector.process_image(frame)
        print("frame, num landmarks", frameNum, pose_detector.get_num_landmarks())
        # Draw landmarks on the frame
        pose_detector.draw_landmarks(frame)
        pose_detector.send_landmarks_via_osc(client)
        try:
            client.send_message("/test", frameNum)
        except Exception as e:
            print("Error: Cannot send OSC message", e)

        # Display the frame
        cv2.imshow('Video', frame)

        # calculate the remaining frame delay to match the video frame rate
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        delay = max(video_delay - int(execution_time), 1)

        # Check if 'q' key is pressed to exit
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    # Release the video capture
    cap.release()

    # Close all OpenCV windows
    cv2.destroyAllWindows()

    return 0

if __name__ == "__main__":
    sys.exit(main())
