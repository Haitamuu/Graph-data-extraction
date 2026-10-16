import cv2
import numpy as np

img = cv2.imread('images/test_graph.png')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
red = ((hsv[:,:,0] < 12) | (hsv[:,:,0] > 168)) & (hsv[:,:,1] > 40) & (hsv[:,:,2] > 40)
blue = (hsv[:,:,0] >= 100) & (hsv[:,:,0] <= 130) & (hsv[:,:,1] > 40) & (hsv[:,:,2] > 40)

# Let's test SimpleBlobDetector or morphological top-hat on the gray/color channels
# In the original image:
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Test Method A: Morphological White Top-Hat / Black Top-Hat on the curve mask
# Black Top-Hat on inverted mask (or closing - original):
# A marker of radius R that bulges on a line of width W:
# If we erode the mask by kernel 3x3:
# The 1-2px line vanishes!
# Only the core of the markers remains!
k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

for name, mask in [('Red', red), ('Blue', blue)]:
    eroded = cv2.erode(mask.astype(np.uint8), k3)
    num, lab, stats, cents = cv2.connectedComponentsWithStats(eroded, connectivity=8)
    print(f"=== {name} with Erode (3x3) ===")
    print(f"Components count: {num - 1}")
    valid = []
    for i in range(1, num):
        cx, cy = cents[i]
        area = stats[i, 4]
        if cy < 220 and cx < 280:
            valid.append((cx, cy, area))
    print(f"Valid markers in plot: {len(valid)}")
    for v in valid[:10]:
        print(f"  marker at x={v[0]:.1f}, y={v[1]:.1f}, area={v[2]}")
