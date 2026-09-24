from flask import Flask, render_template
import os
from config import Config
from routes.audio import audio_bp
from routes.video import video_bp
'''
import torch

print("PyTorch:", torch.__version__)
print("PyTorch CUDA:", torch.version.cuda)
print("CUDA available:", torch.cuda.is_available())
print("GPU count:", torch.cuda.device_count())
'''
def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SAVED_FOLDER"], exist_ok=True)
    os.makedirs("effects", exist_ok=True)
    os.makedirs("static/uploads", exist_ok=True)

    app.register_blueprint(video_bp)
    app.register_blueprint(audio_bp)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    