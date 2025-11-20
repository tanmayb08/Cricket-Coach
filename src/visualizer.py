import os
import math
import matplotlib.pyplot as plt

def plot_heatmap(points, out_path, bins=(30,30)):
    if not points: return None
    xs=[p[0] for p in points]; ys=[p[1] for p in points]
    plt.figure(figsize=(4,6))
    plt.hist2d(xs, ys, bins=bins)
    plt.gca().invert_yaxis()
    plt.colorbar(); plt.title("Bowling Heatmap")
    plt.savefig(out_path); plt.close()
    return out_path

def compute_wagon_wheel(vectors, out_path):
    if not vectors:
        plt.figure(); plt.text(0.5,0.5,"No shots", ha="center"); plt.axis("off")
        plt.savefig(out_path); plt.close()
        return out_path
    angles = [math.degrees(math.atan2(dy, dx)) for dx,dy in vectors]
    plt.figure(figsize=(5,5))
    plt.hist(angles, bins=12)
    plt.title("Wagon Wheel (shot angles)")
    plt.savefig(out_path); plt.close()
    return out_path
