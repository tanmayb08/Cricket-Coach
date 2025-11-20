import streamlit as st
import os
import sys
import subprocess
import time
import glob
import shutil
from pathlib import Path
import runpy

# ----------------------------
# Configuration / paths
# ----------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
UPLOAD_PATH = DATA_DIR / "sample.mp4"   # where uploaded file will be saved
SRC_PIPELINE = ROOT / "src" / "pipeline.py"
OUTPUTS_DIR = ROOT / "outputs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Crick Coach - Frontend", layout="centered")

st.title("Crick Coach — Video Upload & Analysis")
st.write("Upload a cricket video, then run the pipeline to generate heatmaps, wagon wheels, trajectories, etc.")

# ----------------------------
# File uploader
# ----------------------------
uploaded_file = st.file_uploader("Upload a video (mp4 / mov / mkv / webm)", type=["mp4","mov","avi","mkv","webm"], accept_multiple_files=False)

if uploaded_file is not None:
    # Save uploaded file to data/sample.mp4 (overwrite)
    try:
        with open(UPLOAD_PATH, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)
        st.success(f"Saved uploaded video to `{UPLOAD_PATH}`")
        st.video(str(UPLOAD_PATH))
    except Exception as e:
        st.error(f"Failed to save uploaded file: {e}")
        st.stop()
else:
    # If sample already exists, show it
    if UPLOAD_PATH.exists():
        st.info("Using existing `data/sample.mp4`")
        st.video(str(UPLOAD_PATH))

# ----------------------------
# Buttons to run pipeline
# ----------------------------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    run_pipeline_btn = st.button("Run pipeline.py (Heatmap/WagonWheel / Trajectory / Detection)")
with col2:
    run_pipeline_bg_btn = st.button("Run pipeline (in new process)")

# A small helper to display output files
def show_outputs():
    files = sorted(OUTPUTS_DIR.glob("*"))
    if not files:
        st.info("No output files found in the `outputs/` folder yet.")
        return
    st.success(f"Found {len(files)} output file(s) in `outputs/`")
    # Show images first (png/jpg), then other files as downloads
    image_exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
    for p in files:
        try:
            if p.suffix.lower() in image_exts:
                st.image(str(p), caption=p.name, use_column_width=True)
                st.download_button(label=f"Download {p.name}", data=open(p, "rb").read(), file_name=p.name)
            else:
                st.write(p.name)
                st.download_button(label=f"Download {p.name}", data=open(p, "rb").read(), file_name=p.name)
        except Exception as e:
            st.write("Could not display", p.name, e)

# ----------------------------
# Run pipeline: helper functions
# ----------------------------
def run_pipeline_in_process(pipeline_path: Path, video_path: Path, session_write=None):
    """
    Try to execute pipeline.py within this Python process (runpy).
    This will execute the script as if __main__, with sys.argv adjusted.
    If pipeline.py is written to be imported, you may prefer to import and call a function.
    """
    old_argv = sys.argv[:]
    sys.argv = [str(pipeline_path), str(video_path)]
    try:
        # runpy.run_path will run the given script as __main__
        # It may print to stdout/stderr; we can't fully capture that easily without redirecting.
        runpy.run_path(str(pipeline_path), run_name="__main__")
        return True, "Pipeline executed in-process."
    except Exception as e:
        return False, f"In-process run failed: {e}"
    finally:
        sys.argv = old_argv

def run_pipeline_subprocess(pipeline_path: Path, video_path: Path):
    """
    Run pipeline as a subprocess using the current Python interpreter.
    Captures stdout/stderr and returns them.
    """
    cmd = [sys.executable, str(pipeline_path), str(video_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    success = proc.returncode == 0
    return success, proc.stdout + ("\n\nSTDERR:\n" + proc.stderr if proc.stderr else "")

# ----------------------------
# Execution logic
# ----------------------------
if run_pipeline_btn:
    if not UPLOAD_PATH.exists():
        st.error("No `data/sample.mp4` found. Upload a video first.")
    else:
        st.info("Running `src/pipeline.py` (in-process). If this hangs or fails, try 'Run pipeline (in new process)' button.")
        with st.spinner("Running pipeline (in-process)... this may take a while depending on your model and CPU/GPU"):
            # First try to run in-process (preferable if pipeline imports local modules)
            ok, out = run_pipeline_in_process(SRC_PIPELINE, UPLOAD_PATH)
            if ok:
                st.success("Pipeline finished (in-process).")
                st.text(out)
            else:
                st.warning("In-process execution failed; trying subprocess fallback.")
                ok2, out2 = run_pipeline_subprocess(SRC_PIPELINE, UPLOAD_PATH)
                if ok2:
                    st.success("Pipeline finished (subprocess).")
                    st.text(out2)
                else:
                    st.error("Pipeline failed (subprocess). See logs below.")
                    st.text(out2)
        # Show outputs after running
        st.markdown("### Pipeline outputs")
        show_outputs()

if run_pipeline_bg_btn:
    if not UPLOAD_PATH.exists():
        st.error("No `data/sample.mp4` found. Upload a video first.")
    else:
        st.info("Running `src/pipeline.py` as subprocess. Logs will appear after completion.")
        with st.spinner("Running pipeline in subprocess..."):
            ok, out = run_pipeline_subprocess(SRC_PIPELINE, UPLOAD_PATH)
            if ok:
                st.success("Pipeline subprocess finished successfully.")
                st.text(out)
            else:
                st.error("Pipeline subprocess failed. See logs below.")
                st.text(out)
        st.markdown("### Pipeline outputs")
        show_outputs()

# Always show current outputs (so user can browse)
st.markdown("---")
st.header("Outputs (folder)")
show_outputs()

st.markdown("<small>Note: This frontend runs your `src/pipeline.py` directly. If your pipeline requires GPU/large models, run this on a machine with appropriate resources. If pipeline takes long, consider converting it to an async job queue (Celery/RQ) and poll for results.</small>", unsafe_allow_html=True)
