import sys, os
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
import matplotlib.pyplot as plt
from main import segment_image_curves, extract_text_boxes

img = cv2.imread('images/test_graph.png')
ocr_items = extract_text_boxes(img, binarize=True)
boxes = [item['box'] for item in ocr_items]
curves = segment_image_curves(img, boxes)

print(f"Number of curves: {len(curves)}")
for idx, c in enumerate(curves):
    rgb = c['color'].astype(int)
    coords = c['coords']
    print(f"Curve {idx}: RGB={rgb.tolist()}, pixels={len(coords)}")
    
    # Let's inspect the mask of this curve
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    mask[coords[:, 0], coords[:, 1]] = 255
    cv2.imwrite(f"scratch/curve_{idx}_mask.png", mask)

# Also let's inspect the original image in detail:
# Are there dots and lines for each color?
