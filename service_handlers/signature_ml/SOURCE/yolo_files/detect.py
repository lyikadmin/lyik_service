import argparse
import time
from pathlib import Path
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
from io import BytesIO
from PIL import Image
import importlib.resources

from .models.experimental import attempt_load
from .utils.datasets import LoadStreams, LoadImages
from .utils.general import check_img_size, non_max_suppression, scale_coords, set_logging
from .utils.torch_utils import select_device, time_synchronized
yolo_model_best_pt_path = "service_handlers/signature_ml/SOURCE/yolo_files/best.pt"
def detect(image_path):
    # 'weights': 'lyik/SOURCE/yolo_files/best.pt',
        # Access 'best.pt' using the context manager
    opt = {
        'weights': str(yolo_model_best_pt_path),
        'source': image_path,
        'img_size': 640,
        'conf_thres': 0.25,
        'iou_thres': 0.45,
        'device': '',
        'view_img': False,
        'save_txt': False,
        'save_conf': True,
        'save_crop': True,
        'nosave': True,
        'classes': 1,
        'agnostic_nms': False,
        'augment': False,
        'project': 'results/yolov5/',
        'name': 'exp',
        'exist_ok': False,
        'line_thickness': 3,
        'hide_labels': False,
        'hide_conf': False,
    }

    # Initialize
    set_logging()
    device = select_device(opt['device'])
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(opt['weights'], map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(opt['img_size'], s=stride)  # check img_size
    if half:
        model.half()  # to FP16

    # Dataloader setup
    dataset = LoadImages(opt['source'], img_size=imgsz, stride=stride)

    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once

    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # normalize
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = model(img, augment=opt['augment'])[0]

        # Apply NMS
        pred = non_max_suppression(pred, opt['conf_thres'], opt['iou_thres'], classes=opt['classes'], agnostic=opt['agnostic_nms'])

        # Process detections
        cropped_images = []
        for i, det in enumerate(pred):  # detections per image
            im0 = im0s.copy()

            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Extract and store crops in-memory
                for *xyxy, conf, cls in reversed(det):
                    cropped_img = im0[int(xyxy[1]):int(xyxy[3]), int(xyxy[0]):int(xyxy[2])]
                    pil_img = Image.fromarray(cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB))
                    
                    # Save the image to a temporary file-like object
                    buffer = BytesIO()
                    pil_img.save(buffer, format="JPEG")
                    buffer.seek(0)
                    cropped_images.append(buffer)

        return cropped_images if cropped_images else None
