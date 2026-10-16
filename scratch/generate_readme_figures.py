"""
Script to generate high-resolution visual explanation figures for README.md
using the 'test_graph.png' example.
"""
import os
import sys
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from main import (
    calibrate_axes,
    extract_text_boxes,
    segment_image_curves,
    sample_curve_and_markers,
    project_to_axis_units,
    extract_dark_curves,
    get_closest_color_name,
)

OUT_DIR = os.path.join(ROOT, "docs", "images")
os.makedirs(OUT_DIR, exist_ok=True)

img_path = os.path.join(ROOT, "images", "test_graph.png")
img_bgr = cv2.imread(img_path)
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
h, w = img_bgr.shape[:2]

# Style configuration
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

print("1. Generating Step 0: Input Image figure...")
fig, ax = plt.subplots(figsize=(6, 6), dpi=180)
ax.imshow(img_rgb)
ax.set_title("Input Graphic: 'test_graph.png' (316 \u00d7 338 px)", fontsize=13, fontweight='bold', pad=12)
ax.axis("on")
ax.set_xlabel("Pixel X Coordinate", fontsize=10, color='#555555')
ax.set_ylabel("Pixel Y Coordinate", fontsize=10, color='#555555')
ax.tick_params(colors='#555555', labelsize=9)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "step0_input_image.png"), dpi=180)
plt.close(fig)

print("2. Running OCR and Axis Calibration...")
x_scale, y_scale, ocr_items = calibrate_axes(img_bgr)
raw_y_scale = y_scale
y_max_limit = int(max(raw_y_scale[0], raw_y_scale[2]) + 6) if raw_y_scale is not None else None

print("Generating Step 1: OCR & Calibration figure...")
fig = plt.figure(figsize=(16, 5.5), dpi=180)
gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 1.0, 1.0], wspace=0.25)

ax1 = fig.add_subplot(gs[0, 0])
ax2_y = fig.add_subplot(gs[0, 1])
ax2_x = fig.add_subplot(gs[0, 2])

# Panel 1: OCR detections overlay
ax1.imshow(img_rgb)
ax1.set_title("Dual-Pass OCR & Token Classification", fontsize=11, fontweight='bold', pad=10)

for item in ocr_items:
    x0, y0, x1, y1 = item["box"]
    val = item["value"]
    txt = item["text"]
    
    if val is not None:
        # Numeric tick
        rect = patches.Rectangle((x0, y0), x1 - x0, y1 - y0, linewidth=1.8, edgecolor='#00CC44', facecolor='none')
        ax1.add_patch(rect)
        ax1.text(x1 + 2, y1, f"{val:g}", color='#008822', fontsize=7.5, fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.15', facecolor='#EAFFEA', edgecolor='#00CC44', alpha=0.9))
    else:
        # Text label / legend
        rect = patches.Rectangle((x0, y0), x1 - x0, y1 - y0, linewidth=1.4, edgecolor='#FF8800', facecolor='none', linestyle='--')
        ax1.add_patch(rect)

ax1.plot([], [], color='#00CC44', linewidth=2, label='Validated Tick Values (Numeric)')
ax1.plot([], [], color='#FF8800', linewidth=1.5, linestyle='--', label='Text Tokens & Annotations')
ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)
ax1.axis('off')

# Extract exact calibrated ticks
y_ticks = [it for it in ocr_items if it["value"] is not None and it["cx"] < 40 and it["value"] <= 1.0]
x_ticks = [it for it in ocr_items if it["value"] is not None and it["cy"] > 230 and it["value"] >= 1.0]

y_vals = np.array([it["value"] for it in y_ticks])
y_px = np.array([it["cy"] for it in y_ticks])
x_vals = np.array([it["value"] for it in x_ticks])
x_px = np.array([it["cx"] for it in x_ticks])

# Panel 2: Y-Axis Calibration
p_y = np.polyfit(y_px, y_vals, 1)
lin_y_px = np.linspace(30, 230, 100)
ax2_y.scatter(y_px, y_vals, color='#1F77B4', s=65, zorder=5, label='OCR Inliers')
ax2_y.plot(lin_y_px, np.polyval(p_y, lin_y_px), color='#1F77B4', linestyle='-', linewidth=2,
           label=f'RANSAC Fit:\nY = {p_y[0]:.4f}\u00d7px + {p_y[1]:.3f}')
ax2_y.set_title("Y-Axis Calibration (RANSAC Consensus)", fontsize=11, fontweight='bold', pad=10)
ax2_y.set_xlabel("Pixel Y Position (cy in px)", fontsize=10)
ax2_y.set_ylabel("Physical Y Value [0.0 \u2013 1.0]", fontsize=10)
ax2_y.set_ylim(-0.08, 1.08)
ax2_y.grid(True, linestyle='--', alpha=0.5)
ax2_y.legend(loc='upper right', fontsize=9, framealpha=0.9)

# Panel 3: X-Axis Calibration
p_x = np.polyfit(x_px, x_vals, 1)
lin_x_px = np.linspace(40, 310, 100)
ax2_x.scatter(x_px, x_vals, color='#D62728', s=65, marker='s', zorder=5, label='OCR Inliers')
ax2_x.plot(lin_x_px, np.polyval(p_x, lin_x_px), color='#D62728', linestyle='--', linewidth=2,
           label=f'RANSAC Fit:\nX = {p_x[0]:.4f}\u00d7px + {p_x[1]:.3f}')
ax2_x.set_title("X-Axis Calibration (RANSAC Consensus)", fontsize=11, fontweight='bold', pad=10)
ax2_x.set_xlabel("Pixel X Position (cx in px)", fontsize=10)
ax2_x.set_ylabel("Physical X Value [0 \u2013 10 min]", fontsize=10)
ax2_x.set_ylim(-0.8, 10.8)
ax2_x.grid(True, linestyle='--', alpha=0.5)
ax2_x.legend(loc='upper left', fontsize=9, framealpha=0.9)

plt.suptitle("Step 1: OCR Detection and Consensus Axis Calibration (Linear RANSAC)", fontsize=13, fontweight='bold', y=0.98)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "step1_ocr_calibration.png"), dpi=180)
plt.close(fig)

print("3. Segmenting curves and generating Step 2: Segmentation figure...")
text_boxes = [item["box"] for item in ocr_items]
curves = segment_image_curves(img_bgr, text_boxes, y_max_limit=y_max_limit)

# Chromatic curves: Blue & Red (the 2 curves from the start)
# Achromatic curve: Black
hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
color_mask = (hsv[:, :, 1] > 50) & (hsv[:, :, 2] > 50)

# Build black extraction sub-steps for visual illustration
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

# Remove text
binary_notext = binary.copy()
for x0, y0, x1, y1 in text_boxes:
    cv2.rectangle(binary_notext, (int(x0) - 5, int(y0) - 5), (int(x1) + 5, int(y1) + 5), 0, -1)

# Remove axes/grid
horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
grid_mask = cv2.dilate(cv2.add(horiz_lines, vert_lines), np.ones((3, 3), np.uint8), iterations=1)
cleaned_morph = cv2.subtract(binary_notext, grid_mask)

# Remove dilated colors
dilated_colors = cv2.dilate(color_mask.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=1)
black_only = cv2.subtract(cleaned_morph, dilated_colors)

# Find curve masks
blue_mask = np.zeros((h, w), dtype=bool)
red_mask = np.zeros((h, w), dtype=bool)
black_mask = np.zeros((h, w), dtype=bool)

for c in curves:
    name = get_closest_color_name(c["color"])
    coords = c["coords"]
    if name == "Blue":
        blue_mask[coords[:, 0], coords[:, 1]] = True
    elif name == "Red":
        red_mask[coords[:, 0], coords[:, 1]] = True
    elif name in ("Black", "Gray", "Unknown"):
        black_mask[coords[:, 0], coords[:, 1]] = True

fig = plt.figure(figsize=(15, 8), dpi=180)
gs = fig.add_gridspec(2, 4, hspace=0.3, wspace=0.2)

# Row 1: The Two Chromatic Curves (Blue & Red) via Cyclic HSV MeanShift
ax_hsv = fig.add_subplot(gs[0, 0])
ax_hsv.imshow(color_mask, cmap='magma')
ax_hsv.set_title("1. Saturated Pixels (S > 50)\nExcludes White/Black/Axes", fontsize=10, fontweight='bold')
ax_hsv.axis('off')

ax_blue = fig.add_subplot(gs[0, 1])
blue_rgb = np.full((h, w, 3), 255, dtype=np.uint8)
blue_rgb[blue_mask] = [40, 70, 240]
ax_blue.imshow(blue_rgb)
ax_blue.set_title("2. Initial Curve A: Blue Curve\n(MeanShift Hue Cluster 1)", fontsize=10, fontweight='bold', color='#1a44c2')
ax_blue.axis('off')

ax_red = fig.add_subplot(gs[0, 2])
red_rgb = np.full((h, w, 3), 255, dtype=np.uint8)
red_rgb[red_mask] = [240, 50, 50]
ax_red.imshow(red_rgb)
ax_red.set_title("3. Initial Curve B: Red Curve\n(MeanShift Hue Cluster 2)", fontsize=10, fontweight='bold', color='#c21a1a')
ax_red.axis('off')

ax_chrom = fig.add_subplot(gs[0, 3])
chrom_overlay = img_rgb.copy()
# Highlight both colored curves
chrom_overlay[~blue_mask & ~red_mask] = (chrom_overlay[~blue_mask & ~red_mask] * 0.25 + 190).astype(np.uint8)
ax_chrom.imshow(chrom_overlay)
ax_chrom.set_title("Two Initial Curves Segmented\n(Chromatic MeanShift Result)", fontsize=10, fontweight='bold')
ax_chrom.axis('off')

# Row 2: Subtractive Morphology for the Black Curve
ax_bin = fig.add_subplot(gs[1, 0])
ax_bin.imshow(binary, cmap='gray')
ax_bin.set_title("4. Raw Dark Pixels (Inv Thresh)\nContains Text, Axes, All Curves", fontsize=10, fontweight='bold')
ax_bin.axis('off')

ax_notext = fig.add_subplot(gs[1, 1])
ax_notext.imshow(binary_notext, cmap='gray')
ax_notext.set_title("5. Text Bounding Boxes Cleared\n(EasyOCR Region Masking)", fontsize=10, fontweight='bold')
ax_notext.axis('off')

ax_grid = fig.add_subplot(gs[1, 2])
ax_grid.imshow(grid_mask, cmap='gray')
ax_grid.set_title("6. Detected Axes & Grids\n(Open 40\u00d71 and 1\u00d740)", fontsize=10, fontweight='bold')
ax_grid.axis('off')

ax_blk = fig.add_subplot(gs[1, 3])
blk_rgb = np.full((h, w, 3), 255, dtype=np.uint8)
blk_rgb[black_mask] = [0, 0, 0]
ax_blk.imshow(blk_rgb)
ax_blk.set_title("7. Isolated Black Trace\n(Subtracted Axes + Color Masks)", fontsize=10, fontweight='bold')
ax_blk.axis('off')

plt.suptitle("Step 2: Multi-Curve Segmentation (Chromatic HSV MeanShift + Subtractive Morphology)", fontsize=13, fontweight='bold', y=0.98)
fig.savefig(os.path.join(OUT_DIR, "step2_curve_segmentation.png"), dpi=180, bbox_inches='tight')
plt.close(fig)

print("4. Generating Step 3: Decoupling Line vs. Experimental Markers figure...")
# Let's illustrate marker & line decoupling on the Red curve and Black curve
curve_target = None
for c in curves:
    if get_closest_color_name(c["color"]) == "Red":
        curve_target = c
        break
if curve_target is None:
    curve_target = curves[0]

line_data, points_data = sample_curve_and_markers(curve_target["coords"], img_bgr.shape, img_bgr)
raw_coords = curve_target["coords"]

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5), dpi=180)

# Panel 1: Raw segmented pixels
raw_canvas = np.full((h, w, 3), 255, dtype=np.uint8)
raw_canvas[raw_coords[:, 0], raw_coords[:, 1]] = [230, 40, 40]
ax1.imshow(raw_canvas)
ax1.set_xlim(raw_coords[:, 1].min() - 8, raw_coords[:, 1].max() + 8)
ax1.set_ylim(raw_coords[:, 0].max() + 8, raw_coords[:, 0].min() - 8)
ax1.set_title("Raw Segmented Trace\n(Line + Superimposed Markers)", fontsize=11, fontweight='bold')
ax1.axis('on')
ax1.tick_params(labelsize=8)

# Panel 2: Isolated experimental dots
ax2.imshow(np.full((h, w, 3), 250, dtype=np.uint8))
if points_data:
    ax2.scatter(points_data[0], points_data[1], facecolors='#E82C2C', edgecolors='black', s=45, linewidths=1.0, zorder=5)
ax2.set_xlim(raw_coords[:, 1].min() - 8, raw_coords[:, 1].max() + 8)
ax2.set_ylim(raw_coords[:, 0].max() + 8, raw_coords[:, 0].min() - 8)
ax2.set_title(f"Decoupled Experimental Points\n({len(points_data[0]) if points_data else 0} dots via NCC & CC analysis)", fontsize=11, fontweight='bold')
ax2.axis('on')
ax2.tick_params(labelsize=8)

# Panel 3: Reconstructed continuous model line
ax3.imshow(np.full((h, w, 3), 250, dtype=np.uint8))
if line_data:
    ax3.plot(line_data[0], line_data[1], color='#E82C2C', linewidth=2.5, label='Savitzky-Golay Smoothed Model')
if points_data:
    ax3.scatter(points_data[0], points_data[1], facecolors='white', edgecolors='#E82C2C', s=35, linewidths=1.2, zorder=5, label='Experimental Points Overlay')
ax3.set_xlim(raw_coords[:, 1].min() - 8, raw_coords[:, 1].max() + 8)
ax3.set_ylim(raw_coords[:, 0].max() + 8, raw_coords[:, 0].min() - 8)
ax3.set_title("Clean Continuous Model Curve\n(Marker Footprint Removal + SG Filter)", fontsize=11, fontweight='bold')
ax3.legend(loc='lower right', fontsize=8.5)
ax3.axis('on')
ax3.tick_params(labelsize=8)

plt.suptitle("Step 3: Decoupling Continuous Model Line and Discrete Experimental Markers", fontsize=13, fontweight='bold', y=0.98)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "step3_trace_decoupling.png"), dpi=180)
plt.close(fig)

print("5. Generating Step 4: Final Reconstruction & Calibration figure...")
# Let's extract all curves with calibrated physical values
extracted_results = []
for c in curves:
    c_name = get_closest_color_name(c["color"])
    l_dat, p_dat = sample_curve_and_markers(c["coords"], img_bgr.shape, img_bgr)
    
    entry = {"name": f"Curve_{c_name}", "color_name": c_name}
    if c_name == "Red":
        entry["hex"] = "#E03636"
    elif c_name == "Blue":
        entry["hex"] = "#2B5EE8"
    else:
        entry["hex"] = "#111111"
        
    if l_dat:
        entry["line_x"] = project_to_axis_units(l_dat[0], x_scale)
        entry["line_y"] = project_to_axis_units(l_dat[1], y_scale)
    if p_dat:
        entry["pts_x"] = project_to_axis_units(p_dat[0], x_scale)
        entry["pts_y"] = project_to_axis_units(p_dat[1], y_scale)
    extracted_results.append(entry)

fig, (ax_orig, ax_plot) = plt.subplots(1, 2, figsize=(14, 6), dpi=180)

# Left: Original image
ax_orig.imshow(img_rgb)
ax_orig.set_title("Original Scanned Image ('test_graph.png')", fontsize=12, fontweight='bold', pad=10)
ax_orig.axis('off')

# Right: Calibrated reconstructed plot
for crv in extracted_results:
    hx = crv["hex"]
    nm = crv["name"]
    if "line_x" in crv:
        ax_plot.plot(crv["line_x"], crv["line_y"], color=hx, linewidth=2.2, label=f"{nm} (Model Line)")
    if "pts_x" in crv:
        is_dark = crv["color_name"] == "Black"
        face = "white" if is_dark else hx
        ew = 1.0 if is_dark else 0.6
        ax_plot.scatter(crv["pts_x"], crv["pts_y"], facecolors=face, edgecolors='black', s=35, linewidths=ew, zorder=5, label=f"{nm} (Exp Points)")

ax_plot.set_title("Calibrated Digital Reconstruction (Physical Units)", fontsize=12, fontweight='bold', pad=10)
ax_plot.set_xlabel("Time (min)", fontsize=11, fontweight='bold')
ax_plot.set_ylabel("X", fontsize=11, fontweight='bold')
ax_plot.set_xlim(-0.3, 10.3)
ax_plot.set_ylim(-0.05, 1.05)
ax_plot.grid(True, linestyle='--', alpha=0.6)
ax_plot.legend(loc='lower right', fontsize=8.5, framealpha=0.95)

plt.suptitle("Step 4: Full Multi-Curve Digital Output (Both Initial Curves + Black Curve)", fontsize=13, fontweight='bold', y=0.98)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "step4_final_reconstruction.png"), dpi=180)
plt.close(fig)

print("6. Generating End-to-End Visual Banner (Pipeline Flow)...")
# A single panoramic flowchart banner showing:
# [Input Graph] -> [OCR & Calibration] -> [Chromatic Curves (Blue + Red)] -> [Achromatic Curve (Black)] -> [Final Calibrated Plot]
fig, axes = plt.subplots(1, 5, figsize=(18, 4), dpi=180)

axes[0].imshow(img_rgb)
axes[0].set_title("1. Input Image\nScanned Figure", fontsize=10, fontweight='bold')
axes[0].axis('off')

# Small OCR overlay
ocr_thumb = img_rgb.copy()
for it in ocr_items:
    x0, y0, x1, y1 = it["box"]
    c = (0, 200, 50) if it["value"] is not None else (255, 140, 0)
    cv2.rectangle(ocr_thumb, (int(x0), int(y0)), (int(x1), int(y1)), c, 2)
axes[1].imshow(ocr_thumb)
axes[1].set_title("2. Axis OCR\n& RANSAC Fit", fontsize=10, fontweight='bold')
axes[1].axis('off')

# The two initial curves
two_curves = np.full((h, w, 3), 255, dtype=np.uint8)
two_curves[blue_mask] = [40, 70, 240]
two_curves[red_mask] = [240, 50, 50]
axes[2].imshow(two_curves)
axes[2].set_title("3. Initial Curves\nBlue + Red (HSV)", fontsize=10, fontweight='bold')
axes[2].axis('off')

# Black curve
black_thumb = np.full((h, w, 3), 255, dtype=np.uint8)
black_thumb[black_mask] = [20, 20, 20]
axes[3].imshow(black_thumb)
axes[3].set_title("4. Black Curve\nMorph. Subtraction", fontsize=10, fontweight='bold')
axes[3].axis('off')

# Final plot preview
axes[4].set_facecolor('#fafafa')
for crv in extracted_results:
    if "line_x" in crv:
        axes[4].plot(crv["line_x"], crv["line_y"], color=crv["hex"], linewidth=1.8)
    if "pts_x" in crv:
        axes[4].scatter(crv["pts_x"], crv["pts_y"], facecolors='white' if crv['color_name'] == 'Black' else crv['hex'],
                        edgecolors='black', s=16, linewidths=0.6)
axes[4].set_title("5. Final Plot\nAll Curves Digitized", fontsize=10, fontweight='bold')
axes[4].set_xlim(-0.5, 10.5)
axes[4].set_ylim(-0.05, 1.05)
axes[4].grid(True, linestyle=':', alpha=0.5)
axes[4].tick_params(labelsize=7)

plt.suptitle("End-to-End Pipeline on 'test_graph': From Scanned Pixels to Calibrated Vector Data", fontsize=12, fontweight='bold', y=0.98)
plt.tight_layout()

# Draw clean directional flow arrows between subplots
fig.canvas.draw()
for i in range(4):
    p1 = axes[i].get_position()
    p2 = axes[i + 1].get_position()
    x_start = p1.x1 + 0.006
    x_end = p2.x0 - 0.006
    y_mid = 0.5 * (p1.y0 + p1.y1)
    arrow = patches.FancyArrowPatch(
        (x_start, y_mid), (x_end, y_mid),
        transform=fig.transFigure,
        arrowstyle='simple,head_length=8,head_width=8,tail_width=2.5',
        facecolor='#2B5EE8', edgecolor='none', zorder=20
    )
    fig.add_artist(arrow)

fig.savefig(os.path.join(OUT_DIR, "pipeline_workflow_banner.png"), dpi=180)
plt.close(fig)

print("All figures generated successfully in docs/images/!")
