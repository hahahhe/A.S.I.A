from flask import Blueprint, Response, jsonify, request, current_app, url_for, send_from_directory
import io
import os
from werkzeug.utils import secure_filename
import traceback

from services.detection import perform_detection_and_labeling
from services.video import add_audio_to_video, merge_audio_files

video_bp = Blueprint("video", __name__)

@video_bp.route('/upload/video', methods=['POST'])
def upload_video():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일 부분이 없습니다'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '선택된 파일이 없습니다'}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)

        video_url = url_for('video.uploaded_file', filename=filename)
        
        return jsonify({'original_video_url': video_url, 'filename': filename})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/process/labels', methods=['POST'])
def process_labels():
    try:
        data = request.json
        # 클라이언트로부터 original_video_url 받기
        filename = data['filename']
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # 비디오에서 객체 탐지 및 라벨링
        labeled_video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'labeled_{filename}')
        class_durations, capture_images = perform_detection_and_labeling(file_path, labeled_video_path)

        # 처리 결과를 JSON 형태로 반환
        return jsonify({
            "labeled_video_url": url_for('video.uploaded_file', filename=f'labeled_{filename}'),
            "labeled_video_path": labeled_video_path,
            "class_durations": class_durations,
            "capture_images": capture_images
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    

@video_bp.route('/finalize/video', methods=['POST'])
def finalize_video():
    try:
        data = request.json
        labeled_video_path = data['labeled_video_path']
        print('final_label: ', labeled_video_path)
        audio_clips_info = data['audio_clips_info']
        print('final_audio: ', audio_clips_info)
        final_video_path = add_audio_to_video(labeled_video_path, audio_clips_info)

        return jsonify({
            'final_video_url': url_for('video.uploaded_file', filename=os.path.basename(final_video_path))
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@video_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    # 업로드된 파일 제공
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@video_bp.route('/merge', methods=['POST'])
def merge_audio():
    data = request.json
    audio_files = data['audio_files']  

    output_path = merge_audio_files(audio_files)

    return jsonify({"success": True, "output": output_path})