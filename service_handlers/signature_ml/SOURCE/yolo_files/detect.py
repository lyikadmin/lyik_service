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

from service_handlers.signature_ml.SOURCE.yolo_files.models.experimental import attempt_load
from service_handlers.signature_ml.SOURCE.yolo_files.utils.datasets import LoadStreams, LoadImages
from service_handlers.signature_ml.SOURCE.yolo_files.utils.general import check_img_size, non_max_suppression, scale_coords, set_logging
from service_handlers.signature_ml.SOURCE.yolo_files.utils.torch_utils import select_device, time_synchronized
yolo_model_best_pt_path = "service_handlers/signature_ml/SOURCE/yolo_files/best.pt"
def detect(image_path, check_wet_signature_coverage=False, coverage_threshold=0.6):
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
        print(f"The number of detections is {len(pred)}")

        # Process detections
        cropped_images = []
        for i, det in enumerate(pred):  # detections per image
            im0 = im0s.copy()

            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

              # Extract and store crops in-memory
                for *xyxy, conf, cls in reversed(det):
                    # Increase the bounding box area by 10%
                    x1, y1, x2, y2 = xyxy
                    width = x2 - x1
                    height = y2 - y1
                    increase_ratio_by = 0.5
                    x1 = max(0, x1 - increase_ratio_by * width)
                    y1 = max(0, y1 - increase_ratio_by * height)
                    x2 = min(im0.shape[1], x2 + increase_ratio_by * width)
                    y2 = min(im0.shape[0], y2 + increase_ratio_by * height)

                    # Check bounding box coverage if enabled
                    if check_wet_signature_coverage and not check_bounding_box_coverage((x1, y1, x2, y2), im0.shape, coverage_threshold):
                        print("Bounding box coverage below threshold.")
                        return "Signature not detected as wet signature. Make sure the signature is clear, and spans the full image without gaps."

                    cropped_img = im0[int(y1):int(y2), int(x1):int(x2)]
                    pil_img = Image.fromarray(cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB))
                    
                    
                    # Save the image to a temporary file-like object
                    buffer = BytesIO()
                    pil_img.save(buffer, format="JPEG")
                    buffer.seek(0)
                    cropped_images.append(buffer)

        return cropped_images if cropped_images else None

def check_bounding_box_coverage(xyxy, image_shape, coverage_threshold=0.6):
    """
    Checks whether the bounding box covers at least a specified percentage of the image area.

    Args:
        xyxy (list): Bounding box coordinates [x_min, y_min, x_max, y_max].
        image_shape (tuple): Shape of the image as (height, width, channels).
        coverage_threshold (float): Minimum percentage of image area the bounding box must cover.

    Returns:
        bool: True if the bounding box covers the required area, False otherwise.
    """
    bbox_width = xyxy[2] - xyxy[0]
    bbox_height = xyxy[3] - xyxy[1]
    bbox_area = bbox_width * bbox_height

    image_height, image_width = image_shape[:2]
    image_area = image_width * image_height

    coverage_ratio = bbox_area / image_area
    print(f"Coverage_ratio:{coverage_ratio}\n Coverage_threshold: {coverage_threshold}")
    return coverage_ratio >= coverage_threshold