class PoseDetector:
    def __init__(self):
        self.results = None
    def get_landmark_name(self, landmark_id):
        """
        Returns the name of the landmark given the landmark id
        Names are chosen to match Kinect where possible
        """
        raise NotImplementedError("get_landmark_name method must be implemented in subclass")

    def process_image(self, image):
        """
        Process the image using the pose detection model
        subclass must implement this method
        :param image:
        :return: nothing
        """
        raise NotImplementedError("process_image method must be implemented in subclass")

    def draw_landmarks(self, image):
        """
        Draw the pose landmarks over the image (optional)
        :param image:
        :return: nothing
        """
        raise NotImplementedError("draw_landmarks method must be implemented in subclass")

    def send_landmarks_via_osc(self, osc_client):
        """
        Send the pose landmarks via OSC (Open Sound Control)
        form should be /p1/landmark_name [x, y, z]
        may also send /image-height, /image-width, /numLandmarks
        :param osc_client:
        :return: nothing
        """
        raise NotImplementedError("send_landmarks_via_osc method must be implemented in subclass")
