import json
from PIL import Image
import numpy as np
import colorsys

from utils.utils import (
    get_dominant_color,
    color_to_wuxing,
)


from analyzer.wuxing import check_element_harmony
from analyzer.wuxing_detector import WuxingDetector



class LuoshuAnalyzer:
    def __init__(self, config_path="data/jiugong.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.grid_positions = [
            "乾位(西北)", "坎位(北)", "坤位(西南)",
            "震位(东)", "兑位(西)", "中宫",
            "巽位(东南)", "艮位(东北)", "离位(南)"
        ]
        self.object_detector = WuxingDetector()  # 物体检测器实例

    def get_objects_element(self, img_array):
        """通过物体检测获取五行元素"""
        if not self.object_detector:
            return None

        # 假设object_detector有一个detect方法，返回检测到的物体及其五行属性
        detections = self.object_detector.analyze_wuxing(img_array)
        if not detections:
            return None

        # # 计算所有检测物体的五行加权值
        # element_scores = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        # for obj in detections:
        #     for element, score in obj["element"].items():
        #         element_scores[element] += score
        #
        # # 返回得分最高的五行
        # return max(element_scores.items(), key=lambda x: x[1])[0]

        # return detections['score']
        return detections['name']


    def get_dominant_color(self, img_array):
        """获取九宫格区域的主色"""
        pixels = img_array.reshape(-1, 3)
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        return tuple(unique_colors[np.argmax(counts)])

    def rgb_to_element(self, rgb):
        """将RGB颜色转换为五行元素"""
        r, g, b = [x / 255 for x in rgb]
        h, _, _ = colorsys.rgb_to_hsv(r, g, b)

        if h < 0.05 or h > 0.95:
            return "火"
        elif 0.05 <= h < 0.1:
            return "土"
        elif 0.1 <= h < 0.4:
            return "木"
        elif 0.4 <= h < 0.7:
            return "水"
        else:
            return "金"

    def analyze_grid(self, grid_img, grid_index):
        """分析单个九宫格"""
        grid_data = self.config["grids"][grid_index]
        img_array = np.array(grid_img)
        color = get_dominant_color(img_array)

        # 优先使用物体检测判断五行
        element = self.get_objects_element(img_array)

        # 如果没有检测到物体，则使用颜色判断
        if element is None:
            color = get_dominant_color(img_array)
            element = self.rgb_to_element(color)

        # 检查是否符合该宫位五行
        # is_harmony = (element == grid_data["element"])
        harmony = check_element_harmony(element, grid_data["element"])

        # 生成建议
        suggestion = ""
        if not harmony["is_harmony"]:
            # suggestion = f"建议添加{grid_data['element']}元素（如：{', '.join(grid_data['recommend'][:2])}）"
            suggestion = harmony["advice"]
        else:
            suggestion = f"元素协调，避免{', '.join(grid_data['avoid'][:2])}"

        return {
            "position": self.grid_positions[grid_index],
            "bagua_name": grid_data["name"],
            "symbol": grid_data["symbol"],
            "dominant_color": color,
            "detected_element": element,
            "expected_element": grid_data["element"],
            "is_harmony": harmony["is_harmony"],
            "suggestion": suggestion,
            "meaning": grid_data["meaning"]
        }

    def analyze_image(self, image):
        """分析整张图片"""
        img = Image.fromarray(image)
        width, height = img.size
        grid_size = 3
        results = []

        for i in range(grid_size):
            for j in range(grid_size):
                # 切割九宫格
                left = width * j // grid_size
                upper = height * i // grid_size
                right = width * (j + 1) // grid_size
                lower = height * (i + 1) // grid_size
                grid_img = img.crop((left, upper, right, lower))

                # 计算当前格子索引（0-8）
                grid_index = i * grid_size + j
                results.append(self.analyze_grid(grid_img, grid_index))

        return results

