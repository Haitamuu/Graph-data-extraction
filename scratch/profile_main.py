import cProfile
import pstats
from main import process_image
import os

img_path = "images/test_graph.png"
if os.path.exists(img_path):
    print("Profiling process_image...")
    profiler = cProfile.Profile()
    profiler.enable()
    process_image(img_path)
    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(20)
else:
    print("Image not found")
