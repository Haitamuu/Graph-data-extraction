import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
import matplotlib.pyplot as plt

img = cv2.imread('images/test_graph.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Let's inspect the black curve in test_graph.png!
# We know the black curve has:
# 1. Disconnected dots at y=0 (x from 43 to 78)
# 2. Rising curve with dots (x from 78 to 295)
# In fact, what if we use the Distance Transform and Morphological Top-Hat or Hessian / LoG / Circle detection?
# Or what if we use the template matching but with the PROPER threshold and non-maximum suppression radius?
# Let's see what NCC response looks like!

# Let's get the template at (59, 214) or an average template of dots:
tmpl = gray[214 - 3 : 214 + 4, 59 - 3 : 59 + 4] # 7x7
print("Template shape:", tmpl.shape)

res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
print("Res min/max:", res.min(), res.max())

# Let's test different thresholds: 0.4, 0.5, 0.6, 0.7
for th in [0.35, 0.45, 0.55, 0.65, 0.75]:
    peaks = (res == cv2.dilate(res, np.ones((7, 7)))) & (res > th)
    print(f"Threshold {th}: {peaks.sum()} peaks")
