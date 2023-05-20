import mediapipe as mp

from pythonosc import udp_client
from .pose_detector import PoseDetector

class PoseDetectorMediapipe(PoseDetector):
    pose_id_to_name = {
        0: 'head',
        1: 'mp_eye_inner_l',
        2: 'eye_l',
        3: 'mp_eye_outer_l',
        4: 'mp_eye_inner_r',
        5: 'eye_r',
        6: 'mp_eye_outer_e',
        7: 'mp_ear_l',
        8: 'mp_ear_r',
        9: 'mp_mouth_l',
        10: 'mp_mouth_r',
        11: 'shoulder_l',
        12: 'shoulder_r',
        13: 'elbow_l',
        14: 'elbow_r',
        15: 'wrist_l',
        16: 'wrist_r',
        17: 'mp_pinky_l',
        18: 'mp_pinky_r',
        19: 'handtip_l',
        20: 'handtip_r',
        21: 'thumb_l',
        22: 'thumb_r',
        23: 'hip_l',
        24: 'hip_r',
        25: 'knee_l',
        26: 'knee_r',
        27: 'ankle_l',
        28: 'ankle_r',
        29: 'mp_heel_l',
        30: 'mp_heel_r',
        31: 'foot_l',
        32: 'foot_r'
    }

    def __init__(self):
        super().__init__()
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mpDraw = mp.solutions.drawing_utils
        self.results = None

    def process_image(self, image):
        self.results = self.pose.process(image)
        return self.results

    def get_num_landmarks(self):
        if self.results is None:
            return 0
        if self.results.pose_landmarks is not None:
            return len(self.results.pose_landmarks.landmark)
        return 0

    def draw_landmarks(self, image):
        if self.results is not None:
            landmarks = self.results.pose_landmarks
            if landmarks is not None:
                self.mpDraw.draw_landmarks(
                    image,
                    landmarks,
                    self.mp_pose.POSE_CONNECTIONS)

    def get_pose_name(self, pose_id):
        return self.pose_id_to_name.get(pose_id, "Unknown")

    def send_landmarks_via_osc(self, osc_client):
        if self.results is not None:
            if self.results.pose_landmarks is not None:
                for idx, lm in enumerate(self.results.pose_landmarks.landmark):
                    osc_client.send_message(f"p1/{self.get_pose_name(idx)}", [lm.x, lm.y, lm.z])


