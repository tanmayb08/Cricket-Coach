import cv2
import numpy as np
from ultralytics import YOLO

MODEL_NAME = "yolov8n.pt"   # still COCO, we’ll only use it for persons/stumps

def detect_pitch_area(frame, model):
    """Use YOLO to detect players/stumps, then crop pitch region around them."""
    results = model(frame)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    cls = results[0].boxes.cls.cpu().numpy().astype(int)
    
    persons = [b for b,c in zip(boxes,cls) if c==0]  # 0=person
    if not persons:
        return frame, (0,0,frame.shape[1],frame.shape[0])  # full frame

    # take bounding box covering all persons
    x1 = int(min([p[0] for p in persons]))
    y1 = int(min([p[1] for p in persons]))
    x2 = int(max([p[2] for p in persons]))
    y2 = int(max([p[3] for p in persons]))
    
    # expand slightly to cover pitch area
    pad = 50
    x1 = max(0,x1-pad); y1=max(0,y1-pad)
    x2 = min(frame.shape[1],x2+pad); y2=min(frame.shape[0],y2+pad)

    return frame[y1:y2, x1:x2], (x1,y1,x2,y2)


def track_ball(video_path, out_path="outputs/ball_tracking.mp4"):
    model = YOLO(MODEL_NAME)

    cap = cv2.VideoCapture(video_path)
    w,h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (w,h))

    ret, prev_frame = cap.read()
    if not ret: return None

    # detect pitch ONCE → lock ROI
    pitch_prev, roi = detect_pitch_area(prev_frame, model)
    prev_gray = cv2.cvtColor(pitch_prev, cv2.COLOR_BGR2GRAY)

    ball_pos = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # use the SAME ROI as before
        x1,y1,x2,y2 = roi
        pitch = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(pitch, cv2.COLOR_BGR2GRAY)

        # resize to same size as prev_gray
        if gray.shape != prev_gray.shape:
            gray = cv2.resize(gray, (prev_gray.shape[1], prev_gray.shape[0]))

        # optical flow
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray,
                                            None, 0.5, 3, 15, 3, 5, 1.2, 0)

        mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
        motion_mask = (mag > 5).astype(np.uint8)*255

        contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            (x,y,wc,hc) = cv2.boundingRect(c)
            cx,cy = x+wc//2, y+hc//2
            ball_pos = (cx+x1, cy+y1)   # add offset back to full frame
            cv2.circle(frame, ball_pos, 8, (0,0,255), -1)

        out.write(frame)
        prev_gray = gray.copy()

    cap.release()
    out.release()
    return out_path
