from flask import Flask, render_template, send_from_directory
import os
import config

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    # 오디오 파일 저장 경로
    app.config['SAVED_FOLDER'] = config.SAVED_FOLDER

    if not os.path.exists(app.config['SAVED_FOLDER']):
        os.makedirs(app.config['SAVED_FOLDER'])

id_mapping = {}

app = create_app()
@app.route('/', methods=['GET'])
def index():
    # 메인페이지 
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # 업로드된 파일 제공
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)