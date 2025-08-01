import cv2
import mediapipe as mp
from pythonosc import udp_client

# Define landmark names (MediaPipe's 33 landmarks)
# This mapping is crucial for consistent OSC addressing
LANDMARK_NAMES = [
    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer', 'right_eye_inner',
    'right_eye', 'right_eye_outer', 'left_ear', 'right_ear', 'mouth_left',
    'mouth_right', 'left_shoulder', 'right_shoulder', 'left_elbow',
    'right_elbow', 'left_wrist', 'right_wrist', 'left_pinky',
    'right_pinky', 'left_index', 'right_index', 'left_thumb',
    'right_thumb', 'left_hip', 'right_hip', 'left_knee', 'right_knee',
    'left_ankle', 'right_ankle', 'left_heel', 'right_heel', 'left_foot_index',
    'right_foot_index'
]

class PoseData:
    """
    A simple data structure to hold pose information for a single person.
    """
    def __init__(self, landmarks, confidence=None, bbox=None):
        # landmarks: List of MediaPipe NormalizedLandmark objects or similar
        self.landmarks = landmarks
        # confidence: Overall pose confidence (float)
        self.confidence = confidence
        # bbox: Normalized bounding box [x_min, y_min, width, height] (list of floats)
        self.bbox = bbox

class PoseDetector:
    """
    Base class for pose detection. Subclasses will implement specific ML models.
    """
    def __init__(self):
        self.detected_poses = []  # List of PoseData objects, one for each person
        self.image_width = 0
        self.image_height = 0
        self.num_landmarks_per_person = len(LANDMARK_NAMES)

    def process_image(self, image):
        """
        Abstract method to be implemented by subclasses.
        Processes an image to detect poses and populates self.detected_poses.
        """
        raise NotImplementedError("Subclasses must implement process_image()")

    def send_landmarks_via_osc(self, osc_client: udp_client.SimpleUDPClient):
        """
        Sends detected multi-person pose landmarks via OSC.
        """
        if not osc_client:
            print("OSC client not initialized.")
            return

        # Send global frame info
        osc_client.send_message("/image-height", self.image_height)
        osc_client.send_message("/image-width", self.image_width)
        osc_client.send_message("/numLandmarks", self.num_landmarks_per_person)
        osc_client.send_message("/numPersons", len(self.detected_poses))

        # Send per-person data
        for person_id, pose_data in enumerate(self.detected_poses):
            # Send landmark data
            for idx, landmark in enumerate(pose_data.landmarks):
                # Ensure landmark has x, y, z attributes (MediaPipe NormalizedLandmark)
                if hasattr(landmark, 'x') and hasattr(landmark, 'y') and hasattr(landmark, 'z'):
                    landmark_name = LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"unknown_{idx}"
                    osc_address = f"/person{person_id}/landmark/{landmark_name}"
                    osc_client.send_message(osc_address, [landmark.x, landmark.y, landmark.z])
                else:
                    print(f"Warning: Landmark {idx} for person {person_id} missing x, y, z attributes.")

            # Send optional confidence and bbox
            if pose_data.confidence is not None:
                osc_client.send_message(f"/person{person_id}/confidence", pose_data.confidence)
            if pose_data.bbox is not None and len(pose_data.bbox) == 4:
                osc_client.send_message(f"/person{person_id}/bbox", pose_data.bbox)

    def draw_landmarks(self, image):
        """
        Draws detected multi-person pose landmarks on the image.
        This is a generic drawing; subclasses might override for specific model visualizations.
        """
        if not self.detected_poses:
            return image

        for person_id, pose_data in enumerate(self.detected_poses):
            if not pose_data.landmarks:
                continue

            # Convert normalized landmarks to pixel coordinates for drawing
            h, w, _ = image.shape
            points = []
            for landmark in pose_data.landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                points.append((cx, cy))
                # Draw circles on landmarks
                cv2.circle(image, (cx, cy), 5, (0, 255, 0), cv2.FILLED) # Green circles

            # Draw connections (simplified for generic base class, subclasses will use mpDraw.POSE_CONNECTIONS)
            # This part is illustrative; a full connection drawing depends on specific skeleton definition.
            # For MediaPipe, you'd typically use mp.solutions.drawing_utils.draw_landmarks
            # You can add simple lines between key points for a basic visualization, e.g.:
            # if len(points) > 1:
            #     for i in range(len(points) - 1):
            #         cv2.line(image, points[i], points[i+1], (255, 0, 0), 2) # Blue lines

            # Add person ID text
            if points:
                text_pos = (points[0][0] + 10, points[0][1] - 10) # Near the first landmark (nose)
                cv2.putText(image, f"P{person_id}", text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA) # Yellow text

            # Draw bounding box if available
            if pose_data.bbox:
                x_min, y_min, width_norm, height_norm = pose_data.bbox
                x1 = int(x_min * w)
                y1 = int(y_min * h)
                x2 = int((x_min + width_norm) * w)
                y2 = int((y_min + height_norm) * h)
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2) # Red bounding box

        return image

