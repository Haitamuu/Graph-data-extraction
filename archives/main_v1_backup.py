import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, MeanShift
import easyocr
import re
import os
import glob
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
os.environ['OMP_NUM_THREADS'] = '1'

# ==============================================================================
# CONFIGURATION DU PROJET - 100% INTELLIGENT
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSSIER_IMAGES = os.path.join(BASE_DIR, "images")
DOSSIER_RESULTATS = os.path.join(BASE_DIR, "data")
NOMBRE_DE_COURBES = "AUTO"

# ==============================================================================
# MOTEUR D'EXTRACTION BATCH AVEC OCR (Methode de Triangulation)
# ==============================================================================

print("Chargement du moteur IA de lecture de texte (EasyOCR)...")
ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
print("Moteur IA pret.")




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


def extract_axes_scale(image):
    """
    Methode infaillible par alignement (Clustering) :
    Les labels de l'axe Y sont tous alignes verticalement (meme coordonnee X).
    Les labels de l'axe X sont tous alignes horizontalement (meme coordonnee Y).
    """
    img_big = cv2.resize(image, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img_big, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    results = ocr_reader.readtext(thresh)
    
    numbers = []
    ocr_results = []
    for bbox, text, prob in results:
        # Stocker les bounding boxes (divisees par 4) et le texte
        scaled_bbox = [[pt[0]/4.0, pt[1]/4.0] for pt in bbox]
        ocr_results.append({'text': text, 'bbox': scaled_bbox})
        
        clean_text = text.replace(',', '.').replace(' ', '').strip()
        match = re.search(r'^-?\d+(\.\d+)?$', clean_text)
        if match:
            val = float(match.group())
            cx = ((bbox[0][0] + bbox[1][0]) / 2) / 4.0
            cy = ((bbox[0][1] + bbox[2][1]) / 2) / 4.0
            numbers.append({'val': val, 'cx': cx, 'cy': cy})

    print(f"  [DEBUG OCR] Nombres trouves : {[n['val'] for n in numbers]}")
    if len(numbers) < 3:
        return None, None, ocr_results

    # Recherche de l'axe X (Nombres alignes horizontalement -> meme CY)
    x_groups = []
    for num in numbers:
        added = False
        for group in x_groups:
            if abs(group[0]['cy'] - num['cy']) < 15: # Tolerance de 15 pixels
                group.append(num)
                added = True
                break
        if not added:
            x_groups.append([num])
            
    # Le groupe avec la plus grande variation en X est l'axe X
    x_axis_group = max(x_groups, key=lambda g: max(n['cx'] for n in g) - min(n['cx'] for n in g) if len(g)>1 else 0)
    
    # Recherche de l'axe Y (Nombres alignes verticalement -> meme CX)
    y_groups = []
    for num in numbers:
        added = False
        for group in y_groups:
            if abs(group[0]['cx'] - num['cx']) < 15: # Tolerance de 15 pixels
                group.append(num)
                added = True
                break
        if not added:
            y_groups.append([num])
            
    # Le groupe avec la plus grande variation en Y est l'axe Y
    y_axis_group = max(y_groups, key=lambda g: max(n['cy'] for n in g) - min(n['cy'] for n in g) if len(g)>1 else 0)

    x_scale = None
    if len(x_axis_group) >= 2:
        x_axis_group.sort(key=lambda item: item['cx'])
        p1, p2 = x_axis_group[0], x_axis_group[-1]
        if p2['cx'] - p1['cx'] > 10 and p2['val'] != p1['val']:
            x_scale = (p1['cx'], p1['val'], p2['cx'], p2['val'])

    y_scale = None
    if len(y_axis_group) >= 2:
        y_axis_group.sort(key=lambda item: item['cy'])
        p1, p2 = y_axis_group[0], y_axis_group[-1]
        if p2['cy'] - p1['cy'] > 10 and p2['val'] != p1['val']:
            y_scale = (p1['cy'], p1['val'], p2['cy'], p2['val'])
            
    return x_scale, y_scale, ocr_results

def extract_black_curves(image, ocr_bboxes, mask_colored=None):
    """
    Extrait les courbes noires en gommant le texte, les lignes droites, ET les courbes colorees.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # 1. Gommer le texte avec les bounding boxes OCR
    if ocr_bboxes:
        for bbox in ocr_bboxes:
            pts = np.array(bbox, np.int32)
            x, y, w, h = cv2.boundingRect(pts)
            cv2.rectangle(thresh, (x-5, y-5), (x+w+5, y+h+5), 0, -1)
        
    # 2. Gommer les lignes horizontales et verticales (axes, grille)
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    hl = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, hk)
    
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vl = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vk)
    
    grid = cv2.add(hl, vl)
    kernel_dilate = np.ones((3,3), np.uint8)
    grid = cv2.dilate(grid, kernel_dilate, iterations=3)
    
    curve_only = cv2.subtract(thresh, grid)
    
    # 3. Gommer les courbes colorees (si elles existent)
    if mask_colored is not None:
        # mask_colored est un boolean array, on le convertit en uint8
        colored_uint8 = (mask_colored.astype(np.uint8) * 255)
        # Dilater legerement le masque colore pour eviter les bordures anti-aliasees noires
        colored_uint8 = cv2.dilate(colored_uint8, np.ones((3,3), np.uint8), iterations=3)
        curve_only = cv2.subtract(curve_only, colored_uint8)
    
    # 4. Nettoyer le bruit
    contours, _ = cv2.findContours(curve_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    final_mask = np.zeros_like(curve_only)
    for c in contours:
        if cv2.arcLength(c, True) > 20: # Ignorer les points minuscules de poussiere
            x, y, w, h = cv2.boundingRect(c)
            # Une vraie courbe doit avoir une envergure significative (pas juste une fleche d'axe ou un residu de lettre)
            if w > 30 or h > 30:
                cv2.drawContours(final_mask, [c], -1, 255, 2)
            
    # Retourner les coordonnees (Y, X)
    return np.column_stack(np.where(final_mask > 0))

def save_verification_plot(plot_area, all_data, output_path):
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(plot_area, cv2.COLOR_BGR2RGB))
    plt.title("Image Originale")
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    for curve_name, df in all_data.items():
        color_hex = '#000000'
        label_name = curve_name
        if '_' in curve_name and curve_name.split('_')[-1].startswith('#'):
            color_hex = curve_name.split('_')[-1]
            label_name = curve_name.split('_')[1]
            
        x_col = [c for c in df.columns if c.endswith('_X')][0]
        y_col = [c for c in df.columns if c.endswith('_Y')][0]
        plt.plot(df[x_col], df[y_col], label=label_name, color=color_hex, linewidth=2)
        
    plt.title("Reconstruction Automatique")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def process_image(image_path):
    print(f"\nTraitement de : {os.path.basename(image_path)}")
    img = cv2.imread(image_path)
    if img is None:
        print("  -> Erreur : Impossible de lire l'image.")
        return False
        
    x_rect, y_rect = 0, 0
    w_rect, h_rect = img.shape[1], img.shape[0]
    plot_area = img
    
    print("  -> Lecture OCR avancee (Triangulation des pixels)...")
    x_scale, y_scale, ocr_results = extract_axes_scale(img)
    
    if not x_scale or not y_scale:
        print("  -> Echec OCR (pas assez de chiffres lus). Passage en mode Sauvetage (Coordonnees en Pixels).")
        h, w = img.shape[:2]
        # (px_min, val_min, px_max, val_max)
        x_scale = (0, 0, w, w)
        y_scale = (h, 0, 0, h)
        
    print(f"  -> Echelle X deduite entre {x_scale[1]} et {x_scale[3]}")
    print(f"  -> Echelle Y deduite entre {y_scale[1]} et {y_scale[3]}")
    
    img_rgb = cv2.cvtColor(plot_area, cv2.COLOR_BGR2RGB)
    hsv_area = cv2.cvtColor(plot_area, cv2.COLOR_BGR2HSV)
    
    # Filtrage strict : on ne garde que les pixels colores (Saturation > 50) pour ignorer les textes anti-aliasses
    mask = (hsv_area[:,:,1] > 50) & (hsv_area[:,:,2] > 50)
    colored_pixels_hsv = hsv_area[mask]
    colored_pixels_rgb = img_rgb[mask]
    colored_coords = np.column_stack(np.where(mask))
    
    num_curves = 0
    final_coords = []
    final_labels = []
    final_colors = []
    
    # === 0. LECTURE DES LEGENDES ===
    legends = []
    if ocr_results:
        legends = extract_legends(img, ocr_results, x_scale, y_scale)
    
    # === 1. COURBES COLOREES ===
    if len(colored_pixels_hsv) >= 500:
        if str(NOMBRE_DE_COURBES).strip().upper() == "AUTO":
            hues = colored_pixels_hsv[:, 0]
            hues_rad = hues * (np.pi / 90.0)
            features = np.column_stack((np.cos(hues_rad) * 100, np.sin(hues_rad) * 100))
            
            sample_size = min(3000, len(features))
            indices = np.random.choice(len(features), sample_size, replace=False)
            ms = MeanShift(bandwidth=30, bin_seeding=True)
            ms.fit(features[indices])
            
            labels = ms.predict(features)
            num_colored = len(np.unique(labels))
            
            for i in range(num_colored):
                final_colors.append(np.mean(colored_pixels_rgb[labels == i], axis=0))
        else:
            num_colored = int(NOMBRE_DE_COURBES)
            kmeans = KMeans(n_clusters=num_colored, random_state=42, n_init=10)
            labels = kmeans.fit_predict(colored_pixels_rgb)
            for i in range(num_colored):
                final_colors.append(kmeans.cluster_centers_[i])
                
        final_coords.extend(colored_coords)
        final_labels.extend(labels)
        num_curves += num_colored
        
    # === 2. COURBE NOIRE (Morphologie) ===
    bboxes_only = [r['bbox'] for r in ocr_results] if ocr_results else None
    black_curve_coords = extract_black_curves(img, bboxes_only, mask)
    if len(black_curve_coords) >= 200:
        print(f"  -> Courbe noire/grise supplementaire detectee via morphologie ! ({len(black_curve_coords)} pixels)")
        final_coords.extend(black_curve_coords)
        final_labels.extend([num_curves] * len(black_curve_coords))
        final_colors.append([0, 0, 0])
        num_curves += 1
        
    if num_curves == 0:
        print("  -> Erreur : Aucune courbe (ni coloree, ni noire) detectee.")
        return False
        
    colored_coords = np.array(final_coords)
    labels = np.array(final_labels)
    colors = np.array(final_colors)
    
    all_data = {}
    
    for i in range(num_curves):
        curve_coords = colored_coords[labels == i]
        y_pixels = curve_coords[:, 0]
        x_pixels = curve_coords[:, 1]
        
        unique_x = np.unique(x_pixels)
        avg_y = []
        for ux in unique_x:
            avg_y.append(np.mean(y_pixels[x_pixels == ux]))
            
        unique_x = np.array(unique_x)
        avg_y = np.array(avg_y)
        
        # Pixels absolus sur l'image d'origine
        abs_px_x = unique_x + x_rect
        abs_px_y = avg_y + y_rect
        
        # Interpolation mathematique stricte a partir des ancres OCR
        real_x = x_scale[1] + (abs_px_x - x_scale[0]) * (x_scale[3] - x_scale[1]) / (x_scale[2] - x_scale[0])
        real_y = y_scale[1] + (abs_px_y - y_scale[0]) * (y_scale[3] - y_scale[1]) / (y_scale[2] - y_scale[0])
        
        color_hex = '#%02x%02x%02x' % tuple(colors[i].astype(int))
        curve_name = f"Courbe_{i+1}_{color_hex}"
        
        # Mapping avec la legende
        if legends:
            min_dist = float('inf')
            best_legend = None
            for leg in legends:
                dist = np.linalg.norm(np.array(colors[i]) - np.array(leg['color_bgr']))
                if dist < min_dist and dist < 120:
                    min_dist = dist
                    best_legend = leg['text']
            if best_legend:
                curve_name = best_legend
                print(f"  -> Courbe {i+1} nommee '{curve_name}' d'apres la legende ! (Couleur: {colors[i]})")
        
        df_curve = pd.DataFrame({f"{curve_name}_X": real_x, f"{curve_name}_Y": real_y})
        all_data[curve_name] = df_curve
        
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    excel_path = os.path.join(DOSSIER_RESULTATS, f"{base_name}_donnees.xlsx")
    plot_path = os.path.join(DOSSIER_RESULTATS, f"{base_name}_verification.png")
    
    pd.concat(all_data.values(), axis=1).to_excel(excel_path, index=False)
    save_verification_plot(plot_area, all_data, plot_path)
    
    print(f"  -> Operation reussie ! ({num_curves} courbes).")
    return True

def main():
    print("==========================================================")
    print("MOTEUR D'EXTRACTION OCR AVANCE (ZERO CONFIG)")
    print("==========================================================")
    
    os.makedirs(DOSSIER_RESULTATS, exist_ok=True)
    os.makedirs(DOSSIER_IMAGES, exist_ok=True)
    
    image_files = []
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.bmp'):
        image_files.extend(glob.glob(os.path.join(DOSSIER_IMAGES, ext)))
        
    if not image_files:
        print(f"\nAucune image trouvee dans '{DOSSIER_IMAGES}'.")
        return
        
    print(f"\n{len(image_files)} image(s) trouvee(s). Debut du traitement...\n")
    success_count = sum(1 for img_path in image_files if process_image(img_path))
    print(f"\nTRAITEMENT TERMINE : {success_count}/{len(image_files)} succes.")

if __name__ == "__main__":
    main()
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

