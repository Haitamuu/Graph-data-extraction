import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

img = cv2.imread('images/test_graph.png')
# Let's crop the knee region of the black curve where it transitions from y=0 to rising:
# x from 40 to 120, y from 160 to 220
knee_crop = img[160:225, 40:120]
cv2.imwrite('scratch/knee_crop.png', knee_crop)

# Let's also crop the entire black curve:
black_crop = img[35:225, 40:300]
cv2.imwrite('scratch/black_crop.png', black_crop)
print("Crops saved.")
