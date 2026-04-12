from flask import Blueprint, request, jsonify, current_app, url_for
#from services.video_service import process_video
import os
from werkzeug.utils import secure_filename
from services.video_service import perform_detection_and_labeling
import config
import moviepy.editor as mp
import math

video_bp = Blueprint('video', __name__)

@video_bp.route('/upload/video', methods=['POST'])
def upload_video():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일 부분이 없습니다'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '선택된 파일이 없습니다'}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)
        os.makedirs(video_bp.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)

        video_url = url_for('uploaded_file', filename=filename)
        
        return jsonify({'original_video_url': video_url, 'filename': filename})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/process/labels', methods=['POST'])
def process_labels():
    try:
        data = request.json
        # 클라이언트로부터 original_video_url 받기
        filename = data['filename']
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)

        # 비디오에서 객체 탐지 및 라벨링
        labeled_video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'labeled_{filename}')
        class_durations, capture_images = perform_detection_and_labeling(file_path, labeled_video_path)

        # 처리 결과를 JSON 형태로 반환
        return jsonify({
            "labeled_video_url": url_for('uploaded_file', filename=f'labeled_{filename}'),
            "labeled_video_path": labeled_video_path,
            "class_durations": class_durations,
            "capture_images": capture_images
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@video_bp.route('/merge', methods=['POST'])
def merge_audio():
    data = request.json
    audio_files = data['audio_files']  # 오디오 파일 정보
    
    # 오디오 파일 정보 출력
    for audio in audio_files:
        print(f"File: {audio['file']}, Start: {audio['start']}, End: {audio['end']}")

    # 비디오 파일 경로 정의
    video_file = 'uploads/final.mp4'
    video_clip = mp.VideoFileClip(video_file)  # 비디오 클립 정의

    audio_clips = []  # 오디오 클립을 저장할 리스트

    for audio in audio_files:
        # 'List' 폴더와 'uploads' 폴더에서 오디오 파일 경로 찾기
        audio_path_list = [f"uploads/{audio['file']}", f"effects/{audio['file']}", f"saved_audios/{audio['file']}"]
        audio_path = next((path for path in audio_path_list if os.path.exists(path)), None)

        if audio_path is None:
            print(f"Audio file not found: {audio['file']}")
            continue

        original_audio_clip = mp.AudioFileClip(audio_path)
        audio_duration = original_audio_clip.duration

        # 오디오 클립을 반복하여 적절한 길이로 만듭니다.
        repeat_count = math.ceil((audio['end'] - audio['start']) / audio_duration)
        repeated_audio_clip = mp.concatenate_audioclips([original_audio_clip] * repeat_count)

        # 총 길이를 오디오 클립 길이로 조정합니다.
        audio_clip = repeated_audio_clip.subclip(0, audio['end'] - audio['start'])

        # 오디오 클립을 비디오의 지정된 시간대에 배치
        audio_clip = audio_clip.set_start(audio['start'])
        audio_clips.append(audio_clip)

    # 모든 오디오 클립을 하나의 클립으로 합성
    final_audio = mp.CompositeAudioClip(audio_clips)

    # 비디오에 오디오 추가
    final_clip = video_clip.set_audio(final_audio)

    # 결과 저장
    output_path = 'static/uploads/merged_video.mp4'
    final_clip.write_videofile(output_path)

    return jsonify({"success": True, "output": output_path})