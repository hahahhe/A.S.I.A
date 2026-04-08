from flask import Blueprint, request, jsonify, current_app
from services.video_service import process_video
import os

video_bp = Blueprint('video', __name__)

@video_bp.route("/process/labels", methods=["POST"])
def process_labels():
    try:
        data = request.json
        # 클라이언트로부터 original_video_url 받기
        filename = data['filename']
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        models = current_app.config["MODELS"]

        # 비디오에서 객체 탐지 및 라벨링
        labeled_video_path = os.path.join(file_path, f'labeled_{filename}')
        output_path = os.path.join(file_path, f"labeled_{filename}")

        result = process_video(
            labeled_video_path,
            output_path,
            models,
            file_path
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500