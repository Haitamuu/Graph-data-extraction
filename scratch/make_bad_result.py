import cv2
import matplotlib.pyplot as plt
import numpy as np

img = cv2.imread("images/test_graph.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = (hsv[:,:,1] > 50) & (hsv[:,:,2] > 50)
coords = np.column_stack(np.where(mask))

# Sort by x
coords = coords[coords[:,1].argsort()]

plt.figure(figsize=(6,4))
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.title("test_graph.png - Image originale")
plt.savefig("data/bad_result_original.png", dpi=100)
plt.close()

plt.figure(figsize=(6,4))
# Plot all colored pixels as a single line
plt.plot(coords[:,1], coords[:,0], color='black')
plt.gca().invert_yaxis()
plt.title("Nuage de points indifférencié (Toutes courbes confondues)")
plt.savefig("data/bad_result_mixed.png", dpi=100)
plt.close()

print("Bad results generated.")
