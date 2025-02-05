import cv2
import numpy as np
from typing import Tuple


class CrosswalkDetector:
    def __init__(self, yolo_detector, param):
        self._yolo_detector = yolo_detector
        self._param = param
        self._cumulative_crosswalk_img = None # Stores cumulative crosswalk detection

    def reset_buffer(self):
        self._cumulative_crosswalk_img = None

    def _apply_count_threshold_crosswalk(self) -> np.ndarray:
        # Applies a threshold to the cumulative image using count_threshold_crosswalk.

        if self._cumulative_crosswalk_img is None:
            raise ValueError("Cumulative image has not been initialized.")

        # Returns binary mask where True (1) indicates pixels exceeding the threshold
        thresholded_img = (self._cumulative_crosswalk_img >= self._param.count_th_crosswalk).astype(np.uint8)

        return thresholded_img

    def _cumulative_crosswalk(self, input_cvimg: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        # Cumulatively detects crosswalks by analyzing each frame's crosswalk mask.

        if  self._cumulative_crosswalk_img is None:
            # Initialize the cumulative image dimensions based on the input image size
            height, width = input_cvimg.shape[:2]
            self._cumulative_crosswalk_img = np.zeros((height, width), dtype=np.uint8)

        # YOLO detection for crosswalks; returns a mask with detected crosswalk regions
        crosswalk_img, vehicle_img = self._yolo_detector._crosswalk_and_vehicle_yolo(input_cvimg)

        if crosswalk_img is not None:
            # Accumulate crosswalk detections pixel-wise
            self._cumulative_crosswalk_img += crosswalk_img

        # Apply threshold to identify stable crosswalk areas
        try:
            thresholded_img = self._apply_count_threshold_crosswalk()
        except ValueError as e:
            height, width = input_cvimg.shape[:2:]
            thresholded_img = np.ones((height, width), dtype=np.uint8)

        return thresholded_img, vehicle_img

    def _check_overlap_with_crosswalk(self, vehicle_img: np.ndarray, thresholded_img: np.ndarray) -> bool:
        # Checks for overlapping pixels between detected crosswalk areas and vehicles.

        # Detect overlap between vehicles and crosswalk areas
        overlap = cv2.bitwise_and(vehicle_img, thresholded_img)

        # Returns False if no overlap, otherwise True
        if np.any(overlap):
            return True
        else:
            return False
