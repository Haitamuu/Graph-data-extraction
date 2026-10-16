import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

img = cv2.imread('images/test_graph.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

# Let's see what binary looks like at the bottom-left:
# x in [40, 85], y in [210, 225]
bottom_left = binary[210:222, 40:85]
print("Binary at bottom left: shape", bottom_left.shape)
cv2.imwrite('scratch/binary_bottom_left.png', cv2.resize(bottom_left, (450, 120), interpolation=cv2.INTER_NEAREST))

# Now in extract_dark_curves:
# horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
# vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
# grid_mask = cv2.dilate(cv2.add(horiz_lines, vert_lines), np.ones((3, 3), np.uint8), iterations=1)
horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
grid_mask = cv2.dilate(cv2.add(horiz_lines, vert_lines), np.ones((3, 3), np.uint8), iterations=1)

cleaned = cv2.subtract(binary, grid_mask)
cleaned_bl = cleaned[210:222, 40:85]
cv2.imwrite('scratch/cleaned_bl.png', cv2.resize(cleaned_bl, (450, 120), interpolation=cv2.INTER_NEAREST))

print("Saved binary and cleaned bottom left.")
