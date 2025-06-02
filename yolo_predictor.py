import os
from ultralytics import YOLO
from PIL import Image
from collections import Counter

# 모델 로드 (앱 시작 시 1회만)
MODEL_PATH = "yolo11_s/weights/rotten_straw.pt"
model = YOLO(MODEL_PATH)

def run_inference(image_path):
    """
    주어진 이미지에서 YOLO 추론을 수행하고,
    각 클래스의 개수를 반환.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 경로를 찾을 수 없습니다: {image_path}")

    # 추론
    results = model(image_path)

    # 클래스 이름 추출
    class_names = [model.names[int(cls)] for cls in results[0].boxes.cls]
    class_counts = Counter(class_names)

    # 시각화된 결과 저장 (선택)
    output_path = os.path.join("static", "images", "last_pred.jpg")
    results[0].save(filename=output_path)

    return class_counts, output_path
