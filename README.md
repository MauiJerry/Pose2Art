# Pose2Art: smartCamera Pose to TouchDesigner etc

Pose2Art creates an AI Camera run on small 'edge' device that extract Pose and sends tracked points via OSC to TouchDesigner and Unity/UnReal for ART!

The project is documented in longer form on Hackaday.io in 
   https://hackaday.io/project/188345-pose2art-smartcam-to-touchdesigner-unity-via-osc
Installation is a bit complex, so see that project the how-to as well as discussion of details of the code, etc.

See also https://github.com/MauiJerry/pyUdpTest for udp sender/receiver tests. These can be used to test both the udp connection, and as receiver of OSC messages.
pose_OSC_Sender.py is a python app for testing OSC Messages. Initially it sends 17 or 33 landmarks plus the Frame messages. A sendBundle() is provided to test if receivers can handle OSC Bundles.

Initially, one of two OpenCV+PoseEsitimation tools capture frames, extract Pose Landmarks and send via OSC Messages to TouchDesigner. "pose_PC_MediaPipe.py" is a python tool for PC, while "pose_rPi_TFLite.cpp" is raspberryPi4 c++ program.  "poseOSC_dots.toe" is a simple TouchDesigner app that reads the osc landmark messages and displays them as dots.  

The initial code is derived from two other projects on GitHub/web.
The pose_PC_MediaPipe.py and TouchDesigner poseOSC_dots come from https://github.com/cronin4392/TouchDesigner-OpenCV-OSC (MIT License)
The pose_rPi_TFLite files come from Q-Engineering's rPi image projects (BSD 3-Clause License)
	https://github.com/Qengineering/TensorFlow_Lite_Pose_RPi_64-bits
	https://github.com/Qengineering/RPi-image


