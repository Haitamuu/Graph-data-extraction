import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

img = cv2.imread('images/test_graph.png')
from main import extract_text_boxes, extract_dark_curves, segment_image_curves

ocr_items = extract_text_boxes(img, binarize=True)
boxes = [item['box'] for item in ocr_items]
curves = segment_image_curves(img, boxes)

for idx, c in enumerate(curves):
    if c['color'].sum() == 0:
        dark_coords = c['coords']
        break

mask = np.zeros(img.shape[:2], dtype=np.uint8)
mask[dark_coords[:, 0], dark_coords[:, 1]] = 255

num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
print(f"Num labels in dark mask: {num_labels}")
for i in range(1, num_labels):
    w_i, h_i, a_i = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT], stats[i, cv2.CC_STAT_AREA]
    cx, cy = centroids[i]
    print(f"Comp {i}: center=({cx:.1f}, {cy:.1f}), w={w_i}, h={h_i}, area={a_i}")
