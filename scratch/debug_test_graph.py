import cv2, os, sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
import matplotlib.pyplot as plt
from main import calibrate_axes, extract_curve_legends, segment_image_curves, sample_curve_and_markers, project_to_axis_units

img = cv2.imread('images/test_graph.png')
x_scale, y_scale, ocr_items = calibrate_axes(img)
print('x_scale:', x_scale)
print('y_scale:', y_scale)
for item in ocr_items:
    print('OCR item:', item['text'], 'val:', item['value'], 'box:', item['box'])
 
legends = extract_curve_legends(img, ocr_items)
print('Legends:', legends)

raw_y_scale = y_scale
y_max_limit = int(max(raw_y_scale[0], raw_y_scale[2]) + 6) if raw_y_scale is not None else None
curves = segment_image_curves(img, [item['box'] for item in ocr_items], y_max_limit=y_max_limit)
print('Number of curves found:', len(curves))
for idx, c in enumerate(curves):
    coords = c['coords']
    print(f'Curve {idx}: color={c["color"]}, nb_pixels={len(coords)}, x_min={coords[:,1].min()}, x_max={coords[:,1].max()}, y_min={coords[:,0].min()}, y_max={coords[:,0].max()}')
    line_data, points_data = sample_curve_and_markers(coords, img.shape, img)
    if line_data:
        lx, ly = line_data
        print(f'   Line: len={len(lx)}, x_min={lx.min()}, x_max={lx.max()}, y_min={ly.min()}, y_max={ly.max()}')
        if x_scale:
            px = project_to_axis_units(lx, x_scale)
            py = project_to_axis_units(ly, y_scale)
            print(f'   Calib Line: px_min={px.min():.2f}, px_max={px.max():.2f}, py_min={py.min():.2f}, py_max={py.max():.2f}')
    else:
        print('   No Line')
    if points_data:
        ptx, pty = points_data
        print(f'   Points: len={len(ptx)}, x_min={ptx.min()}, x_max={ptx.max()}, y_min={pty.min()}, y_max={pty.max()}')
        if x_scale:
            ppx = project_to_axis_units(ptx, x_scale)
            ppy = project_to_axis_units(pty, y_scale)
            print(f'   Calib Points: ppx_min={ppx.min():.2f}, ppx_max={ppx.max():.2f}, ppy_min={ppy.min():.2f}, ppy_max={ppy.max():.2f}')
            print(f'   Calib Points values: X={np.round(ppx, 1)[:10]}...')
            print(f'   Calib Points values: Y={np.round(ppy, 3)[:10]}...')
    else:
        print('   No Points')
