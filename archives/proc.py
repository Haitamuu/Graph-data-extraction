import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pytesseract
import re
import sys
import logging
from collections import Counter

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

pytesseract.pytesseract.tesseract_cmd = resource_path('tesseract.exe')

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_all_image_files(folder_path):
    """Return a list of image files from the provided folder."""
    supported_extensions = ('.bmp', '.png', '.jpg', '.jpeg')
    return [file_name for file_name in os.listdir(folder_path) if file_name.lower().endswith(supported_extensions)]


def read_and_crop_main_region(image_path):
    """Read the image, detect the largest contour, and crop it."""
    image_original = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image_original, cv2.COLOR_BGR2RGB)
    image_grayscale = cv2.cvtColor(image_original, cv2.COLOR_BGR2GRAY)

    _, image_thresholded = cv2.threshold(
        image_grayscale, 50, 255, cv2.THRESH_BINARY_INV)
    contours_detected, _ = cv2.findContours(
        image_thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours_detected:
        return None

    largest_contour = max(contours_detected, key=cv2.contourArea)
    x_coord, y_coord, width, height = cv2.boundingRect(largest_contour)
    image_cropped = image_rgb[y_coord:y_coord +
                              height, x_coord:x_coord + width]
    return image_cropped


def detect_grid_lines_from_image(grayscale_image, image_width, image_height):
    """Detect vertical and horizontal grid lines from the grayscale image."""
    blurred_image = cv2.GaussianBlur(grayscale_image, (5, 5), 0)
    edge_detected_image = cv2.Canny(blurred_image, 30, 100, apertureSize=3)
    detected_lines = cv2.HoughLinesP(
        edge_detected_image, 1, np.pi / 180, threshold=60, minLineLength=80, maxLineGap=5)

    vertical_line_coordinates = []
    horizontal_line_coordinates = []

    if detected_lines is not None:
        for x1, y1, x2, y2 in detected_lines[:, 0]:
            angle_in_degrees = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle_in_degrees) < 10 or abs(angle_in_degrees) > 170:
                horizontal_line_coordinates.append((x1, y1, x2, y2))
            elif abs(angle_in_degrees - 90) < 10 or abs(angle_in_degrees + 90) < 10:
                vertical_line_coordinates.append((x1, y1, x2, y2))

    x_pixel_positions = sorted(set(
        int((x_start + x_end) / 2) for x_start, _, x_end, _ in vertical_line_coordinates
        if 10 <= (x_start + x_end) / 2 <= image_width - 10
    ))

    y_pixel_positions = sorted(set(
        int((y_start + y_end) / 2) for _, y_start, _, y_end in horizontal_line_coordinates
        if 10 <= (y_start + y_end) / 2 <= image_height - 10
    ))

    return x_pixel_positions, y_pixel_positions


def extract_red_pixel_coordinates(hsv_image):
    """Extract coordinates of red-colored pixels after cleaning."""
    mask_lower_red = cv2.inRange(hsv_image, (0, 70, 50), (10, 255, 255))
    mask_upper_red = cv2.inRange(hsv_image, (170, 70, 50), (180, 255, 255))
    combined_red_mask = cv2.bitwise_or(mask_lower_red, mask_upper_red)

    number_of_labels, label_matrix, stats, _ = cv2.connectedComponentsWithStats(
        combined_red_mask, connectivity=8)
    cleaned_mask = np.zeros_like(combined_red_mask)

    for label_index in range(1, number_of_labels):
        x, y, width, height, area = stats[label_index]
        if area > 10 and not (height <= 4 and width >= 10):
            cleaned_mask[label_matrix == label_index] = 255

    red_pixel_positions = np.column_stack(np.where(cleaned_mask))
    return [(x_position, y_position) for y_position, x_position in red_pixel_positions]


def extract_numeric_value_from_image(image_section):
    """Apply OCR to an image crop and extract numeric value."""
    enlarged_image = cv2.resize(
        image_section, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    _, thresholded_image = cv2.threshold(cv2.bitwise_not(
        enlarged_image), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    ocr_configuration = r'--psm 6 --oem 3 -c tessedit_char_whitelist=-0123456789.'
    ocr_text_result = pytesseract.image_to_string(
        thresholded_image, config=ocr_configuration).strip()

    match_result = re.match(r'(-?\d+(\.\d+)?)', ocr_text_result)
    if not match_result:
        return None

    numeric_value = float(match_result.group(1))
    return int(numeric_value) if '.' not in match_result.group(1) else numeric_value * 10000


def convert_pixel_to_physical_coordinates(pixel_coordinates, x_value_range, y_value_range, pixel_bounds):
    """Map pixel positions to corresponding physical coordinates based on OCR scale."""
    x_min_pixel, x_max_pixel, y_top_pixel, y_bottom_pixel = pixel_bounds
    x_min_value, x_max_value, y_min_value, y_max_value = x_value_range + y_value_range

    converted_coordinates = []
    for x_pixel, y_pixel in pixel_coordinates:
        x_mapped = x_min_value + \
            (x_pixel - x_min_pixel) / (x_max_pixel -
                                       x_min_pixel) * (x_max_value - x_min_value)
        y_mapped = y_min_value + (y_bottom_pixel - y_pixel) / \
            (y_bottom_pixel - y_top_pixel) * (y_max_value - y_min_value)
        converted_coordinates.append((x_mapped, y_mapped))

    return converted_coordinates


def save_trace_plot_and_data(x_values, y_values, image_base_name, output_directory_path, crop_img):
    """Save cropped image (top) and reconstructed trace (bottom) as a single image, plus CSV data."""
    trace_image_path = os.path.join(
        output_directory_path, f"{image_base_name}_trace.png")
    trace_data_path = os.path.join(
        output_directory_path, f"{image_base_name}_trace.csv")

    fig, axs = plt.subplots(2, 1, figsize=(10, 8))  

    axs[0].imshow(crop_img)
    axs[0].set_title(f"Cropped Image - {image_base_name}")
    axs[0].axis('off')

    axs[1].plot(x_values, y_values, '-', color='red')
    axs[1].set_title(f"Reconstructed Trace - {image_base_name}")
    axs[1].set_xlabel("X")
    axs[1].set_ylabel("Y")
    axs[1].grid(True)

    plt.tight_layout()
    plt.savefig(trace_image_path)

    # Save the CSV
    dataframe_trace = pd.DataFrame({'X': x_values, 'Y': y_values})
    dataframe_trace.to_csv(trace_data_path, index=False)


def process_entire_image_folder(folder_path):
    """Main function to process all image files inside a folder."""
    for image_file_name in get_all_image_files(folder_path):
        try:
            image_path = os.path.join(folder_path, image_file_name)
            image_base_name = os.path.splitext(image_file_name)[0]
            image_output_directory = os.path.join(folder_path, image_base_name)
            os.makedirs(image_output_directory, exist_ok=True)

            cropped_image = read_and_crop_main_region(image_path)
            if cropped_image is None:
                logging.warning(
                    f"Skipping {image_file_name}: No contour found.")
                continue

            grayscale_cropped_image = cv2.cvtColor(
                cropped_image, cv2.COLOR_RGB2GRAY)
            image_height, image_width = cropped_image.shape[:2]

            x_pixel_axis_positions, y_pixel_axis_positions = detect_grid_lines_from_image(
                grayscale_cropped_image, image_width, image_height)

            if not x_pixel_axis_positions or not y_pixel_axis_positions:
                logging.warning(
                    f"Skipping {image_file_name}: Grid lines not detected.")
                continue

            hsv_cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2HSV)
            red_trace_pixel_coordinates = extract_red_pixel_coordinates(
                hsv_cropped_image)

            x_pixel_start, x_pixel_end = x_pixel_axis_positions[0], x_pixel_axis_positions[-1]
            y_pixel_top, y_pixel_bottom = y_pixel_axis_positions[0], y_pixel_axis_positions[-1]

            x_start_value = extract_numeric_value_from_image(
                grayscale_cropped_image[image_height-34:image_height-4, max(0, x_pixel_start-40):min(image_width, x_pixel_start+40)])
            x_end_value = extract_numeric_value_from_image(
                grayscale_cropped_image[image_height-34:image_height-4, max(0, x_pixel_end-40):min(image_width, x_pixel_end+40)])
            y_start_value = extract_numeric_value_from_image(
                grayscale_cropped_image[max(0, y_pixel_bottom-20):y_pixel_bottom+20, max(0, x_pixel_start-80):x_pixel_start-18])
            y_end_value = extract_numeric_value_from_image(
                grayscale_cropped_image[max(0, y_pixel_top-20):y_pixel_top+20, max(0, x_pixel_start-80):x_pixel_start-18])

            if None in [x_start_value, x_end_value, y_start_value, y_end_value]:
                logging.warning(
                    f"Skipping {image_file_name}: Failed to extract axis values via OCR.")
                continue

            physical_coordinates = convert_pixel_to_physical_coordinates(
                red_trace_pixel_coordinates,
                (x_start_value, x_end_value),
                (y_start_value, y_end_value),
                (x_pixel_start, x_pixel_end, y_pixel_top, y_pixel_bottom)
            )

            x_coordinate_list, y_coordinate_list = zip(
                *sorted(physical_coordinates))
            x_sorted_values = np.array(x_coordinate_list)
            y_interpolated_values = np.interp(
                x_sorted_values, x_sorted_values, np.array(y_coordinate_list))

            save_trace_plot_and_data(
                x_sorted_values, y_interpolated_values, image_base_name, image_output_directory, cropped_image)
            logging.info(
                f"Successfully processed: {image_file_name} → Saved to: {image_output_directory}")

        except Exception as processing_error:
            logging.error(
                f"Error processing {image_file_name}: {processing_error}")
