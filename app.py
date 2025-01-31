import streamlit as st
import cv2
import torch
from utils.hubconf import custom
import numpy as np
import tempfile
import time
from collections import Counter
import json
import pandas as pd
from model_utils import get_yolo, color_picker_fn, get_system_stat
from ultralytics import YOLO
#import pafy
from pathlib import Path
import sys


st.set_page_config(
    page_icon='🕳️',
    page_title='Pothole Detection')

# st.header("LY Project 2023")
# st.subheader("KJSCE, Mumbai")
p_time = 0

st.sidebar.title('Settings')
# Choose the model
model_type = st.sidebar.selectbox(
    'Choose DL Model', ( 'YOLOv8',)
)

# #background image
st.title("Pothole Detection - Deep learning")
sample_img = cv2.imread('pothole_front.png')
FRAME_WINDOW = st.image(sample_img, channels='BGR')
cap = None

if not model_type == 'YOLO Model':
    # path_model_file = st.sidebar.text_input(
    #     f'path to {model_type} Model:',
    #     f'eg: dir/{model_type}.pt'
    # )

    # Get the absolute path of the current file
    file_path = Path(__file__).resolve()

    # Get the parent directory of the current file
    root_path = file_path.parent

    # Add the root path to the sys.path list if it is not already there
    if root_path not in sys.path:
        sys.path.append(str(root_path))

    # Get the relative path of the root directory with respect to the current working directory
    ROOT = root_path.relative_to(Path.cwd())

    # v5n model
    # MODEL_DIR = ROOT / 'weights'
    # DETECTION_MODEL_5 = MODEL_DIR / 'v5n.200.pt'
    # model_path_5 = Path(DETECTION_MODEL_5)

    # v8n model
    MODEL_DIR = ROOT / 'weights'
    DETECTION_MODEL_8 = MODEL_DIR / 'best.pt' # best.pt
    model_path_8 = Path(DETECTION_MODEL_8)


    if st.sidebar.checkbox('Load Model'):
        
        # YOLOv5 Model
        # if model_type == 'YOLOv5':
        #   model = YOLO(model_path_5)

        # YOLOv7 Model
        if model_type == 'YOLOv8':
            model = YOLO(model_path_8)

        # Load Class names
        class_labels = model.names

        # Inference Mode
        options = st.sidebar.radio(
            'Options:', ('Webcam', 'Image', 'Video'), index=1)

        # Confidence
        confidence = st.sidebar.slider(
           'Detection Confidence', min_value=0.0, max_value=1.0, value=0.25)

        # Draw thickness
        draw_thick = st.sidebar.slider(
            'Draw Thickness:', min_value=1,
            max_value=20, value=3
        )
        
        color_pick_list = []
        for i in range(len(class_labels)):
            classname = class_labels[i]
            color = color_picker_fn(classname, i)
            color_pick_list.append(color)

        # Image
        if options == 'Image':
            upload_img_file = st.sidebar.file_uploader(
                'Upload Image', type=['jpg', 'jpeg', 'png'])
            if upload_img_file is not None:
                pred = st.checkbox(f'Predict Using {model_type}')
                file_bytes = np.asarray(
                    bytearray(upload_img_file.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, 1)
                FRAME_WINDOW.image(img, channels='BGR')

                if pred:
                    img, current_no_class = get_yolo(img, model_type, model, confidence, color_pick_list, class_labels, draw_thick)
                    FRAME_WINDOW.image(img, channels='BGR')

                    # Current number of classes
                    class_fq = dict(Counter(i for sub in current_no_class for i in set(sub)))
                    class_fq = json.dumps(class_fq, indent = 4)
                    class_fq = json.loads(class_fq)
                    df_fq = pd.DataFrame(class_fq.items(), columns=['Class', 'Number'])
                    
                    # Updating Inference results
                    with st.container():
                        st.markdown("<h2>Inference Statistics</h2>", unsafe_allow_html=True)
                        st.markdown("<h3>Detected objects in curret Frame</h3>", unsafe_allow_html=True)
                        st.dataframe(df_fq, use_container_width=True)
        
        # Video
        if options == 'Video':
            upload_video_file = st.sidebar.file_uploader(
                'Upload Video', type=['mp4', 'avi', 'mkv'])
            if upload_video_file is not None:
                pred = st.checkbox(f'Predict Using {model_type}')

                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(upload_video_file.read())
                cap = cv2.VideoCapture(tfile.name)
                # if pred:


        # Web-cam
        if options == 'Webcam':
            cam_options = st.sidebar.selectbox('Webcam Channel',
                                            ('Select Channel', '0', '1', '2', '3'))
        
            if not cam_options == 'Select Channel':
                pred = st.checkbox(f'Predict Using {model_type}')
                cap = cv2.VideoCapture(int(cam_options))


        # # RTSP
        # if options == 'RTSP':
        #   rtsp_url = st.sidebar.text_input(
        #       'RTSP URL:',
        #      'eg: rtsp://admin:name6666@198.162.1.58/cam/realmonitor?channel=0&subtype=0'
        #  )
        #  pred = st.checkbox(f'Predict Using {model_type}')
        #  cap = cv2.VideoCapture(rtsp_url)

        # # Youtube
        # if options == 'Youtube':
        #     youtube_url = st.sidebar.text_input("YouTube Video url:")
        #     pred = st.checkbox(f'Predict Using {model_type}')
        #     if youtube_url:
        #         try:
        #             video = pafy.new(youtube_url)
        #             best = video.getbest(preftype="mp4")
        #             cap = cv2.VideoCapture(best.url)
        #         except:
        #             st.warning('Please enter a valid YouTube video url.')



if (cap != None) and pred:
    stframe1 = st.empty()
    stframe2 = st.empty()
    stframe3 = st.empty()
    while True:
        success, img = cap.read()
        if not success:
            st.error(
                f"{options} NOT working\nCheck {options} properly!!",
                icon="🚨"
            )
            break

        img, current_no_class = get_yolo(img, model_type, model, confidence, color_pick_list, class_labels, draw_thick)
        FRAME_WINDOW.image(img, channels='BGR')

        # FPS
        c_time = time.time()
        fps = 1 / (c_time - p_time)
        p_time = c_time

        # Current number of classes
        class_fq = dict(Counter(i for sub in current_no_class for i in set(sub)))
        class_fq = json.dumps(class_fq, indent = 4)
        class_fq = json.loads(class_fq)
        df_fq = pd.DataFrame(class_fq.items(), columns=['Class', 'Number'])
        
        # Updating Inference results
        get_system_stat(stframe1, stframe2, stframe3, fps, df_fq)
