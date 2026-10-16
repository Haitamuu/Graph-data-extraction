import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

img = cv2.imread('images/test_graph.png')
from main import extract_text_boxes, segment_image_curves

ocr_items = extract_text_boxes(img, binarize=True)
boxes = [item['box'] for item in ocr_items]
curves = segment_image_curves(img, boxes, y_max_limit=220)

for idx, c in enumerate(curves):
    if c['color'].sum() == 0:
        dark_coords = c['coords']
        break

mask = np.zeros(img.shape[:2], dtype=np.uint8)
mask[dark_coords[:, 0], dark_coords[:, 1]] = 255

# Let's inspect mask:
# Connected components:
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

line_comp = np.zeros_like(mask)
line_comp[labels == 1] = 255 # The main rising curve

# Let's test distance transform on line_comp:
dist = cv2.distanceTransform(line_comp, cv2.DIST_L2, 5)
print("Dist min/max on line_comp:", dist.min(), dist.max())

# Along the line, the line thickness is ~1 to 1.5 pixels.
# The markers are circles/disks with thickness ~2.5 to 3.5 pixels!
# Let's see the histogram of dist values:
print("Dist percentiles:", [np.percentile(dist[dist > 0], p) for p in [25, 50, 75, 90, 95, 99]])

# Peaks in distance transform:
dil = cv2.dilate(dist, np.ones((7, 7), np.uint8))
peaks = (dist == dil) & (dist >= 1.8)
num_p, _, stats_p, cents_p = cv2.connectedComponentsWithStats(peaks.astype(np.uint8), connectivity=8)
print(f"Distance transform peaks with dist >= 1.8: {num_p - 1} peaks")

peaks_list = [cents_p[i] for i in range(1, num_p)]
peaks_list.sort(key=lambda p: p[0])
print("X coordinates of distance transform peaks on line_comp:")
print([round(p[0], 1) for p in peaks_list])
