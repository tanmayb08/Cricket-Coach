import numpy as np
import cv2

def detect_ball_positions(tracks):
    """Filter YOLO tracks for sports ball class (id=32)."""
    return [(t["frame"], t["cx"], t["cy"]) for t in tracks if t["cls"] == 32]

def compute_bounces(points):
    """Find local minima in y trajectory (bounce points)."""
    if not points:
        return []
    points = sorted(points, key=lambda x: x[0])
    ys = np.array([p[2] for p in points])
    kernel = np.ones(5) / 5
    ys_s = np.convolve(ys, kernel, mode="same")
    bounces = []
    for i in range(2, len(ys_s)-2):
        if ys_s[i] < ys_s[i-1] and ys_s[i] < ys_s[i+1]:
            bounces.append((points[i][0], points[i][1], points[i][2]))
    return bounces

def classify_length(y, H):
    """Classify delivery length based on bounce Y position."""
    if y < H*0.35: return "full/yorker"
    if y < H*0.55: return "good length"
    return "short"
