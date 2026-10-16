import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

img = cv2.imread('images/test_graph.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Saturation > 40 and Value > 50 is colored:
colored_mask = (hsv[:,:,1] > 40) & (hsv[:,:,2] > 50)
# Dark achromatic is gray < 160 and NOT colored:
dark_mask = (gray < 160) & (~colored_mask)

# Plot box crop: x in [41, 85], y in [210, 220]
crop = dark_mask[210:220, 41:85].astype(np.uint8) * 255
cv2.imwrite('scratch/dark_mask_bl.png', cv2.resize(crop, (440, 100), interpolation=cv2.INTER_NEAREST))
print("Saved dark_mask_bl.png")
