import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Assuming pose_detector.py is in the same directory or accessible via PYTHONPATH
from pose_detector.pose_detector import PoseDetector, PoseData, LANDMARK_NAMES

class PoseDetectorMediapipe(PoseDetector):
    """
    Implements multi-person pose detection using MediaPipe Pose Landmarker.
    """
    def __init__(self, model_path="pose_landmarker_heavy.task", num_poses=2):
        """
        Initializes the MediaPipe Pose Landmarker.

        Args:
            model_path (str): Path to the MediaPipe pose landmarker model file (.task).
                              You'll need to download this model, e.g.,
                              https://developers.google.com/mediapipe/solutions/vision/pose_landmarker/python#model_options
                              'pose_landmarker_heavy.task' is generally recommended for accuracy.
            num_poses (int): Maximum number of poses to detect.
        """
        super().__init__()
        self.model_path = model_path
        self.num_poses = num_poses
        self.detector = None
        self._initialize_detector()
        # MediaPipe's drawing utilities are very helpful
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose

    def _initialize_detector(self):
        """Initializes the MediaPipe Pose Landmarker with multi-person options."""
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                output_segmentation_masks=False, # Not needed for skeletal tracking
                num_poses=self.num_poses,        # Crucial for multi-person detection
                min_pose_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.detector = vision.PoseLandmarker.create_from_options(options)
            print(f"MediaPipe Pose Landmarker initialized with model: {self.model_path}")
        except Exception as e:
            print(f"Error initializing MediaPipe Pose Landmarker: {e}")
            print("Please ensure the model file (e.g., 'pose_landmarker_heavy.task') is in the correct path.")
            self.detector = None # Ensure detector is None if initialization fails

    def process_image(self, image):
        """
        Processes an image to detect multiple poses using MediaPipe Pose Landmarker.
        Populates self.detected_poses with PoseData objects.

        Args:
            image (numpy.ndarray): The input image (BGR format from OpenCV).

        Returns:
            list: A list of PoseData objects if poses are detected, otherwise an empty list.
        """
        self.detected_poses = [] # Clear previous detections
        if self.detector is None:
            print("Pose detector not initialized. Cannot process image.")
            return []

        # Convert the OpenCV BGR image to MediaPipe's Image format (RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat. and RGB, data=image)

        # Update image dimensions
        self.image_height, self.image_width, _ = image.shape

        # Perform pose detection
        detection_result = self.detector.detect(mp_image)

        if detection_result and detection_result.pose_landmarks:
            for pose_landmarks in detection_result.pose_landmarks:
                # pose_landmarks is a list of NormalizedLandmark objects
                # MediaPipe's PoseLandmarker also provides a 'world_landmarks' attribute
                # if 3D coordinates are available, and 'segmentation_masks' if enabled.
                
                # For simplicity, we'll use the NormalizedLandmark objects directly
                # You might want to extract confidence or bounding box if the API provides it
                # For PoseLandmarker, confidence is per landmark, not a single pose confidence.
                # Bounding box can be inferred from min/max landmark coords, or some models provide it directly.
                
                # Create a PoseData object for each detected person
                self.detected_poses.append(PoseData(landmarks=pose_landmarks))
                
            return self.detected_poses
        return []

    def draw_landmarks(self, image):
        """
        Draws detected multi-person pose landmarks on the image using MediaPipe's drawing utilities.
        """
        if not self.detected_poses:
            return image

        for person_id, pose_data in enumerate(self.detected_poses):
            if not pose_data.landmarks:
                continue

            # Use MediaPipe's drawing utilities for accurate skeleton drawing
            # The pose_landmarks object is directly compatible.
            self.mp_drawing.draw_landmarks(
                image,
                pose_data.landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2), # Landmark color
                self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)  # Connection color
            )

            # Add person ID text
            if pose_data.landmarks:
                # Get approximate position for text (e.g., near the nose or top shoulder)
                # Assuming nose is landmark 0, or pick a stable point
                if len(pose_data.landmarks) > 0:
                    x_px = int(pose_data.landmarks[0].x * self.image_width)
                    y_px = int(pose_data.landmarks[0].y * self.image_height)
                    text_pos = (x_px + 10, y_px - 10)
                    cv2.putText(image, f"Person {person_id}", text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

            # Bounding box drawing (optional, can be calculated from landmarks if not provided by model)
            if pose_data.bbox:
                x_min, y_min, width_norm, height_norm = pose_data.bbox
                x1 = int(x_min * self.image_width)
                y1 = int(y_min * self.image_height)
                x2 = int((x_min + width_norm) * self.image_width)
                y2 = int((y_min + height_norm) * self.image_height)
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2) # Red bounding box

        return image

