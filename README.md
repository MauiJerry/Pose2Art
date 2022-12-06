# Pose2Art: smartCamera Pose to TouchDesigner etc

Pose2Art creates an AI Camera run on small 'edge' device that extract Pose and sends tracked points via OSC to TouchDesigner and Unity/UnReal for ART!

The project is document in longer form on Hackaday.io in 
   https://hackaday.io/project/188345-pose2art-smartcam-to-touchdesigner-unity-via-osc
Installation is a bit complex, so see that project the how-to as well as discussion of details of the code, etc.

The initial code is derived from two other projects on GitHub/web.
The pose_PC_MediaPipe.py and TouchDesigner poseOSC_dots come from https://github.com/cronin4392/TouchDesigner-OpenCV-OSC (MIT License)
The pose_rPi_TFLite files come from Q-Engineering's rPi image projects (BSD 3-Clause License)
	https://github.com/Qengineering/TensorFlow_Lite_Pose_RPi_64-bits
	https://github.com/Qengineering/RPi-image

