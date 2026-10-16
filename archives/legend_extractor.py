import cv2
import numpy as np
import re

def extract_legends(img, ocr_results, x_scale, y_scale):
    """
    Extrait les legendes (couleur + texte) pour renommer les colonnes du CSV.
    """
    legends = []
    
    # Trouver l'axe des X et Y en pixels
    x_min = min(x_scale[0], x_scale[2]) if x_scale else 0
    x_max = max(x_scale[0], x_scale[2]) if x_scale else img.shape[1]
    y_min = min(y_scale[0], y_scale[2]) if y_scale else 0
    y_max = max(y_scale[0], y_scale[2]) if y_scale else img.shape[0]
    
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    for item in ocr_results:
        text = item['text'].strip()
        # Ignorer les textes numeriques pur (ce sont surement des axes)
        if re.match(r'^-?\d+(\.\d+)?$', text.replace(',', '.')):
            continue
            
        # Ignorer les textes d'un caractere
        if len(text) < 2:
            continue
            
        # Obtenir bbox
        bbox = item['bbox']
        pts = np.array(bbox, np.int32)
        x, y, w, h = cv2.boundingRect(pts)
        
        # Ignorer les textes qui sont proches des axes detectes ou en dehors du graphe
        # On suppose que la legende est a l'interieur du graphe ou bien isolee.
        # Par defaut, on va juste regarder la couleur a gauche.
        
        # On regarde une fenetre juste a GAUCHE du texte (la ou il y a le carre ou la ligne de couleur)
        patch_width = int(h * 2.5) # on regarde a gauche sur une largeur de 2.5x la hauteur
        patch_x = max(0, x - patch_width - 5)
        patch_y = max(0, y - 2)
        patch_h = h + 4
        
        if patch_width <= 0 or patch_h <= 0: continue
        
        patch_hsv = hsv_img[patch_y:patch_y+patch_h, patch_x:patch_x+patch_width]
        patch_bgr = img[patch_y:patch_y+patch_h, patch_x:patch_x+patch_width]
        
        # Ne garder que les pixels colores ou sombres dans ce patch (ignorer le fond blanc)
        # Saturation > 50 (colore) ou Value < 100 (noir/gris)
        mask_colored = (patch_hsv[:,:,1] > 50)
        mask_dark = (patch_hsv[:,:,2] < 150)
        mask_valid = mask_colored | mask_dark
        
        valid_pixels = patch_bgr[mask_valid]
        if len(valid_pixels) > 10:
            # Couleurs moyenne
            avg_color = np.median(valid_pixels, axis=0) # [B, G, R]
            legends.append({
                'text': text,
                'color_bgr': avg_color.tolist()
            })
            print(f"  [LEGENDE] Texte: '{text}' | Couleur BGR: {avg_color}")
            
    return legends
