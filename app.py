from flask import Flask, render_template, request, redirect, url_for, flash
import os
from pipeline import *
from werkzeug.utils import secure_filename
import secrets
import time
from flask import jsonify, send_from_directory
import subprocess


UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_PHOTOS_DEST']='outputs'
app.secret_key = secrets.token_hex(32)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    # list uploaded files to show recently uploaded preview (optional)
    uploads = sorted(os.listdir(app.config['UPLOAD_FOLDER']), reverse=True)
    return render_template('index.html', uploads=uploads)


#Heatmap and wagon wheel detection function
def draw_heat_wagon():
    mainfn()


# @app.route('/upload', methods=['POST'])
# def upload():
#     # Expect form field name 'video'
#     if 'video' not in request.files:
#         flash('No file part in the request')
#         return redirect(url_for('index'))

#     file = request.files['video']
#     if file.filename == '':
#         flash('No selected file')
#         return redirect(url_for('index'))

#     if file and allowed_file(file.filename):
#         filename = "sample.mp4"
#         save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

#         file.save(save_path)
#         flash(f'Uploaded: {filename}')
#         # Keep your backend pipeline: you can call your processing function here
#         return redirect(url_for('index'))

#     else:
#         flash('Unsupported file type')
#         return redirect(url_for('index'))

@app.route('/upload', methods=['GET','POST'])
def upload():
    if 'video' not in request.files:
        flash('No file part in the request')
        return redirect(url_for('index'))

    file = request.files['video']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    # Force save as sample.mp4
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample.mp4')

    if file:
        file.save(save_path)
        flash('Video saved as sample.mp4')
        # If you want to trigger your processing pipeline, call it here:
        # process_video(save_path)
        return redirect(url_for('index'))

    flash('Upload failed')
    return redirect(url_for('index'))

# For Button

SAMPLE_NAME = 'sample.mp4'
SAMPLE_PATH = os.path.join(app.config['UPLOAD_FOLDER'], SAMPLE_NAME)

@app.route('/sample_exists', methods=['GET'])
def sample_exists():
    """
    Quick endpoint frontend uses to check whether sample.mp4 exists on server.
    Returns JSON with a direct static URL if exists.
    """
    if os.path.exists(SAMPLE_PATH):
        url = url_for('static', filename=f'uploads/{SAMPLE_NAME}')
        return jsonify({'exists': True, 'url': url})
    return jsonify({'exists': False})

# Placeholder analysis functions - replace with actual pipeline calls
def analyze_heat_wagon(video_path):
    """
    Run heatmap + wagon wheel analysis on 'video_path'.
    Replace with your real code. Should produce outputs (images or json) in static/outputs/.
    For now, simulate work and return a result path or message.
    """
    # Simulate processing time
    time.sleep(2)  # remove in real pipeline
    # Suppose you produce 'heatmap.png' and 'wagon_wheel.png' in static/outputs/
    outputs_dir = os.path.join('static', 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    # Here you'd run the real code and write outputs
    heatmap_path = os.path.join(outputs_dir, 'heatmap.png')
    wagon_path = os.path.join(outputs_dir, 'wagon_wheel.png')
    # For now just touch files if they don't exist so frontend can open them
    for p in (heatmap_path, wagon_path):
        if not os.path.exists(p):
            open(p, 'wb').close()
    return {'message': 'Heatmap and wagon wheel generated', 'result_url': url_for('static', filename='outputs/heatmap.png')}

def analyze_trajectory_and_person(video_path):
    """
    Run trajectory + on-field person detection.
    Replace with your real code.
    """
    time.sleep(2)  # simulate processing
    outputs_dir = os.path.join('static', 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    traj_path = os.path.join(outputs_dir, 'trajectory.png')
    people_path = os.path.join(outputs_dir, 'people_detect.png')
    for p in (traj_path, people_path):
        if not os.path.exists(p):
            open(p, 'wb').close()
    return {'message': 'Trajectory and person detection results ready', 'result_url': url_for('static', filename='outputs/trajectory.png')}

# API endpoints triggered by frontend buttons
# @app.route('/analyze/heatwagon', methods=['POST'])
# def analyze_heatwagon():
#     if not os.path.exists(SAMPLE_PATH):
#         return jsonify({'status': 'error', 'message': 'sample.mp4 not found on server'}), 400

#     # Call your heavy processing function here:
#     try:
#         result = analyze_heat_wagon(SAMPLE_PATH)
#         return jsonify({'status': 'ok', 'message': result.get('message'), 'result_url': result.get('result_url')})
#     except Exception as e:
#         app.logger.exception('Heat/wagon analysis failed')
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# @app.route('/analyze/trajectory', methods=['POST'])
# def analyze_trajectory():
#     if not os.path.exists(SAMPLE_PATH):
#         return jsonify({'status': 'error', 'message': 'sample.mp4 not found on server'}), 400

#     try:
#         result = analyze_trajectory_and_person(SAMPLE_PATH)
#         return jsonify({'status': 'ok', 'message': result.get('message'), 'result_url': result.get('result_url')})
#     except Exception as e:
#         app.logger.exception('Trajectory analysis failed')
#         return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/outputs/<filename>')
def get_file2(filename):
    return send_from_directory(app.config['RESULT_PHOTOS_DEST'], filename)

@app.route('/heatwagon', methods=['GET','POST'])
def analyze_heatwagon():
    if not os.path.exists(SAMPLE_PATH):
        return jsonify({'status': 'error', 'message': 'sample.mp4 not found'}), 400
    try:
        # Run your actual script
        # subprocess.run(["python", "src/analyze_heatwagon.py", SAMPLE_PATH], check=True)
        # subprocess.run(["python", "pipeline.py", SAMPLE_PATH], check=True)
        # Assume script saves heatmap.png in static/outputs/
        draw_heat_wagon()
        print("heatmap done")
        # return jsonify({
        #     'status': 'ok',
        #     'message': 'Heatmap & Wagon Wheel analysis complete',
        #     'result_url': url_for('static', filename='outputs/heatmap.png')
        # })
        file_url = url_for('get_file2' , filename='pitch_heatmap.png')
        return render_template('result.html', file_url = file_url)
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Analysis failed: {e}'}), 500


@app.route('/analyze/trajectory', methods=['POST'])
def analyze_trajectory():
    if not os.path.exists(SAMPLE_PATH):
        return jsonify({'status': 'error', 'message': 'sample.mp4 not found'}), 400
    try:
        subprocess.run(["python", "analyze_trajectory.py", SAMPLE_PATH], check=True)
        return jsonify({
            'status': 'ok',
            'message': 'Trajectory & On-field Detection complete',
            'result_url': url_for('static', filename='outputs/trajectory.png')
        })
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Analysis failed: {e}'}), 500


# Button End



if __name__ == '__main__':
    app.run(debug=True)
