"""
Image Analysis Module
Extracts atmospheric indicators from satellite images
for PM2.5 estimation without machine learning.

Author: PM2.5 Estimation System
"""

import cv2
import numpy as np
import os
from typing import Dict, Tuple


class ImageAnalyzer:
    """
    Analyzes satellite images to extract atmospheric features
    that correlate with PM2.5 pollution levels.
    """
    
    def __init__(self, image_path: str):
        """
        Initialize the analyzer with an image path.
        
        Args:
            image_path: Path to the satellite image
        """
        self.image_path = image_path
        self.image = None
        self.gray_image = None
        self.hsv_image = None
        
    def load_and_preprocess(self) -> bool:
        """
        Load image and prepare it for analysis.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read image
            self.image = cv2.imread(self.image_path)
            
            if self.image is None:
                raise ValueError("Failed to load image")
            
            # Resize to standard size for consistent processing
            self.image = cv2.resize(self.image, (800, 600))
            
            # Convert to grayscale
            self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            
            # Convert to HSV for saturation analysis
            self.hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
            
            return True
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def calculate_haze_score(self) -> float:
        """
        Calculate haze score based on image clarity.
        Higher haze = lower edge sharpness = higher PM2.5
        
        Returns:
            float: Haze score (0-100)
        """
        # Apply Laplacian edge detection
        laplacian = cv2.Laplacian(self.gray_image, cv2.CV_64F)
        edge_variance = laplacian.var()
        
        # Lower variance = more haze
        # Normalize to 0-100 scale (inverted)
        max_variance = 1000  # Typical max for clear images
        haze_score = max(0, 100 - (edge_variance / max_variance * 100))
        
        return min(100, haze_score)
    
    def calculate_brightness(self) -> float:
        """
        Calculate average brightness.
        Very high or very low brightness can indicate atmospheric conditions.
        
        Returns:
            float: Brightness score (0-255)
        """
        # Calculate mean brightness
        brightness = np.mean(self.gray_image)
        return float(brightness)
    
    def calculate_contrast(self) -> float:
        """
        Calculate image contrast.
        Low contrast often correlates with high pollution.
        
        Returns:
            float: Contrast score (0-100)
        """
        # Standard deviation represents contrast
        contrast_std = np.std(self.gray_image)
        
        # Normalize to 0-100 scale
        # Typical std range: 0-80
        contrast_score = (contrast_std / 80) * 100
        
        return min(100, contrast_score)
    
    def calculate_saturation(self) -> float:
        """
        Calculate average saturation.
        Lower saturation often indicates hazy, polluted conditions.
        
        Returns:
            float: Saturation score (0-255)
        """
        # Extract saturation channel from HSV
        saturation_channel = self.hsv_image[:, :, 1]
        avg_saturation = np.mean(saturation_channel)
        
        return float(avg_saturation)
    
    def calculate_atmospheric_turbidity(self) -> float:
        """
        Calculate atmospheric turbidity using dark channel prior concept.
        
        Returns:
            float: Turbidity score (0-100)
        """
        # Split into BGR channels
        b, g, r = cv2.split(self.image)
        
        # Dark channel: minimum of RGB channels
        dark_channel = cv2.min(cv2.min(r, g), b)
        
        # Higher dark channel values = more atmospheric scattering
        turbidity = np.mean(dark_channel)
        
        # Normalize to 0-100
        turbidity_score = (turbidity / 255) * 100
        
        return float(turbidity_score)
    
    def calculate_visibility_index(self) -> float:
        """
        Calculate visibility index based on histogram distribution.
        
        Returns:
            float: Visibility score (0-100, lower = worse visibility)
        """
        # Calculate histogram
        hist = cv2.calcHist([self.gray_image], [0], None, [256], [0, 256])
        
        # Normalize histogram
        hist_norm = hist.ravel() / hist.sum()
        
        # Calculate entropy (higher entropy = better visibility)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        
        # Normalize to 0-100 (max entropy ≈ 8 for 8-bit image)
        visibility_score = (entropy / 8) * 100
        
        return min(100, visibility_score)
    
    def analyze(self) -> Dict[str, float]:
        """
        Perform complete image analysis and extract all features.
        
        Returns:
            dict: Dictionary containing all atmospheric indicators
        """
        if not self.load_and_preprocess():
            raise ValueError("Failed to load and preprocess image")
        
        features = {
            'haze_score': self.calculate_haze_score(),
            'brightness': self.calculate_brightness(),
            'contrast': self.calculate_contrast(),
            'saturation': self.calculate_saturation(),
            'turbidity': self.calculate_atmospheric_turbidity(),
            'visibility': self.calculate_visibility_index()
        }
        
        return features

    def generate_preprocessing_pipeline(self, results_dir: str, output_prefix: str) -> Dict[str, str]:
        """
        Generate and save a full preprocessing pipeline for UI visualization.

        Steps:
        - Original image
        - Resize
        - Denoise
        - Normalization (Min-Max)
        - Contrast

        Args:
            results_dir: Directory where images are stored
            output_prefix: Prefix used in generated filenames

        Returns:
            dict: Relative filenames keyed by processing stage
        """
        if self.image is None:
            if not self.load_and_preprocess():
                raise ValueError("Failed to load image for preprocessing pipeline")

        os.makedirs(results_dir, exist_ok=True)

        # Re-load source for true "original" representation before preprocessing.
        original = cv2.imread(self.image_path)
        if original is None:
            raise ValueError("Failed to read original image for preprocessing pipeline")

        resized = cv2.resize(original, (800, 600), interpolation=cv2.INTER_LINEAR)
        denoised = cv2.GaussianBlur(resized, (5, 5), 0)

        normalized_float = cv2.normalize(denoised.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX)
        normalized = normalized_float.astype(np.uint8)

        lab = cv2.cvtColor(normalized, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_contrast = clahe.apply(l_channel)
        contrast_image = cv2.cvtColor(cv2.merge([l_contrast, a_channel, b_channel]), cv2.COLOR_LAB2BGR)

        stages = {
            'original': original,
            'resized': resized,
            'denoised': denoised,
            'normalized': normalized,
            'contrast': contrast_image,
        }

        saved_paths = {}
        for stage_name, stage_image in stages.items():
            filename = f"{output_prefix}_{stage_name}.png"
            output_path = os.path.join(results_dir, filename)
            cv2.imwrite(output_path, stage_image)
            saved_paths[stage_name] = filename

        return saved_paths

    def generate_kmeans_segmentation(self, results_dir: str, output_prefix: str) -> str:
        """Generate segmentation image using K-means clustering for any input image."""
        os.makedirs(results_dir, exist_ok=True)

        image = cv2.imread(self.image_path)
        if image is None:
            raise ValueError("Failed to load image for K-means segmentation")

        image = cv2.resize(image, (800, 600), interpolation=cv2.INTER_LINEAR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pixels = rgb_image.reshape((-1, 3)).astype(np.float32)

        # Fixed K ensures consistent segmentation behavior across uploaded inputs.
        k = 4
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 1.0)
        _compactness, labels, centers = cv2.kmeans(
            pixels,
            k,
            None,
            criteria,
            8,
            cv2.KMEANS_PP_CENTERS,
        )

        centers = np.uint8(centers)
        segmented_rgb = centers[labels.flatten()].reshape(rgb_image.shape)

        # Draw soft boundaries to make segmented structures more interpretable.
        gray_seg = cv2.cvtColor(segmented_rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray_seg, 70, 140)
        segmented_bgr = cv2.cvtColor(segmented_rgb, cv2.COLOR_RGB2BGR)
        segmented_bgr[edges > 0] = [30, 30, 30]

        filename = f"{output_prefix}_kmeans_segmented.png"
        output_path = os.path.join(results_dir, filename)
        cv2.imwrite(output_path, segmented_bgr)
        return filename
    
    def get_processed_image(self) -> np.ndarray:
        """
        Get the preprocessed image for visualization.
        
        Returns:
            np.ndarray: Processed image
        """
        return self.image


def analyze_image(image_path: str) -> Dict[str, float]:
    """
    Convenience function to analyze an image and return features.
    
    Args:
        image_path: Path to the satellite image
        
    Returns:
        dict: Atmospheric features extracted from the image
    """
    analyzer = ImageAnalyzer(image_path)
    return analyzer.analyze()
