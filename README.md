# Pose2Art: smartCamera Pose to TouchDesigner etc

Pose2Art creates an AI Camera that can run on small 'edge' device that extract Pose and sends tracked points via OSC to TouchDesigner (and Unity/UnReal) for ART!

The project is documented in longer form in the Hackaday.io project [Pose2Art: SmartCam to TouchDesigner, Unity via OSC](https://hackaday.io/project/188345-pose2art-smartcam-to-touchdesigner-unity-via-osc).  It is an evolving project, with the initial setups (esp pushing into Raspberry Pi) being a bit complex, so see that project for the how-to as well as discussion of details of the code, etc. As of June 2023, this repo is ahead of Hackaday project,

![Pose2Art Concept](https://photos.app.goo.gl/y4pmms1N1JPyVgMf6)

![Quick Video Demo1](https://photos.app.goo.gl/uPo9WM19AiW8XYXp8)

![Video with Fluid Sim](https://photos.app.goo.gl/8rxi97qLAv2Bf4Fq8)

See related repo [pyUdpTest](https://github.com/MauiJerry/pyUdpTest) for udp sender/receiver tests. These can be used to test both the udp connection, and as receiver of OSC messages. (TL:DR turn off windows defender)

There are a couple tools to implement the pose capture and sending OSC, along with a number of TouchDesigner applications that utilize the messages.
- **pose_PC_MediaPipe.py**: python tool for PC, sending 33 landmarks 
- **pose_rPi_TFLite.cpp**: raspberryPi4 c++ program, sending 17 landmarks  (in subfolder rPi_prototypes)
- **posePCGui.py**: Python TK gui over pose_detector; select webcam/file, ndi name, osc IP/port, loop video. Displays in TK window as well as sending osc and orig image via NDI
- **pose_detector** package (subfolder) 
    - **pose_detector.py**: PoseDetector base class
	- **pose_detector_mediapipe**: PoseDetectorMediapipe version
	- **alphapose.py** : stub that might support alphapose

Sample TouchDesigner apps:
- **poseOSC_dots.toe** is a simple TouchDesigner app that reads the osc landmark messages and displays them as dots.
- **pose_OSC_Sender.py** is a python app for testing OSC Messages. Initially it sends 17 or 33 landmarks plus the Frame messages. A sendBundle() is provided to test if receivers can handle OSC Bundles.
- **handDrawing.toe**: revision of example from HQPro to use OSC instead of kinect (part of paid course)
-- [Immersive Design & Creative Technology Mini-Degree/Pillars/Kinect 2 Fundamentals/05 - Drawing with Kinect Skeleton Data](https://hqpro.interactiveimmersive.io/products/immersive-design-creative-technology-mini-degree/categories/2151460601/posts/2162173127)
- **handDrawing_wNDI.toe**: TD app maps over ndi from posePCGui 
- **landmarksAsSpheres.toe** puts a sphere at each landmark (incl face?)
- **landmarksAsGeom_wNDI.toe** similar to sphere, also rcvs video via NDI
- **handsAsEmitters.toe** particle emitters at hand tips (vid save to file)
- **OSC_TubularTrim.toe** make flat/tube skeleton between landmarks
- **osc_fluidHand.toe** fluid emitter on hands using two [Fluid_simulation.tox](https://derivative.ca/community-post/asset/fluid-simulation-component/65741)

The **testScripts folder** holds scaffolding test tools
    * oscServer.py: pythonosc server that prints received messages
    * send_capture.py: NDI example with minor changes
    * testMediaPipe.py: tests PoseDetectorMediapipe with webcam
    * testMediaPipeFile.py: tests PoseDetectorMediapipe with video file
    * udpServerPrint.py: udp socket server prints data received

A number of explorations are NOT in git at this time. Mostly these are various TouchDesigner apps that explore different effects off the skeleton.  I've also been looking into alternative Pose2Art cameras that can do multiple person and/or Hand Tracking and Gestures recognition.

# Critique

Initially there were 2 hardware SmartCamera for Pose_OSC: a PC's webcam and raspberryPi4.  The PC can do a respectable frame rate with decent graphics board. My PC webcam gets about 28fps, which is decent. The rPi4 about 8-9fps, which is not good enough for interactive work.  Maybe the Jetson Nano or Coral dev boards will be better.  Meanwhile, we at least have a path for getting ML data into TouchDesigner via OSC.  This method could be extended for multiple person tracking (on fast hardware), object detection or other ML processing. The OSC messages will need to change for those new applications, so when you fork this, document them ;-)

### Credit Where Credit Due

The initial code is derived from other projects on GitHub/web.
- **pose_PC_MediaPipe.py** and TouchDesigner **poseOSC_dots.toe** come from [cronin4392's TouchDesigner-OpenCV-OSC project](https://github.com/cronin4392/TouchDesigner-OpenCV-OSC) (MIT License)
- **pose_rPi_TFLite** files come from Q-Engineering's rPi image projects (BSD 3-Clause License)
	- https://github.com/Qengineering/TensorFlow_Lite_Pose_RPi_64-bits
	- https://github.com/Qengineering/RPi-image
- Fluid Simulation relies on [Bruno Imbrizi's youTube tutorial](https://www.youtube.com/watch?v=2k6H5Qa_fCE) and Kurt Kaminski's uploading of that as a [TOX on Community.Derivative](
https://derivative.ca/community-post/asset/fluid-simulation-component/65741).  Kurt has a [revised version on GitHub](https://github.com/kamindustries/touchFluid)

