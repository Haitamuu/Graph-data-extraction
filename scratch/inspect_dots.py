import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

img = cv2.imread('images/test_graph.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Let's inspect the markers in test_graph.png!
# Notice the template used in main.py:
# marker_template_indices[1]:
# Let's find all connected components in dark_achromatic mask
dark_canvas_plot = cv2.imread('scratch/dark_canvas_plot.png', cv2.IMREAD_GRAYSCALE)

# Also let's check what the dots look like.
# Let's crop a few dots and save them enlarged!
# At y=0: around x=54, y=215
dot1 = img[210:220, 50:60]
# Along the curve: around x=100, y=190
dot2 = img[185:195, 95:105]
# Along the curve: around x=150, y=130
dot3 = img[125:135, 145:155]
# Along the curve: around x=200, y=80
dot4 = img[75:85, 195:205]

cv2.imwrite('scratch/dot1_enlarged.png', cv2.resize(dot1, (80, 80), interpolation=cv2.INTER_NEAREST))
cv2.imwrite('scratch/dot2_enlarged.png', cv2.resize(dot2, (80, 80), interpolation=cv2.INTER_NEAREST))
cv2.imwrite('scratch/dot3_enlarged.png', cv2.resize(dot3, (80, 80), interpolation=cv2.INTER_NEAREST))
cv2.imwrite('scratch/dot4_enlarged.png', cv2.resize(dot4, (80, 80), interpolation=cv2.INTER_NEAREST))

print("Saved enlarged dot crops.")
