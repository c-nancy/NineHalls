import cv2
import colorsys
import numpy as np
import os

# 辅助函数：获取主色
def get_dominant_color(img_array, k=1):
    pixels = img_array.reshape(-1, 3)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
    _, labels, palette = cv2.kmeans(pixels.astype(np.float32), k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    return tuple(map(int, palette[0]))


# 辅助函数：颜色转五行
def color_to_wuxing(rgb):
    """基于《易经》五行理论的精确色彩分类"""
    r, g, b = [x / 255 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h_degree = h * 360  # 转换为0-360度色环

    # 先判断特殊色系（金、土）
    if s < 0.2 and v > 0.8:
        return {"name": "金", "score": int(v * 100), "reason": "低饱和高明度"}


    if 40 <= h_degree <= 60 and s > 0.5:  # 黄色系
        return {"name": "土", "score": int(s * 100), "reason": "中央土色"}
    #
    # if 0.3 < s < 0.7 and 0.7 < v < 0.9:  # 金属光泽区间
    #     return {"name": "金", "score": 90, "reason": "金属光泽"}

    if v < 0.15:  # 极低明度
        return {"name": "水", "score": 100, "reason": "玄冥之色"}

    # 常规五行色系判断
    if h_degree < 40 or h_degree >= 350:  # 红-品红区间
        return {"name": "火", "score": int(s * 100), "reason": "赤色属火"}

    elif 60 <= h_degree < 150:  # 黄绿-绿色区间
        return {"name": "木", "score": int((s + v) / 2 * 100), "reason": "青色属木"}

    elif 150 <= h_degree < 250:  # 青-蓝色区间
        return {"name": "水", "score": int(v * 100), "reason": "玄色属水"}

    else:  # 紫色系（250-350）
        return {"name": "火", "score": int(s * 70 + v * 30), "reason": "紫为火之余气"}


def find_system_font():
    # 常见 Linux 字体路径列表
    font_dirs = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # DejaVu 字体（常见于 Ubuntu/Debian）
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # RedHat/CentOS
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # 中文字体
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  # 其他发行版
        "/usr/local/share/fonts/",  # 手动安装的字体
        os.path.expanduser("~/.local/share/fonts/"),  # 用户字体
    ]