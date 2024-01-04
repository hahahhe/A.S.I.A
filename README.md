<img src="static/img/logo.png" align="left" width="100" style="margin-right: 10px;"/>

# A.S.I.A
[Watch the Project Demo Here](https://youtu.be/WJXArTy-frs)

## Project Description
This project leverages AI models to automatically generate and insert appropriate sound effects into videos at the correct positions. This project has been developed using the YOLOv5, Kosmos-2-patch14-224, and AudioLDM-m-full models. Each model provides unique features, and their combination [specific strengths or differentiating points].

## System Functionality
The system encompasses video processing, audio generation, and audio editing capabilities.

### Video Processing Workflow
- The user uploads a video.
- The video is sequenced into 0.5-second intervals.
- YOLOv5 object detection identifies objects in each frame, recording the start and end times of detection.
- Kosmos-2 generates captions for the midpoint of the detected object's duration.
- AudioLDM creates audio based on these captions.
- The generated audio is then inserted into the video at the times when the objects were detected.

### Audio Editing
- Users can adjust the position and length of audio clips, replace audio.
- Implement logic using the Python moviepy module.

## Models Used
- **YOLOv5**: Utilized for object detection. Licensed under AGPLv3.
- **Kosmos-2-patch14-224**: Generating captions. Licensed under the MIT License.
- **AudioLDM-m-full**: Employed for audio processing. Licensed under CC BY-NC-SA 4.0.

## License
This project uses models that are subject to different licenses. For detailed information, please refer to the LICENSE file.

## Team Members
- [최준혁](https://github.com/hahahhe): Team Leader - Led the team and managed code integration.
- [나희진](https://github.com/skgmlwls): Developer - Worked on audio editing features.
- [이수근](https://github.com/lsugeun): Developer - Worked on model implementation and Python coding.
- [장기원](https://github.com/wkdrldnjs): Developer - Focused on audio list retrieval from the API.