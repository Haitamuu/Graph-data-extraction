import cv2
import numpy as np

def extract_curve_and_markers(coords, img_shape):
    """
    Sépare une courbe continue et ses marqueurs expérimentaux (ticks/dots superposés).
    """
    ys, xs = coords[:, 0], coords[:, 1]
    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()

    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    mask[ys, xs] = 255

    # 1. Échantillonnage de la ligne continue (profil moyen Y par colonne X)
    unique_x, inv = np.unique(xs, return_inverse=True)
    line_x = unique_x.astype(float)
    line_y = np.bincount(inv, weights=ys) / np.bincount(inv)

    # 2. Détection des marqueurs/ticks par transformée en distance et pics locaux
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    
    # Un marqueur crée un pic local de surépaisseur par rapport au reste de la ligne
    # On cherche les maxima locaux stricts
    dilated = cv2.dilate(dist, np.ones((7, 7), dtype=np.uint8))
    local_peaks = (dist == dilated) & (dist >= 1.5)
    
    num_peaks, _, stats, centroids = cv2.connectedComponentsWithStats(local_peaks.astype(np.uint8), connectivity=8)
    
    markers = []
    for i in range(1, num_peaks):
        cx, cy = centroids[i]
        # Vérifie qu'on est bien sur le tracé
        if cy < img_shape[0] - 15 and cx < img_shape[1] - 15:
            markers.append((cx, cy))
            
    markers.sort(key=lambda p: p[0])

    # Si au moins 4 marqueurs bien répartis le long de la ligne
    if len(markers) >= 4:
        pts_x = np.array([p[0] for p in markers], dtype=float)
        pts_y = np.array([p[1] for p in markers], dtype=float)
        return (line_x, line_y), (pts_x, pts_y)
    
    return (line_x, line_y), None

# Test on test_graph.png curves
import sys, os
sys.path.insert(0, os.path.abspath("."))
from main import segment_image_curves, extract_text_boxes

img = cv2.imread('images/test_graph.png')
ocr_items = extract_text_boxes(img, binarize=True)
boxes = [item['box'] for item in ocr_items]
curves = segment_image_curves(img, boxes)

for idx, c in enumerate(curves):
    line, markers = extract_curve_and_markers(c['coords'], img.shape)
    print(f"Curve {idx} (RGB={c['color'].astype(int).tolist()}):")
    print(f"  Line points: {len(line[0])}")
    if markers is not None:
        print(f"  Markers (ticks/dots) found: {len(markers[0])}")
        print(f"  Sample markers: {list(zip(markers[0][:5].round(1), markers[1][:5].round(1)))}")
    else:
        print(f"  No markers detected (pure continuous line)")
