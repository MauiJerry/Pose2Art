import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

from pose_detector.pose_detector import PoseDetector, PoseData, LANDMARK_NAMES

class PoseDetectorMoveNet(PoseDetector):
    """
    Implements multi-person pose detection using Google's MoveNet (MultiPose variant).
    Requires TensorFlow and TensorFlow Hub.
    """
    def __init__(self, model_url="https://tfhub.dev/google/movenet/multipose/lightning/1", num_poses=2):
        """
        Initializes the MoveNet detector.

        Args:
            model_url (str): URL to the MoveNet MultiPose model from TensorFlow Hub.
                             'multipose/lightning/1' for speed, 'multipose/thunder/1' for accuracy.
            num_poses (int): Maximum number of poses to detect.
        """
        super().__init__()
        self.model_url = model_url
        self.num_poses = num_poses
        self.interpreter = None
        self.input_size = 256 # MoveNet Lightning's typical input size
        self._initialize_detector()
        # MoveNet typically outputs 17 keypoints (COCO format)
        # You might need to map these to your LANDMARK_NAMES if they differ.
        self.num_landmarks_per_person = 17 # Default COCO keypoints for MoveNet

    def _initialize_detector(self):
        """Initializes the MoveNet model from TensorFlow Hub."""
        try:
            # Load the model from TensorFlow Hub
            model = hub.load(self.model_url)
            self.interpreter = model.signatures['serving_default']
            
            # Determine input size from model if possible, or set default
            if 'input_1' in self.interpreter.inputs[0].name: # Check for common input name
                self.input_size = self.interpreter.inputs[0].shape[1]
            print(f"MoveNet detector initialized with model: {self.model_url}, input size: {self.input_size}")
        except Exception as e:
            print(f"Error initializing MoveNet: {e}")
            print("Please ensure TensorFlow and TensorFlow Hub are installed and the model URL is correct.")
            self.interpreter = None

    def process_image(self, image):
        """
        Processes an image to detect multiple poses using MoveNet.
        Populates self.detected_poses with PoseData objects.

        Args:
            image (numpy.ndarray): The input image (BGR format from OpenCV).

        Returns:
            list: A list of PoseData objects if poses are detected, otherwise an empty list.
        """
        self.detected_poses = []
        if self.interpreter is None:
            print("MoveNet detector not initialized. Cannot process image.")
            return []

        self.image_height, self.image_width, _ = image.shape

        try:
            # Resize image to model input size
            resized_image = cv2.resize(image, (self.input_size, self.input_size))
            # Convert to RGB and add batch dimension, normalize to [0, 1]
            input_tensor = tf.convert_to_tensor(resized_image, dtype=tf.float32)
            input_tensor = tf.expand_dims(input_tensor, axis=0)
            input_tensor = tf.image.convert_image_dtype(input_tensor, dtype=tf.float32)

            # Run inference
            outputs = self.interpreter(input_tensor)
            # output_0 shape: (1, 6, 56) for MultiPose Lightning (6 people, 17 keypoints * 3 (y,x,conf) + 5 (bbox))
            # The output format can vary slightly, refer to MoveNet documentation for exact structure.
            keypoints_with_scores = outputs['output_0'].numpy()

            # Process detections
            for person_idx in range(keypoints_with_scores.shape[1]):
                person_data = keypoints_with_scores[0, person_idx, :]
                
                # Each person's data is typically [y1, x1, y2, x2, score, keypoint_y, keypoint_x, keypoint_score, ...]
                # Extract bounding box and overall score
                # Note: MoveNet's output format for bbox and score can be tricky.
                # This is a common interpretation for MultiPose:
                person_score = person_data[4] # Overall pose confidence
                
                # Keypoints start from index 5, and are (y, x, score) triplets
                keypoints_raw = person_data[5:].reshape(-1, 3) # (17, 3) for 17 keypoints
                
                landmarks = []
                for kp_id in range(self.num_landmarks_per_person):
                    y_norm, x_norm, conf = keypoints_raw[kp_id]
                    # Create a dummy object with x, y, z for compatibility
                    landmarks.append(type('obj', (object,), {'x': x_norm, 'y': y_norm, 'z': conf})())

                # Calculate bounding box from keypoints if not directly provided or reliable
                # MoveNet MultiPose output often has a bounding box at the start (y1, x1, y2, x2)
                y1_bbox_norm, x1_bbox_norm, y2_bbox_norm, x2_bbox_norm = person_data[0], person_data[1], person_data[2], person_data[3]
                bbox_norm = [x1_bbox_norm, y1_bbox_norm, x2_bbox_norm - x1_bbox_norm, y2_bbox_norm - y1_bbox_norm]

                # Filter by overall pose confidence
                if person_score > 0.2: # Adjust threshold as needed
                    self.detected_poses.append(PoseData(landmarks=landmarks, confidence=person_score, bbox=bbox_norm))
            
            return self.detected_poses
        except Exception as e:
            print(f"Error processing image with MoveNet: {e}")
            return []

    # The base class draw_landmarks should work for MoveNet's output format.
