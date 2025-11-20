import os
import numpy as np
import torch
import ultralytics.nn.tasks as tasks
from ultralytics import YOLO

# ✅ Fix PyTorch 2.6 unpickling issues
torch.serialization.add_safe_globals([
    tasks.DetectionModel,                # YOLO model
    torch.nn.modules.container.Sequential,  # standard Sequential
    torch.nn.Conv2d,
    torch.nn.BatchNorm2d,
    torch.nn.ReLU,
    torch.nn.SiLU,
    torch.nn.MaxPool2d,
    torch.nn.AdaptiveAvgPool2d,
    torch.nn.Linear,
])


MODEL_NAME = "yolov8n.pt"

def run_tracking(video_path, project="outputs", name="track"):
    """
    Run YOLOv8 tracking on input video.
    Saves annotated video to outputs/project/name.
    """
    model = YOLO(MODEL_NAME)
    model.track(source=video_path, tracker="bytetrack.yaml", imgsz=640, conf=0.25,
                save=True, project=project,classes=[32], name=name)
    # find annotated file
    out_dir = os.path.join(project, name)
    for f in os.listdir(out_dir):
        if f.endswith(".mp4"):
            return os.path.join(out_dir, f)
    return None

def extract_tracks(video_path):
    """
    Return per-frame ball/player tracks with id, cls, and coordinates.
    """
    model = YOLO(MODEL_NAME)
    tracks = []
    for i, r in enumerate(model.track(source=video_path, stream=True,
                                      tracker="bytetrack.yaml", imgsz=640, conf=0.25)):
        if not r.boxes: 
            continue
        frame_no = getattr(r, "frame", i)
        boxes = r.boxes
        cls = boxes.cls.cpu().numpy().astype(int)
        xyxy = boxes.xyxy.cpu().numpy()
        ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else np.arange(len(cls))
        for c, tid, bb in zip(cls, ids, xyxy):
            x1,y1,x2,y2 = bb
            cx, cy = float((x1+x2)/2), float((y1+y2)/2)
            tracks.append({"frame": int(frame_no), "id": int(tid), "cls": int(c), "cx": cx, "cy": cy})
    return tracks
