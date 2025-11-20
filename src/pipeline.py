import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import json
from ultralytics import YOLO

MODEL_NAME = "yolov8n.pt"   # pre-trained YOLOv8

OUT_DIR = "outputs"

def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)

os.makedirs(OUT_DIR, exist_ok=True)

# def track_ball(video_path):
#     cap = cv2.VideoCapture(video_path)
#     w,h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#     out = cv2.VideoWriter(os.path.join(OUT_DIR, "ball_tracking.mp4"), fourcc, fps, (w,h))

#     model = YOLO(MODEL_NAME)

#     ret, prev_frame = cap.read()
#     if not ret: return None, []

#     prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

#     ball_positions = []
#     frame_idx = 0

#     while True:
#         ret, frame = cap.read()
#         if not ret: break

#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         # resize to match prev_gray if needed
#         if gray.shape != prev_gray.shape:
#             gray = cv2.resize(gray, (prev_gray.shape[1], prev_gray.shape[0]))

#         # Optical Flow
#         flow = cv2.calcOpticalFlowFarneback(prev_gray, gray,
#                                             None, 0.5, 3, 15, 3, 5, 1.2, 0)
#         mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
#         motion_mask = (mag > 5).astype(np.uint8) * 255

#         contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         ball_pos = None
#         if contours:
#             c = max(contours, key=cv2.contourArea)
#             x,y,wc,hc = cv2.boundingRect(c)
#             ball_pos = (x + wc//2, y + hc//2)
#             cv2.circle(frame, ball_pos, 8, (0,0,255), -1)

#         ball_positions.append((frame_idx, ball_pos))
#         out.write(frame)
#         prev_gray = gray.copy()
#         frame_idx += 1

#     cap.release()
#     out.release()
#     print("✅ Annotated video saved at outputs/ball_tracking.mp4")
#     return ball_positions

def track_ball(video_path):
    """
    Tracks a ball in a video using YOLOv8 and saves an annotated video.
    Returns the annotated video path and the ball's positions over time.

    Args:
        video_path (str): The path to the input video file.

    Returns:
        tuple: A tuple containing the path to the annotated video and
               a list of tuples with (frame_idx, (x, y)) coordinates of the ball.
    """
    model = YOLO(MODEL_NAME)
    project = "outputs"
    name = "track"

    # Run tracking and save the annotated video
    results_generator = model.track(
        source=video_path,
        tracker="bytetrack.yaml",
        imgsz=640,
        conf=0.25,
        save=True,
        project=project,
        classes=[32],
        name=name,
        stream=True
    )

    ball_positions = []
    annotated_video_path = None
    
    # Process the streamed results to get ball positions and the video path
    for i, r in enumerate(results_generator):
        # Determine the annotated video path from the first result object
        if annotated_video_path is None and r.save_dir:
            annotated_video_path = os.path.join(r.save_dir, os.path.basename(video_path))
        
        # Extract ball positions if detections exist
        if r.boxes and r.boxes.id is not None:
            boxes = r.boxes
            cls = boxes.cls.cpu().numpy().astype(int)
            ids = boxes.id.cpu().numpy().astype(int)
            xyxy = boxes.xyxy.cpu().numpy()
            
            for c, tid, bb in zip(cls, ids, xyxy):
                # Check for the ball class (class ID 32)
                if c == 32:
                    x1, y1, x2, y2 = bb
                    cx, cy = float((x1 + x2) / 2), float((y1 + y2) / 2)
                    ball_positions.append((i, (int(cx), int(cy))))
                    
    if annotated_video_path:
        print(f"✅ Annotated video saved at {annotated_video_path}")
    else:
        print("❌ Failed to generate annotated video.")

    return ball_positions

# def make_heatmap(ball_positions):
#     xs = [p[1][0] for p in ball_positions if p[1] is not None]
#     ys = [p[1][1] for p in ball_positions if p[1] is not None]

#     plt.figure(figsize=(6,8))
#     heatmap, xedges, yedges = np.histogram2d(xs, ys, bins=(100,100))
#     plt.imshow(heatmap.T, origin="lower", cmap="hot", interpolation="nearest")
#     plt.colorbar()
#     plt.title("Ball Heatmap")
#     heatmap_path = os.path.join(OUT_DIR, "heatmap.png")
#     plt.savefig(heatmap_path)
#     plt.close()
#     print(f"✅ Heatmap saved at {heatmap_path}")

# def make_pitch_heatmap(ball_positions, frame_shape=(360, 640)):
#     # Pitch region (adjust based on your video scaling)
#     PITCH_X1, PITCH_X2 = 200, 440
#     PITCH_Y1, PITCH_Y2 = 100, 280

#     # Collect only ball positions inside pitch
#     valid_positions = [
#         p[1] for p in ball_positions if p[1] is not None
#         and PITCH_X1 <= p[1][0] <= PITCH_X2
#         and PITCH_Y1 <= p[1][1] <= PITCH_Y2
#     ]

#     if len(valid_positions) == 0:
#         print("⚠️ No ball positions inside pitch")
#         return

#     heatmap = np.zeros((frame_shape[0], frame_shape[1]), dtype=np.float32)

#     for (x, y) in valid_positions:
#         if 0 <= int(y) < frame_shape[0] and 0 <= int(x) < frame_shape[1]:
#             heatmap[int(y), int(x)] += 1

#     heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
#     heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
#     heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

#     # Draw pitch boundary on heatmap
#     cv2.rectangle(
#         heatmap_color, (PITCH_X1, PITCH_Y1), (PITCH_X2, PITCH_Y2),
#         (255, 255, 255), 2
#     )

#     heatmap_path = os.path.join(OUT_DIR, "pitch_heatmap.png")
#     cv2.imwrite(heatmap_path, heatmap_color)
#     print(f"✅ Pitch Heatmap saved at {heatmap_path}")

def make_pitch_heatmap(ball_positions, frame_shape=(360, 640), config_path="config.json"):
    # Load config
    config = load_config(config_path)
    pitch = config["pitch"]
    PITCH_X1, PITCH_X2 = pitch["x1"], pitch["x2"]
    PITCH_Y1, PITCH_Y2 = pitch["y1"], pitch["y2"]

    # Filter only positions inside pitch
    valid_positions = [
        p[1] for p in ball_positions if p[1] is not None
        and PITCH_X1 <= p[1][0] <= PITCH_X2
        and PITCH_Y1 <= p[1][1] <= PITCH_Y2
    ]

    if len(valid_positions) == 0:
        print("⚠️ No ball positions inside pitch")
        return

    heatmap = np.zeros((frame_shape[0], frame_shape[1]), dtype=np.float32)

    for (x, y) in valid_positions:
        if 0 <= int(y) < frame_shape[0] and 0 <= int(x) < frame_shape[1]:
            heatmap[int(y), int(x)] += 1

    heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
    heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
    heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    # Draw pitch boundary
    cv2.rectangle(
        heatmap_color, (PITCH_X1, PITCH_Y1), (PITCH_X2, PITCH_Y2),
        (255, 255, 255), 2
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    heatmap_path = os.path.join(OUT_DIR, "pitch_heatmap.png")
    cv2.imwrite(heatmap_path, heatmap_color)
    print(f"✅ Pitch Heatmap saved at {heatmap_path}")

# def make_wagon_wheel(ball_positions):
#     valid_positions = [p[1] for p in ball_positions if p[1] is not None]
#     if len(valid_positions) < 2:
#         print("⚠️ Not enough ball positions for wagon wheel")
#         return
#     origin = valid_positions[0]
#     angles = []
#     for x,y in valid_positions:
#         dx, dy = x - origin[0], y - origin[1]
#         angle = math.degrees(math.atan2(dy, dx))
#         angles.append(angle)

#     plt.figure(figsize=(5,5))
#     plt.hist(angles, bins=36, range=(-180,180), color="green", alpha=0.7)
#     plt.title("Wagon Wheel")
#     plt.xlabel("Angle (degrees)")
#     plt.ylabel("Count")
#     wagon_path = os.path.join(OUT_DIR, "wagon_wheel.png")
#     plt.savefig(wagon_path)
#     plt.close()
#     print(f"✅ Wagon Wheel saved at {wagon_path}")

def make_wagon_wheel(ball_positions):
    valid_positions = [p[1] for p in ball_positions if p[1] is not None]
    if len(valid_positions) < 2:
        print("⚠️ Not enough ball positions for wagon wheel")
        return
    
    # Take first ball position as "batsman"
    origin = valid_positions[0]
    angles = []
    for x,y in valid_positions:
        dx, dy = x - origin[0], y - origin[1]
        angle = math.atan2(dy, dx)  # radians
        angles.append(angle)

    # Convert angles to radians for polar plot
    angles = np.array(angles)
    radii = np.ones_like(angles)  # just give each shot length 1 (equal weight)

    plt.figure(figsize=(6,6), facecolor="white")
    ax = plt.subplot(111, polar=True)
    ax.set_theta_zero_location("N")   # 0° = top (like cricket pitch)
    ax.set_theta_direction(-1)        # clockwise

    ax.scatter(angles, radii, c="green", s=50, alpha=0.75)

    # Optional: add radial grid (represents field)
    ax.set_rticks([])
    ax.set_title("Wagon Wheel", va="bottom")

    wagon_path = os.path.join(OUT_DIR, "wagon_wheel.png")
    plt.savefig(wagon_path, bbox_inches="tight")
    plt.close()
    print(f"✅ Wagon Wheel saved at {wagon_path}")


# 


# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("Usage: python pipeline.py <video_path>")
#         sys.exit(1)
    # video_path = sys.argv[1]
if __name__ == "__main__":
    video_path = "static/uploads/sample.mp4"
    ball_positions = track_ball(video_path)
    #make_heatmap(ball_positions)
    make_pitch_heatmap(ball_positions)
    make_wagon_wheel(ball_positions)
