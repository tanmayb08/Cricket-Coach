import sys
from src.pipeline import run_full_pipeline
from src.ball_tracker import track_ball




if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    results = run_full_pipeline(video_path)

    #newly added code
    '''out = track_ball(video_path)
    print("Ball tracking video saved:", out)'''

    print("=== Results ===")
    print("Annotated video:", results["annotated_video"])
    print("Heatmap:", results["bowling_heatmap"])
    print("Wagon wheel:", results["wagon_wheel"])
    print("Insights:", results["insights"])
