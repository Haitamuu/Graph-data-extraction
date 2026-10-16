import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
from scipy.ndimage import maximum_filter

img = cv2.imread('images/test_graph.png')
from main import extract_text_boxes, segment_image_curves

ocr_items = extract_text_boxes(img, binarize=False)
boxes = [item['box'] for item in ocr_items]
curves = segment_image_curves(img, boxes, y_max_limit=220)

for idx, c in enumerate(curves):
    if c['color'].sum() == 0:
        dark_c = c
        break

coords = dark_c['coords']
ys, xs = coords[:, 0], coords[:, 1]
mask = np.zeros(img.shape[:2], dtype=np.uint8)
mask[ys, xs] = 255

num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
disconnected = []
templates = []
line_mask = np.zeros_like(mask)

for i in range(1, num_labels):
    w_i, h_i, a_i = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT], stats[i, cv2.CC_STAT_AREA]
    if w_i > 20 or h_i > 20:
        line_mask[labels == i] = 255
    elif 2 <= a_i <= 70 and w_i <= 16 and h_i <= 16:
        disconnected.append(centroids[i])
        if 3 <= w_i <= 10 and 3 <= h_i <= 10 and 0.7 <= (w_i / h_i) <= 1.4 and 4 <= a_i <= 35:
            templates.append(i)

print(f"Disconnected markers found: {len(disconnected)}")
print("Disconnected X coordinates:", [round(p[0], 1) for p in sorted(disconnected, key=lambda p: p[0])])

# Now test template matching or distance transform on line_mask:
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
tmpl_idx = templates[1]
cx, cy = int(round(centroids[tmpl_idx][0])), int(round(centroids[tmpl_idx][1]))
r = 3
template = gray[cy - r : cy + r + 1, cx - r : cx + r + 1]
th, tw = template.shape
res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
dil = cv2.dilate(line_mask, np.ones((7, 7), np.uint8))
roi = dil[th // 2 : th // 2 + res.shape[0], tw // 2 : tw // 2 + res.shape[1]]
res_roi = np.where(roi > 0, res, 0)

for filt_size in [5, 6, 7]:
    for thresh in [0.35, 0.40, 0.45, 0.50]:
        peaks = (res_roi == maximum_filter(res_roi, size=filt_size)) & (res_roi > thresh)
        py, px = np.where(peaks)
        pts = [np.array([x + tw / 2.0, y + th / 2.0]) for x, y in zip(px, py)]
        # Merge with disconnected:
        all_pts = disconnected + pts
        all_pts.sort(key=lambda p: p[0])
        cleaned = []
        for p in all_pts:
            if not cleaned or np.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) >= 4.5:
                cleaned.append(p)
        print(f"filt_size={filt_size}, thresh={thresh:.2f} -> {len(cleaned)} total markers (pts on line: {len(pts)})")
