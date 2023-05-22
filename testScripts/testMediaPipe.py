import cv2
from pythonosc import udp_client

from pose_detector import PoseDetectorMediapipe

pose_detector = PoseDetectorMediapipe()

# Open webcam
cap = cv2.VideoCapture(0)
UDP_URL = "127.0.0.1"
UDP_PORT = 5005
client = udp_client.SimpleUDPClient(UDP_URL, UDP_PORT)

frameNum =0
while True:
    ret, frame = cap.read()  # Read a frame from the video

    if not ret:
        print("Failed to read frame")
        break
    frameNum = frameNum +1

    # Process the frame
    results = pose_detector.process_image(frame)
    print("frame, num landmarks", frameNum, pose_detector.get_num_landmarks())
    # Draw landmarks on the frame
    pose_detector.draw_landmarks(frame)
    pose_detector.send_landmarks_via_osc(client)

    # Display the frame
    cv2.imshow('Video', frame)

    # Check if 'q' key is pressed to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture
cap.release()

# Close all OpenCV windows
cv2.destroyAllWindows()

