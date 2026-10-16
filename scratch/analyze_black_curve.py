import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
import matplotlib.pyplot as plt

img = cv2.imread('images/test_graph.png')
h, w = img.shape[:2]

# Let's see the colors in test_graph:
# Blue curve, Red curve, Black curve.
# Let's inspect BGR / HSV of each:
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Blue mask:
blue_mask = (hsv[:,:,0] >= 90) & (hsv[:,:,0] <= 130) & (hsv[:,:,1] > 60)
# Red mask:
red_mask = ((hsv[:,:,0] <= 15) | (hsv[:,:,0] >= 165)) & (hsv[:,:,1] > 60)

# What are dark/black pixels in the plot area?
# The plot box is approximately: x in [42, 296], y in [40, 216]
plot_box = img[40:217, 42:297]
cv2.imwrite('scratch/plot_box.png', plot_box)

# In the plot box, what is dark?
# Background is white (~255, 255, 255)
# Any pixel with gray < 180 is either colored or black/dark!
dark_all = (gray < 160)
colored = blue_mask | red_mask

# Pure black / dark achromatic:
dark_achromatic = dark_all & (~colored) & (hsv[:,:,1] < 40)

# Save dark achromatic mask in the plot area:
dark_canvas = np.zeros((h, w), dtype=np.uint8)
dark_canvas[dark_achromatic] = 255
# Mask out axes borders
dark_canvas_plot = np.zeros((h, w), dtype=np.uint8)
dark_canvas_plot[41:216, 43:296] = dark_canvas[41:216, 43:296]
cv2.imwrite('scratch/dark_canvas_plot.png', dark_canvas_plot)

# Text inside plot:
# "750 °C" is around x in [210, 260], y in [148, 170]
# "Dots: Exp data", "Lines: Fitting" around x in [200, 285], y in [185, 220]
print("Plot box analyzed and masks saved.")
