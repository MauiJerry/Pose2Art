# Pose2Art: smartCamera Pose to TouchDesigner etc

Pose2Art creates an AI Camera run on small 'edge' device that extract Pose and sends tracked points via OSC to TouchDesigner and Unity/UnReal for ART!

The project is documented in longer form in the Hackaday.io project [Pose2Art: SmartCam to TouchDesigner, Unity via OSC](https://hackaday.io/project/188345-pose2art-smartcam-to-touchdesigner-unity-via-osc) Installation is a bit complex, so see that project the how-to as well as discussion of details of the code, etc.

See related repo [pyUdpTest](https://github.com/MauiJerry/pyUdpTest) for udp sender/receiver tests. These can be used to test both the udp connection, and as receiver of OSC messages.

Initially, one of two OpenCV+PoseEsitimation tools capture frames, extract Pose Landmarks and send via OSC Messages to a TouchDesigner application. 
- **pose_PC_MediaPipe.py** is a python tool for PC, sending 33 landmarks 
- **pose_rPi_TFLite.cpp** is raspberryPi4 c++ program, sending 17 landmarks  
- **poseOSC_dots.toe** is a simple TouchDesigner app that reads the osc landmark messages and displays them as dots.  

- **pose_OSC_Sender.py** is a python app for testing OSC Messages. Initially it sends 17 or 33 landmarks plus the Frame messages. A sendBundle() is provided to test if receivers can handle OSC Bundles.

# Critique

Initially there are 2 hardware SmartCamera for Pose_OSC: a PC's webcam and raspberryPi4.  The PC can do a respectable frame rate with decent graphics board. My PC webcam gets about 28fps, which is decent. The rPi4 about 8-9fps, which is not good enough for interactive work.  Maybe the Jetson Nano or Coral dev boards will be better.  Meanwhile, we at least have a path for getting ML data into TouchDesigner via OSC.  This method could be extended for multiple person tracking (on fast hardware), object detection or other ML processing. The OSC messages will need to change for those new applications, so when you fork this, document them ;-)

### Credit Where Credit Due

The initial code is derived from two other projects on GitHub/web.
- **pose_PC_MediaPipe.py** and TouchDesigner **poseOSC_dots.toe** come from [cronin4392's TouchDesigner-OpenCV-OSC project](https://github.com/cronin4392/TouchDesigner-OpenCV-OSC) (MIT License)
- **pose_rPi_TFLite** files come from Q-Engineering's rPi image projects (BSD 3-Clause License)
	- https://github.com/Qengineering/TensorFlow_Lite_Pose_RPi_64-bits
	- https://github.com/Qengineering/RPi-image


