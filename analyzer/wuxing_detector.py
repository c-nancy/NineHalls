import cv2
import numpy as np
from ultralytics import YOLO
import json
from PIL import Image
from utils.utils import (
    get_dominant_color,
    color_to_wuxing,
)


class WuxingDetector:
    def __init__(self, config_path='data/wuxing_mapping.json', yolo_path='yolo11n.pt'):
        # 初始化YOLO
        self.model = YOLO(yolo_path)  # 可选：yolov8s/m/l/x
        # 加载五行映射表
        with open(config_path, 'r', encoding='utf-8') as f:
            self.WUXING_MAPPING = json.load(f)

    def analyze_wuxing(self,image_array):
        """
        分析图像五行属性
        :param image_array: 图片array
        :param min_area_ratio: 物体最小占比阈值（默认10%）
        :return: {"wuxing": 五行结果, "method": 检测方式, "details": 详情}
        """

        min_area_ratio = 0.1

        # 读取图像并获取尺寸
        # 统一转换为RGB numpy数组
        if isinstance(image_array, Image.Image):
            img_array = np.array(image_array)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)  # PIL转OpenCV格式
        elif isinstance(image_array, np.ndarray):
            img_array = image_array.copy()  # 避免修改原数组
        else:
            raise ValueError("Unsupported image type. Expected PIL.Image or numpy array.")

        h, w = img_array.shape[:2]
        total_pixels = h * w
        detections = []

        results = self.model(img_array)  # 关键修改：直接传数组而非路径

        # 提取有效物体（面积>10%）
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area = (x2 - x1) * (y2 - y1)
            if area / total_pixels >= min_area_ratio and box.conf > 0.5:  # 置信度>50%
                label = self.model.names[int(box.cls)]
                detections.append({
                    "label": label,
                    "area_ratio": round(area / total_pixels, 2),
                    "confidence": float(box.conf)
                })

        # 根据物体判断五行
        if detections:
            wuxing_weights = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
            reason = ""
            for obj in detections:
                mapping = self.WUXING_MAPPING.get(obj["label"], self.WUXING_MAPPING["default"])
                # for label, weight, name, reason in mapping.items():
                #     wuxing_weights[label] += weight * obj["area_ratio"]  # 按面积加权
                #     reason += f"{name}: {reason}"
                for label, weight in mapping['element'].items():
                    wuxing_weights[label] += weight * obj["area_ratio"]  # 按面积加权
                    reason += f"{mapping['name']}: {mapping['reason']}\n"

            main_wuxing = max(wuxing_weights, key=wuxing_weights.get)
            # return {
            #     "wuxing": main_wuxing,
            #     "method": "object",
            #     "details": {
            #         "detected_objects": detections,
            #         "wuxing_weights": wuxing_weights
            #     }
            # }
            score = max(wuxing_weights.values())
            return {
                "name": main_wuxing,
                "reason": reason,
                "score": score
            }

        # 物体检测失败时降级到颜色分析
        # return {
        #     "wuxing": self.color_based_wuxing(img_array),
        #     "method": "color",
        #     "reason": "色彩理论"
        # }
        dominant_color = get_dominant_color(img_array)
        wuxing = color_to_wuxing(dominant_color)
        return wuxing


    def color_based_wuxing(self, img):
        """颜色五行分析（HSV空间）"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 定义五行颜色范围（HSV）
        color_ranges = {
            "木": ((35, 50, 50), (85, 255, 255)),  # 绿色
            "火": ((0, 100, 100), (20, 255, 255)),  # 红色
            "土": ((20, 30, 50), (35, 150, 150)),  # 黄色/棕色
            "金": ((0, 0, 100), (30, 50, 200)),  # 白色/金属色
            "水": ((85, 50, 50), (120, 255, 255))  # 蓝色
        }

        # 计算各五行颜色占比
        element_pixels = {}
        for element, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            element_pixels[element] = mask.sum()

        return max(element_pixels, key=element_pixels.get)


# # 示例调用
# result = analyze_wuxing("../testdatas/cat.png")
# print(f"五行属性: {result['wuxing']} (检测方式: {result['method']})")
# print("详情:", result["details"])