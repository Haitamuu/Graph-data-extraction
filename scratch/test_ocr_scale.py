import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False, verbose=False)
crop = cv2.imread('scratch/x_axis_crop.png')

print("Direct OCR on crop:")
res = reader.readtext(crop)
for r in res:
    print(" ", r[1], r[0])

print("\nUpscaled 2x on crop:")
crop2 = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
res2 = reader.readtext(crop2)
for r in res2:
    print(" ", r[1], r[0])

print("\nUpscaled 3x on crop:")
crop3 = cv2.resize(crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
res3 = reader.readtext(crop3)
for r in res3:
    print(" ", r[1], r[0])

# What about the whole image resized?
# In main.py:
# scale = min(OCR_SCALE_FACTOR, OCR_MAX_DIMENSION / max(height, width))
# For test_graph: height=292, width=315.
# OCR_SCALE_FACTOR was 1.5!
# 315 * 1.5 = 472 px! That's tiny for small digits like 0, 2, 4, 6, 8!
# Let's test the whole image upscaled with higher scale:
img = cv2.imread('images/test_graph.png')
print("\nWhole image with scale=2.5:")
img_scaled = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
gray = cv2.cvtColor(img_scaled, cv2.COLOR_BGR2GRAY)
res_full = reader.readtext(gray)
for r in res_full:
    print(" ", r[1], r[0])
