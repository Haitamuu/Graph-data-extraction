import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
from main import get_ocr_engine, parse_tick_value, calibrate_single_axis, fit_axis_ransac

img = cv2.imread('images/test_graph.png')
h, w = img.shape[:2]

reader = get_ocr_engine()

# High-resolution pass for small images:
scale = max(2.5, 900.0 / max(h, w))
resized = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

ocr_detections = reader.readtext(gray)
items = []
for bbox, raw_text, _ in ocr_detections:
    pts = np.asarray(bbox, dtype=np.float32) / scale
    x_min, y_min = pts.min(axis=0)
    x_max, y_max = pts.max(axis=0)
    val = parse_tick_value(raw_text)
    items.append({
        "text": raw_text,
        "box": (float(x_min), float(y_min), float(x_max), float(y_max)),
        "cx": float((x_min + x_max) / 2.0),
        "cy": float((y_min + y_max) / 2.0),
        "value": val,
    })

num_items = [it for it in items if it["value"] is not None]
for it in num_items:
    print(f"Num: {it['text']} -> {it['value']} at cx={it['cx']:.1f}, cy={it['cy']:.1f}")

tol = max(10, 0.02 * max(h, w))
x_scale, nb_x = calibrate_single_axis(num_items, "cy", tol)
y_scale, nb_y = calibrate_single_axis(num_items, "cx", tol)

print("x_scale:", x_scale, "nb_x:", nb_x)
print("y_scale:", y_scale, "nb_y:", nb_y)
