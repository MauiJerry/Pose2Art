class PoseDetector:
    def __init__(self):
        self.results = None

    def process_image(self, image):
        raise NotImplementedError("process_image method must be implemented in subclass")

    def draw_landmarks(self, image):
        raise NotImplementedError("draw_landmarks method must be implemented in subclass")

    def send_landmarks_via_osc(self, osc_client, channel_prefix):
        raise NotImplementedError("send_landmarks_via_osc method must be implemented in subclass")
