import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np

# Let's inspect the black dots along the black curve in test_graph.png!
img = cv2.imread('images/test_graph.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Where are the black dots in reality?
# In test_graph.png:
# Black curve has dots from x=43 to x=292.
# Let's find the spacing between dots:
# In the original physical experiment, dots are recorded at regular time intervals dt!
# Let's check dt:
# At 10 min, x = 296 px. At 0 min, x = 42 px. Total span = 254 px for 10 min.
# So 1 min = 25.4 px.
# Look at the dots along the black curve:
# Between x=43 and x=79: dots at ~43, ~49, ~55, ~62, ~68, ~74, ~80 -> step of ~6.3 px!
# 6.3 px / 25.4 px/min = 0.25 min = 15 seconds!
# Every 0.25 min (15 seconds), there is an experimental data point!
# 10 min / 0.25 min = 40 points total (from t=0 to t=10 min)!
# 40 points, exactly evenly spaced in time (abscissa step ~6.35 pixels)!
print("Theoretical spacing of dots: ~6.35 pixels (every 0.25 min, ~40 points total)!")
