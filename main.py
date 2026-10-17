"""
Technical Project - Automated Curve Extraction from Scanned Scientific Plots
Authors: Haitam Safouane Ourtane, student at EMSE

Processing Pipeline:
1. OCR detection and robust axis calibration (linear RANSAC).
2. Legend extraction via morphological and colorimetric analysis.
3. Curve segmentation:
   - Colored traces via unsupervised clustering (MeanShift on cyclic HSV).
   - Black/dark traces via subtractive morphology (filtering axes/grids/text).
4. Decoupling continuous model lines and discrete experimental markers.
5. Sampling f(x) = y and exporting calibrated data to Excel & verification charts.
"""

import argparse
import glob
import os
import re
import time
import warnings
from typing import Dict, List, Optional, Tuple

import cv2
import matplotlib
matplotlib.use("Agg")  # Headless mode for rendering without a display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import maximum_filter
from scipy.signal import medfilt, savgol_filter
from sklearn.cluster import KMeans, MeanShift

warnings.filterwarnings("ignore", category=UserWarning)

# ------------------------------------------------------------------------------
# Global Parameters and Experimental Thresholds
# ------------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_DIR = os.path.join(BASE_DIR, "images")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "data")

# OCR scaling parameters
# A 1.5x scale factor capped at 1024px offers the optimal trade-off
# between small character legibility and CPU inference speed.
OCR_SCALE_FACTOR = 1.5
OCR_MAX_DIMENSION = 1024

# Component detection thresholds (in pixels)
MIN_COLORED_PIXELS = 500   # Eliminates chromatic noise and JPEG compression artifacts
MIN_CLUSTER_PIXELS = 100   # Minimum cluster size to validate a colored curve
MIN_BLACK_PIXELS = 200     # Validation threshold for a dark/black trace
LEGEND_MAX_COLOR_DIST = 70 # Maximum Euclidean RGB distance patch <-> curve

# Robust regex for numeric tick marks: accepts integers, decimals, negatives,
# and numbers without leading zeros (e.g. .1, -.5, 0.42, 10)
NUMBER_REGEX = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)$")

_ocr_instance = None
_KNOWN_COLORS = {
    "Black": (0, 0, 0),
    "Gray": (128, 128, 128),
    "White": (255, 255, 255),
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Yellow": (255, 255, 0),
    "Cyan": (0, 255, 255),
    "Magenta": (255, 0, 255),
    "Orange": (255, 128, 0),
    "Pink": (255, 192, 203),
    "Brown": (139, 69, 19)
}


def get_closest_color_name(rgb: np.ndarray) -> str:
    """
    Determines the common name of a color in HSV/colorimetric space.
    Ensures reliable discrimination between Red, Orange, Yellow, Blue, etc.
    """
    r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c

    # Grayscale / achromatic
    if max_c < 45:
        return "Black"
    if max_c > 225 and delta < 20:
        return "White"
    if delta < 25:
        return "Gray"

    # Compute Hue in degrees [0, 360[
    if delta == 0:
        hue = 0.0
    elif max_c == r:
        hue = 60.0 * (((g - b) / delta) % 6)
    elif max_c == g:
        hue = 60.0 * (((b - r) / delta) + 2)
    else:
        hue = 60.0 * (((r - g) / delta) + 4)

    # Sectoral classification
    if hue >= 345 or hue < 15:
        return "Red"
    elif 15 <= hue < 45:
        return "Orange"
    elif 45 <= hue < 75:
        return "Yellow"
    elif 75 <= hue < 165:
        return "Green"
    elif 165 <= hue < 195:
        return "Cyan"
    elif 195 <= hue < 265:
        return "Blue"
    elif 265 <= hue < 315:
        return "Magenta"
    elif 315 <= hue < 345:
        return "Pink"

    return "Unknown"


def get_ocr_engine():
    """Initializes EasyOCR reader once (cached instance)."""
    global _ocr_instance
    if _ocr_instance is None:
        import easyocr
        print("Loading EasyOCR model...")
        _ocr_instance = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _ocr_instance


def parse_tick_value(text: str) -> Optional[float]:
    """
    Cleans and parses an OCR string into a numeric float value.
    Handles commas, unicode minus signs, and attached tick marks.
    """
    cleaned = text.replace(",", ".").replace("\u2212", "-").replace(" ", "")
    cleaned = cleaned.rstrip("-\u2013\u2014_|")  # Remove trailing tick mark artifacts
    
    if NUMBER_REGEX.match(cleaned):
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def extract_text_boxes(image: np.ndarray, binarize: bool = False) -> List[dict]:
    """
    Runs optical character recognition on the scaled image.
    Returns bounding boxes and parsed values mapped back to original image space.
    """
    height, width = image.shape[:2]
    max_dim = max(height, width)
    # Ensure optimal sizing for numeric OCR (~950px target for small images)
    if max_dim < 850:
        scale = max(1.8, min(3.2, 950.0 / max_dim))
    else:
        scale = min(OCR_SCALE_FACTOR, OCR_MAX_DIMENSION / max_dim)
        scale = max(1.0, scale)
    
    resized = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    if binarize:
        _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    results = []
    ocr_detections = get_ocr_engine().readtext(gray)
    
    for bbox, raw_text, _ in ocr_detections:
        pts = np.asarray(bbox, dtype=np.float32) / scale
        x_min, y_min = pts.min(axis=0)
        x_max, y_max = pts.max(axis=0)
        
        results.append({
            "text": raw_text,
            "box": (float(x_min), float(y_min), float(x_max), float(y_max)),
            "cx": float((x_min + x_max) / 2.0),
            "cy": float((y_min + y_max) / 2.0),
            "value": parse_tick_value(raw_text),
        })
    return results


def group_ticks_by_axis(numbers: List[dict], coord_key: str, tolerance: float) -> List[List[dict]]:
    """
    Groups tick marks aligned along an axis (constant X or constant Y coordinate).
    """
    groups: List[List[dict]] = []
    for item in sorted(numbers, key=lambda n: n[coord_key]):
        matched = False
        for group in groups:
            if abs(group[0][coord_key] - item[coord_key]) < tolerance:
                group.append(item)
                matched = True
                break
        if not matched:
            groups.append([item])
    return groups


def verify_regular_spacing(positions: np.ndarray, values: np.ndarray, tolerance: float = 0.06) -> bool:
    """Verifies that 3 points form regularly spaced tick marks."""
    order = np.argsort(positions)
    d_pos = np.diff(positions[order])
    d_val = np.diff(values[order])
    return (abs(d_pos[0] - d_pos[1]) <= tolerance * d_pos.max() and
            abs(d_val[0] - d_val[1]) <= tolerance * np.abs(d_val).max())


def fit_axis_ransac(points: List[dict], coord_key: str) -> Tuple[Optional[Tuple[float, float, float, float]], int]:
    """
    Robust linear fitting by consensus (RANSAC).
    Eliminates outlier tick marks read by OCR.
    """
    if len(points) < 2:
        return None, 0

    pixel_pos = np.array([p[coord_key] for p in points], dtype=float)
    real_vals = np.array([p["value"] for p in points], dtype=float)
    value_span = real_vals.max() - real_vals.min()

    if value_span == 0:
        return None, 0

    tolerance = 0.04 * value_span
    best_consensus_score = None
    best_inliers_mask = None

    # Exhaustive search over all possible pairs
    for i in range(len(pixel_pos)):
        for j in range(i + 1, len(pixel_pos)):
            delta_px = pixel_pos[j] - pixel_pos[i]
            if abs(delta_px) < 5 or real_vals[i] == real_vals[j]:
                continue

            slope = (real_vals[j] - real_vals[i]) / delta_px
            intercept = real_vals[i] - slope * pixel_pos[i]

            inliers = np.abs(slope * pixel_pos + intercept - real_vals) <= tolerance
            score = (int(inliers.sum()), float(np.ptp(pixel_pos[inliers])))

            if best_consensus_score is None or score > best_consensus_score:
                best_consensus_score = score
                best_inliers_mask = inliers

    if best_inliers_mask is None:
        return None, 0

    nb_inliers = int(best_inliers_mask.sum())
    # Safety condition: minimum 3 aligned points with regular spacing
    if nb_inliers < 3 or (nb_inliers == 3 and not verify_regular_spacing(pixel_pos[best_inliers_mask], real_vals[best_inliers_mask])):
        return None, 0

    # Final least-squares regression over validated inliers
    slope, intercept = np.polyfit(pixel_pos[best_inliers_mask], real_vals[best_inliers_mask], 1)
    px_min, px_max = pixel_pos[best_inliers_mask].min(), pixel_pos[best_inliers_mask].max()
    
    return (px_min, slope * px_min + intercept, px_max, slope * px_max + intercept), nb_inliers


def calibrate_single_axis(numbers: List[dict], align_coord: str, tolerance: float):
    """Selects the best tick alignment for a given axis."""
    best_calibration, max_inliers, max_span = None, 0, 0.0
    tick_coord = "cx" if align_coord == "cy" else "cy"

    for group in group_ticks_by_axis(numbers, align_coord, tolerance):
        calibration, count = fit_axis_ransac(group, tick_coord)
        if calibration is None:
            continue
        span = abs(calibration[2] - calibration[0])
        if (count, span) > (max_inliers, max_span):
            best_calibration, max_inliers, max_span = calibration, count, span

    return best_calibration, max_inliers


def calibrate_axes(image: np.ndarray):
    """
    Locates tick marks and calibrates the mapping from pixels to physical units.
    Executes a fallback pass with binarization if initial detection is partial.
    """
    h, w = image.shape[:2]
    align_tolerance = max(10, 0.02 * max(h, w))

    ocr_items = extract_text_boxes(image, binarize=False)
    numeric_items = [item for item in ocr_items if item["value"] is not None]

    x_scale, nb_x = calibrate_single_axis(numeric_items, "cy", align_tolerance)
    y_scale, nb_y = calibrate_single_axis(numeric_items, "cx", align_tolerance)

    # Fallback pass with Otsu/threshold binarization if axis calibration is incomplete
    if nb_x < 3 or nb_y < 3:
        print("  [OCR] Partial axis detection -> fallback pass with binarization...")
        fallback_items = extract_text_boxes(image, binarize=True)
        for item in fallback_items:
            if item["value"] is not None:
                # Add item if not already detected
                if all(abs(item["cx"] - existing["cx"]) > 8 or abs(item["cy"] - existing["cy"]) > 8 for existing in numeric_items):
                    numeric_items.append(item)
                    ocr_items.append(item)

        x_alt, nb_x_alt = calibrate_single_axis(numeric_items, "cy", align_tolerance)
        y_alt, nb_y_alt = calibrate_single_axis(numeric_items, "cx", align_tolerance)

        if nb_x_alt >= nb_x:
            x_scale, nb_x = x_alt, nb_x_alt
        if nb_y_alt >= nb_y:
            y_scale, nb_y = y_alt, nb_y_alt

    print(f"  [OCR] Retained tick marks: {sorted(item['value'] for item in numeric_items)}")
    print(f"  [OCR] Consistent points -> X Axis: {nb_x}, Y Axis: {nb_y}")
    return x_scale, y_scale, ocr_items


def find_legend_color_patch(patch_bgr: np.ndarray, patch_hsv: np.ndarray, text_height: int) -> Optional[np.ndarray]:
    """
    Identifies a representative color patch or line segment for a legend item.
    Verifies compactness and aspect ratio to discard residual text characters.
    """
    mask = ((patch_hsv[:, :, 1] > 50) | (patch_hsv[:, :, 2] < 160)).astype(np.uint8)
    nb_components, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    best_area, target_id = 0, None
    for idx in range(1, nb_components):
        width = int(stats[idx, cv2.CC_STAT_WIDTH])
        height = int(stats[idx, cv2.CC_STAT_HEIGHT])
        area = int(stats[idx, cv2.CC_STAT_AREA])

        fill_ratio = area / float(width * height)
        is_patch = fill_ratio >= 0.6 and width >= 0.4 * text_height and height >= 0.4 * text_height
        is_line_marker = height <= 0.4 * text_height and width >= 1.0 * text_height

        if (is_patch or is_line_marker) and area > best_area:
            best_area, target_id = area, idx

    if target_id is None:
        return None

    median_bgr = np.median(patch_bgr[labels == target_id], axis=0)
    return median_bgr[::-1]  # Convert BGR -> RGB


def extract_curve_legends(image: np.ndarray, text_boxes: List[dict]) -> List[dict]:
    """Associates each text label with the color patch located directly to its left."""
    h, _ = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    detected_legends = []

    for box in text_boxes:
        label = box["text"].strip()
        if box["value"] is not None or len(label) < 2:
            continue

        x0, y0, _, y1 = box["box"]
        th = max(1, int(y1 - y0))
        roi_x0, roi_x1 = max(0, int(x0 - 3 * th - 4)), max(0, int(x0 - 2))
        roi_y0, roi_y1 = max(0, int(y0)), min(h, int(y1))

        if (roi_x1 - roi_x0 < 3) or (roi_y1 - roi_y0 < 3):
            continue

        color_rgb = find_legend_color_patch(image[roi_y0:roi_y1, roi_x0:roi_x1], hsv[roi_y0:roi_y1, roi_x0:roi_x1], th)
        if color_rgb is not None:
            detected_legends.append({"text": label, "color_rgb": color_rgb})
            print(f"  [Legend] '{label}' -> RGB {color_rgb.astype(int).tolist()}")

    return detected_legends


def match_curves_with_legends(curve_colors: List[np.ndarray], legends: List[dict]) -> Dict[int, str]:
    """Greedy bipartite matching between extracted curves and legends based on color proximity."""
    candidates = []
    for c_idx, color in enumerate(curve_colors):
        for l_idx, leg in enumerate(legends):
            dist = float(np.linalg.norm(np.asarray(color, float) - leg["color_rgb"]))
            if dist <= LEGEND_MAX_COLOR_DIST:
                candidates.append((dist, c_idx, l_idx))

    matched_names: Dict[int, str] = {}
    assigned_curves, assigned_legends = set(), set()
    for _, c_idx, l_idx in sorted(candidates):
        if c_idx not in assigned_curves and l_idx not in assigned_legends:
            matched_names[c_idx] = legends[l_idx]["text"]
            assigned_curves.add(c_idx)
            assigned_legends.add(l_idx)

    return matched_names


def extract_dark_curves(image: np.ndarray, text_boxes: List[tuple], colored_mask: Optional[np.ndarray] = None, y_max_limit: Optional[int] = None) -> np.ndarray:
    """
    Extracts black/dark traces using subtractive morphological filtering.
    Removes text, grid lines, axes, and anti-aliasing artifacts from colored curves.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # 1. Mask text regions
    for x0, y0, x1, y1 in text_boxes:
        cv2.rectangle(binary, (int(x0) - 5, int(y0) - 5), (int(x1) + 5, int(y1) + 5), 0, -1)

    # 2. Eliminate straight orthogonal lines (axes and grid)
    horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
    vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
    grid_mask = cv2.dilate(cv2.add(horiz_lines, vert_lines), np.ones((3, 3), np.uint8), iterations=1)
    cleaned = cv2.subtract(binary, grid_mask)

    # 3. Eliminate anti-aliasing artifacts from colored curves
    if colored_mask is not None:
        dilated_colors = cv2.dilate(colored_mask.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=1)
        cleaned = cv2.subtract(cleaned, dilated_colors)

    # 4. Preserve continuous traces AND experimental markers (connected or disconnected)
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    result_canvas = np.zeros_like(cleaned)
    h_img, w_img = cleaned.shape[:2]
    max_y = y_max_limit if y_max_limit is not None else (h_img - 15)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        _, _, w, h = cv2.boundingRect(cnt)
        m = cv2.moments(cnt)
        cx = m['m10'] / max(1e-5, m['m00'])
        cy = m['m01'] / max(1e-5, m['m00'])

        # Only retain elements inside the active plotting area (outside axis borders)
        if 42 <= cx <= w_img - 15 and 30 <= cy <= max_y:
            # Continuous model curve segment
            if w > 20 or h > 20:
                cv2.drawContours(result_canvas, [cnt], -1, 255, -1)
            # Disconnected experimental marker (isolated dot / tick)
            elif 2 <= area <= 70 and w <= 16 and h <= 16:
                cv2.drawContours(result_canvas, [cnt], -1, 255, -1)

    return np.column_stack(np.where(result_canvas > 0))  # Format (y, x)


def segment_image_curves(image: np.ndarray, text_boxes: List[tuple], forced_clusters: str = "AUTO", y_max_limit: Optional[int] = None) -> List[dict]:
    """
    Separates individual curves in the plot:
    - Chromatic detection via MeanShift or KMeans
    - Achromatic detection via mathematical morphology
    """
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_mask = (hsv[:, :, 1] > 50) & (hsv[:, :, 2] > 50)
    detected_curves = []

    if int(color_mask.sum()) >= MIN_COLORED_PIXELS:
        pixel_coords = np.column_stack(np.where(color_mask))
        pixel_rgb = rgb[color_mask]

        if str(forced_clusters).strip().upper() == "AUTO":
            # Circular representation of hue to avoid discontinuity at 180 deg
            hue_angle = hsv[:, :, 0][color_mask] * (np.pi / 90.0)
            features = np.column_stack((np.cos(hue_angle) * 100, np.sin(hue_angle) * 100))
            
            # Representative subsampling to speed up MeanShift convergence
            rng = np.random.default_rng(0)
            sample_indices = rng.choice(len(features), min(1000, len(features)), replace=False)
            
            ms_model = MeanShift(bandwidth=30, bin_seeding=True)
            labels = ms_model.fit(features[sample_indices]).predict(features)
        else:
            k = int(forced_clusters)
            labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(pixel_rgb)

        for cluster_id in np.unique(labels):
            subset = labels == cluster_id
            if subset.sum() >= MIN_CLUSTER_PIXELS:
                detected_curves.append({
                    "coords": pixel_coords[subset],
                    "color": pixel_rgb[subset].mean(axis=0),
                })

    dark_pixels = extract_dark_curves(image, text_boxes, color_mask, y_max_limit=y_max_limit)
    if len(dark_pixels) >= MIN_BLACK_PIXELS:
        print(f"  -> Black/gray trace detected ({len(dark_pixels)} pixels)")
        detected_curves.append({"coords": dark_pixels, "color": np.zeros(3)})

    return detected_curves


def sample_curve_and_markers(coords: np.ndarray, img_shape: Tuple[int, int], image: Optional[np.ndarray] = None) -> Tuple[Optional[Tuple[np.ndarray, np.ndarray]], Optional[Tuple[np.ndarray, np.ndarray]]]:
    """
    Analyzes a trace to extract in a decoupled manner:
    1. Continuous curve profile (theoretical model / fitting).
    2. Discrete coordinates of experimental markers (ticks / dots).
    
    Returns (line_data, points_data):
    - line_data: (x_line, y_line) or None if pure scatter plot
    - points_data: (x_points, y_points) or None if pure continuous line without markers
    """
    ys, xs = coords[:, 0], coords[:, 1]
    min_x, max_x = xs.min(), xs.max()
    span_x = max_x - min_x

    # Binary mask
    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    mask[ys, xs] = 255

    # 1. Verification of pure scatter plot (isolated elements from the start)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    valid_comps = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 5]

    is_pure_scatter = False
    if valid_comps and span_x > 0:
        max_w = max(stats[i, cv2.CC_STAT_WIDTH] for i in valid_comps)
        max_area = max(stats[i, cv2.CC_STAT_AREA] for i in valid_comps)
        total_area = sum(stats[i, cv2.CC_STAT_AREA] for i in valid_comps)
        is_pure_scatter = (len(valid_comps) >= 4) and (max_w < 50) and (max_w < 0.25 * span_x) and (max_area / total_area < 0.35)

    if is_pure_scatter:
        areas = [stats[i, cv2.CC_STAT_AREA] for i in valid_comps]
        med_area = float(np.median(areas))
        filtered = [i for i in valid_comps if stats[i, cv2.CC_STAT_AREA] >= max(5, 0.2 * med_area)]
        pts = sorted([centroids[i] for i in filtered], key=lambda p: p[0])
        return None, (np.array([p[0] for p in pts], dtype=float), np.array([p[1] for p in pts], dtype=float))

    # 2. Trace contains a continuous line: separate continuous branches from disconnected markers
    line_mask = np.zeros_like(mask)
    disconnected_markers = []
    marker_template_indices = []

    for i in range(1, num_labels):
        w_i, h_i, a_i = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT], stats[i, cv2.CC_STAT_AREA]
        if w_i > 20 or h_i > 20:
            line_mask[labels == i] = 255
        elif 2 <= a_i <= 70 and w_i <= 16 and h_i <= 16:
            disconnected_markers.append(centroids[i])
            if 3 <= w_i <= 10 and 3 <= h_i <= 10 and 0.7 <= (w_i / h_i) <= 1.4 and 4 <= a_i <= 35:
                marker_template_indices.append(i)

    if np.sum(line_mask > 0) == 0:
        line_mask = mask.copy()

    on_line_markers = []

    # 3. Detection of markers along the continuous trace
    # Strategy A: Guided template matching if compact disconnected markers exist
    if image is not None and len(marker_template_indices) >= 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        tmpl_idx = marker_template_indices[1]
        cx, cy = int(round(centroids[tmpl_idx][0])), int(round(centroids[tmpl_idx][1]))
        r = 3
        if cy - r >= 0 and cy + r + 1 <= gray.shape[0] and cx - r >= 0 and cx + r + 1 <= gray.shape[1]:
            template = gray[cy - r : cy + r + 1, cx - r : cx + r + 1]
            th, tw = template.shape
            res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            dil = cv2.dilate(line_mask, np.ones((7, 7), np.uint8))
            roi = dil[th // 2 : th // 2 + res.shape[0], tw // 2 : tw // 2 + res.shape[1]]
            res_roi = np.where(roi > 0, res, 0)
            peaks = (res_roi == maximum_filter(res_roi, size=6)) & (res_roi > 0.35)
            py, px = np.where(peaks)
            for x, y in zip(px + tw / 2.0, py + th / 2.0):
                on_line_markers.append(np.array([x, y]))

    # Strategy B: Adaptive morphological erosion
    if not on_line_markers:
        dist = cv2.distanceTransform(line_mask, cv2.DIST_L2, 5)
        non_zero = dist[dist > 0]
        if len(non_zero) > 0:
            med_dist = np.median(non_zero)
            k_radius = int(np.floor(med_dist * 2.0))
            k_radius = max(3, min(k_radius, 7))
            if k_radius % 2 == 0:
                k_radius += 1

            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_radius, k_radius))
            er = cv2.erode(line_mask, k)
            num_e, _, stats_e, cents_e = cv2.connectedComponentsWithStats(er, connectivity=8)
            valid_e = [i for i in range(1, num_e) if stats_e[i, cv2.CC_STAT_AREA] >= 3]

            widths = [stats_e[i, cv2.CC_STAT_WIDTH] for i in valid_e]
            small_dots = [w for w in widths if w <= 15]

            has_markers = len(small_dots) >= 4 and (len(small_dots) / len(valid_e) >= 0.5 if len(valid_e) else False)
            if has_markers:
                on_line_markers = [cents_e[i] for i in valid_e if stats_e[i, cv2.CC_STAT_WIDTH] <= 15]

    # 4. Merge detected experimental markers
    all_markers = disconnected_markers + on_line_markers
    cleaned_markers = []
    if len(all_markers) >= 4:
        all_markers.sort(key=lambda p: p[0])
        min_dist = 4.5 if len(disconnected_markers) >= 3 else 3.0
        for p in all_markers:
            if not cleaned_markers or np.hypot(p[0] - cleaned_markers[-1][0], p[1] - cleaned_markers[-1][1]) >= min_dist:
                cleaned_markers.append(p)

    has_markers = len(cleaned_markers) >= 4
    points_data = None
    if has_markers:
        pts_x = np.array([p[0] for p in cleaned_markers], dtype=float)
        pts_y = np.array([p[1] for p in cleaned_markers], dtype=float)
        points_data = (pts_x, pts_y)

    # 5. Clean extraction of continuous curve (subtracting markers + smoothing)
    line_canvas = line_mask.copy()
    if has_markers:
        for mx, my in cleaned_markers:
            cv2.circle(line_canvas, (int(round(mx)), int(round(my))), 2, 0, -1)

    ys_l, xs_l = np.where(line_canvas > 0)
    if len(xs_l) < 20:
        ys_l, xs_l = np.where(line_mask > 0)

    unique_x, inv = np.unique(xs_l, return_inverse=True)
    raw_lx = unique_x.astype(float)
    raw_ly = np.bincount(inv, weights=ys_l) / np.bincount(inv)

    if has_markers and len(raw_lx) >= 15:
        all_x = np.arange(int(raw_lx.min()), int(raw_lx.max()) + 1, dtype=float)
        interp_y = np.interp(all_x, raw_lx, raw_ly)
        w_len = min(17, max(5, int(len(all_x) // 5) * 2 + 1))
        smooth_y = savgol_filter(medfilt(interp_y, min(5, w_len)), w_len, 2)
        smooth_y = np.clip(smooth_y, np.min(raw_ly), np.max(raw_ly))
        smooth_y[0] = interp_y[0]
        smooth_y[1] = 0.5 * (smooth_y[1] + interp_y[1])
        smooth_y[-1] = interp_y[-1]
        smooth_y[-2] = 0.5 * (smooth_y[-2] + interp_y[-2])
        line_data = (all_x, smooth_y)
    else:
        line_data = (raw_lx, raw_ly)

    return line_data, points_data


def project_to_axis_units(pixel_values: np.ndarray, scale_spec: Tuple[float, float, float, float]) -> np.ndarray:
    """Applies affine transformation from pixel coordinates to calibrated physical units."""
    p1, v1, p2, v2 = scale_spec
    return v1 + (pixel_values - p1) * (v2 - v1) / (p2 - p1)


def generate_unique_curve_name(base_name: str, used_names: set) -> str:
    """Generates a unique identifier avoiding legend naming collisions."""
    candidate, count = base_name, 2
    while candidate in used_names:
        candidate = f"{base_name}_{count}"
        count += 1
    return candidate


def export_verification_chart(original_img: np.ndarray, curves: List[dict], output_path: str, is_calibrated: bool):
    """Generates a side-by-side comparison figure (original image vs extracted data)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.imshow(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB))
    ax1.set_title("Original Image")
    ax1.axis("off")

    for curve in curves:
        color_hex = curve["hex"]
        name = curve["name"]
        
        # 1. Plot continuous line (if present)
        if "line_x" in curve:
            label_line = f"{name} (Line)" if "points_x" in curve else name
            ax2.plot(curve["line_x"], curve["line_y"], label=label_line, color=color_hex, linewidth=2)
            
        # 2. Plot experimental points (if present)
        if "points_x" in curve:
            label_pts = f"{name} (Points)" if "line_x" in curve else name
            is_dark = color_hex.lower() in ("#000000", "#0", "black")
            face = "white" if (is_dark and "line_x" in curve) else color_hex
            ew = 1.0 if face == "white" else 0.6
            ax2.scatter(curve["points_x"], curve["points_y"], label=label_pts, facecolors=face, edgecolors='black', linewidths=ew, s=30, zorder=5)

    status_title = "Extracted Data" if is_calibrated else "Extracted Data (in pixels - uncalibrated axes)"
    ax2.set_title(status_title)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    for attempt in range(5):
        try:
            plt.savefig(output_path, dpi=150)
            break
        except Exception:
            time.sleep(0.3)
    plt.close(fig)


def process_chart_image(image_path: str, output_directory: str) -> bool:
    """Processes a chart image and generates the calibrated Excel spreadsheet and control plot."""
    start_time = time.perf_counter()
    file_name = os.path.basename(image_path)
    print(f"\nProcessing: {file_name}")

    img = cv2.imread(image_path)
    if img is None:
        print("  -> Error: unable to open image file.")
        return False

    height, width = img.shape[:2]
    x_scale, y_scale, ocr_items = calibrate_axes(img)

    raw_y_scale = y_scale
    y_max_limit = int(max(raw_y_scale[0], raw_y_scale[2]) + 6) if raw_y_scale is not None else None

    fallback_axes = []
    if x_scale is None:
        x_scale = (0.0, 0.0, float(width), float(width))
        fallback_axes.append("X")
    if y_scale is None:
        y_scale = (float(height), 0.0, 0.0, float(height))
        fallback_axes.append("Y")

    is_calibrated = len(fallback_axes) == 0
    if not is_calibrated:
        print(f"  -> Unresolved axes ({'+'.join(fallback_axes)}): automatic fallback to pixel coordinates.")

    print(f"  -> X Calibration: [{x_scale[1]:.3g} ; {x_scale[3]:.3g}] | Y Calibration: [{y_scale[1]:.3g} ; {y_scale[3]:.3g}]")

    legends = extract_curve_legends(img, ocr_items)
    curves = segment_image_curves(img, [item["box"] for item in ocr_items], y_max_limit=y_max_limit)

    if not curves:
        print("  -> Error: no curve signal detected.")
        return False

    legend_map = match_curves_with_legends([c["color"] for c in curves], legends)
    registered_names = set()

    # Detect title if single curve present
    chart_title = None
    if len(curves) == 1:
        text_only = [item for item in ocr_items if item["value"] is None and len(item["text"].strip()) > 3]
        if text_only:
            top_text = sorted(text_only, key=lambda x: x["cy"])[0]["text"]
            chart_title = re.sub(r'[^A-Za-z0-9_]+', '_', top_text).strip('_')
            if len(chart_title) < 3:
                chart_title = None

    data_columns = {}
    for idx, curve in enumerate(curves):
        line_data, points_data = sample_curve_and_markers(curve["coords"], img.shape, img)
        curve["hex"] = "#{:02x}{:02x}{:02x}".format(*(int(c) for c in curve["color"]))

        # 1. Official legend label or fallback strategy
        default_label = legend_map.get(idx)
        if default_label is None:
            if len(curves) == 1 and chart_title:
                default_label = chart_title
            else:
                color_name = get_closest_color_name(curve["color"])
                default_label = f"Curve_{color_name}"

        curve["name"] = generate_unique_curve_name(default_label, registered_names)
        registered_names.add(curve["name"])

        # 2. Calibration and storage of coordinates
        has_line = line_data is not None
        has_points = points_data is not None

        if has_line and has_points:
            curve["line_x"] = project_to_axis_units(line_data[0], x_scale)
            curve["line_y"] = project_to_axis_units(line_data[1], y_scale)
            curve["points_x"] = project_to_axis_units(points_data[0], x_scale)
            curve["points_y"] = project_to_axis_units(points_data[1], y_scale)
            
            data_columns[f"{curve['name']}_Line_X"] = curve["line_x"]
            data_columns[f"{curve['name']}_Line_Y"] = curve["line_y"]
            data_columns[f"{curve['name']}_Points_X"] = curve["points_x"]
            data_columns[f"{curve['name']}_Points_Y"] = curve["points_y"]
            print(f"  -> {curve['name']} : Model ({len(curve['line_x'])} pts) + Experimental measurements ({len(curve['points_x'])} points)")

        elif has_points and not has_line:
            curve["points_x"] = project_to_axis_units(points_data[0], x_scale)
            curve["points_y"] = project_to_axis_units(points_data[1], y_scale)
            
            data_columns[f"{curve['name']}_X"] = curve["points_x"]
            data_columns[f"{curve['name']}_Y"] = curve["points_y"]
            print(f"  -> {curve['name']} : Experimental scatter plot ({len(curve['points_x'])} points)")

        else:
            curve["line_x"] = project_to_axis_units(line_data[0], x_scale)
            curve["line_y"] = project_to_axis_units(line_data[1], y_scale)
            
            data_columns[f"{curve['name']}_X"] = curve["line_x"]
            data_columns[f"{curve['name']}_Y"] = curve["line_y"]
            print(f"  -> {curve['name']} : Continuous curve ({len(curve['line_x'])} pts)")

    # Tabular export to Excel
    base_name = os.path.splitext(file_name)[0]
    excel_path = os.path.join(output_directory, f"{base_name}_data.xlsx")
    plot_path = os.path.join(output_directory, f"{base_name}_verification.png")

    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data_columns.items()]))
    df.to_excel(excel_path, index=False)
    export_verification_chart(img, curves, plot_path, is_calibrated)

    elapsed = time.perf_counter() - start_time
    print(f"  -> Success: {len(curves)} curve(s) processed in {elapsed:.1f}s")
    return True


def main():
    parser = argparse.ArgumentParser(description="Automated extraction of experimental curves.")
    parser.add_argument("--input", default=DEFAULT_INPUT_DIR, help="Directory containing images to process.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory to save output results.")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.input, exist_ok=True)

    supported_extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp")
    files_to_process = []
    for ext in supported_extensions:
        files_to_process.extend(glob.glob(os.path.join(args.input, ext)))

    if not files_to_process:
        print(f"No image found in '{args.input}'.")
        return

    print("==========================================================")
    print("AUTOMATED EXPERIMENTAL CURVE EXTRACTION PIPELINE")
    print(f"Images detected: {len(files_to_process)}")
    print("==========================================================")

    success_count = 0
    for image_path in sorted(files_to_process):
        try:
            if process_chart_image(image_path, args.output):
                success_count += 1
        except Exception as err:
            print(f"  -> Failed on {os.path.basename(image_path)}: {err}")

    print(f"\nProcessing complete: {success_count}/{len(files_to_process)} files processed successfully.")


if __name__ == "__main__":
    main()
