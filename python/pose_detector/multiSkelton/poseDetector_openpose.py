import cv2
import numpy as np
# Assuming OpenPose Python API is installed and accessible
# The exact import might vary based on your OpenPose installation path.
# For example, it might be:
# from openpose import pyopenpose as op
# or you might need to add its build directory to PYTHONPATH
try:
    import pyopenpose as op
except ImportError:
    print("Error: pyopenpose not found. Please ensure OpenPose is installed with Python bindings.")
    op = None

from pose_detector.pose_detector import PoseDetector, PoseData, LANDMARK_NAMES

class PoseDetectorOpenPose(PoseDetector):
    """
    Implements multi-person pose detection using OpenPose.
    Note: OpenPose installation is complex and often requires building from source.
    This class assumes pyopenpose is correctly installed and accessible.
    """
    def __init__(self, model_folder="/path/to/openpose/models/", num_poses=2):
        """
        Initializes the OpenPose detector.

        Args:
            model_folder (str): Path to the OpenPose models directory (e.g., 'models' in OpenPose root).
                                 Download models from OpenPose GitHub if not already present.
            num_poses (int): Maximum number of poses to detect (OpenPose handles this internally).
        """
        super().__init__()
        self.model_folder = model_folder
        self.num_poses = num_poses # OpenPose handles this internally
        self.op_wrapper = None
        self._initialize_detector()
        # OpenPose has its own drawing capabilities, but we'll adapt to base class draw_landmarks

        # OpenPose has a different landmark set, so we might need a mapping or adjust LANDMARK_NAMES
        # For simplicity, this example assumes a direct mapping or uses OpenPose's default output.
        # OpenPose typically outputs 25 body keypoints by default.
        # You might want to define a specific OPENPOSE_LANDMARK_NAMES if needed.
        # For a full implementation, you'd map OpenPose's output to your common LANDMARK_NAMES.
        # For now, we'll just use the raw OpenPose output structure.
        self.num_landmarks_per_person = 25 # Default COCO keypoints for OpenPose

    def _initialize_detector(self):
        """Initializes the OpenPose wrapper."""
        if op is None:
            print("OpenPose Python API (pyopenpose) not available. Skipping initialization.")
            return

        try:
            # Custom Params for OpenPose (adjust as needed)
            params = dict()
            params["model_folder"] = self.model_folder
            params["net_resolution"] = "-1x368" # Or "656x368" for better accuracy
            params["render_pose"] = 0 # Disable internal rendering to use OpenCV for display
            params["number_people_max"] = self.num_poses # Max people to detect

            # Starting OpenPose
            self.op_wrapper = op.WrapperPython()
            self.op_wrapper.configure(params)
            self.op_wrapper.start()
            print(f"OpenPose detector initialized with model folder: {self.model_folder}")
        except Exception as e:
            print(f"Error initializing OpenPose: {e}")
            self.op_wrapper = None

    def process_image(self, image):
        """
        Processes an image to detect multiple poses using OpenPose.
        Populates self.detected_poses with PoseData objects.

        Args:
            image (numpy.ndarray): The input image (BGR format from OpenCV).

        Returns:
            list: A list of PoseData objects if poses are detected, otherwise an empty list.
        """
        self.detected_poses = []
        if self.op_wrapper is None:
            print("OpenPose detector not initialized. Cannot process image.")
            return []

        self.image_height, self.image_width, _ = image.shape

        try:
            # Process image
            datum = op.Datum()
            datum.cvInputData = image
            self.op_wrapper.emplaceAndPop([datum])

            # Extract pose keypoints
            if datum.poseKeypoints is not None:
                # poseKeypoints shape: (num_persons, num_keypoints, 3) where last dim is (x, y, confidence)
                for person_keypoints in datum.poseKeypoints:
                    landmarks = []
                    bbox = [float('inf'), float('inf'), -float('inf'), -float('inf')] # x_min, y_min, x_max, y_max

                    for kp_id, keypoint in enumerate(person_keypoints):
                        x, y, conf = keypoint
                        # Normalize coordinates (0-1)
                        norm_x = x / self.image_width
                        norm_y = y / self.image_height

                        # OpenPose provides confidence per keypoint, not a single pose confidence.
                        # For simplicity, we'll use a dummy z (depth) for now, or average confidence.
                        # For now, we'll store confidence as z, and it's 2D.
                        landmarks.append(type('obj', (object,), {'x': norm_x, 'y': norm_y, 'z': conf})())

                        # Update bounding box
                        if conf > 0.05: # Only consider confident keypoints for bbox
                            bbox[0] = min(bbox[0], norm_x)
                            bbox[1] = min(bbox[1], norm_y)
                            bbox[2] = max(bbox[2], norm_x)
                            bbox[3] = max(bbox[3], norm_y)

                    # Convert bbox to [x_min, y_min, width, height]
                    if bbox[0] != float('inf'): # If any keypoints were found
                        bbox_final = [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]]
                    else:
                        bbox_final = None

                    # OpenPose doesn't provide a single pose confidence directly,
                    # so we can average keypoint confidences or set a default.
                    avg_confidence = np.mean(person_keypoints[:, 2]) if person_keypoints.shape[0] > 0 else None

                    self.detected_poses.append(PoseData(landmarks=landmarks, confidence=avg_confidence, bbox=bbox_final))
            return self.detected_poses
        except Exception as e:
            print(f"Error processing image with OpenPose: {e}")
            return []

    # You can override draw_landmarks if OpenPose's internal drawing is preferred,
    # or adapt the base class drawing to OpenPose's keypoint structure.
    # For now, the base class draw_landmarks will attempt to draw based on the PoseData structure.

