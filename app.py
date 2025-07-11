import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import json
import os

from analyzer.luoshu import LuoshuAnalyzer
from analyzer.wuxing_detector import WuxingDetector
from utils.report_format import ReportFormatter



def draw_ninehalls(img):
    # 加载八卦配置
    with open('data/jiugong.json', 'r', encoding='utf-8') as f:
        bagua_config = json.load(f)['grids']

    width, height = img.size
    grid_img = img.copy()
    draw = ImageDraw.Draw(grid_img)

    font_size = min(width, height) // 25

    # 设置中文字体（建议使用支持中文的字体文件）
    try:
        cn_font = ImageFont.truetype("data/fonts/simhei.ttf", font_size) if os.name == 'nt' else ImageFont.truetype("NotoSansCJK-Regular.ttc", font_size)
    except:
        cn_font = ImageFont.load_default()  # 备用默认字体

        # 八卦符号用Segoe UI Symbol（仅Windows）
    symbol_font = ImageFont.truetype("data/fonts/seguisym.ttf", font_size) if os.name == 'nt' else cn_font

    # 绘制九宫格线（红色虚线效果）
    dash_pattern = [8, 4]  # 实线8px，空白4px
    for i in range(1, 3):
        # 竖线（虚线）
        for y in range(0, height, sum(dash_pattern)):
            draw.line([(width * i // 3, y), (width * i // 3, y + dash_pattern[0])],
                      fill="#FF0000", width=2)
        # 横线（虚线）
        for x in range(0, width, sum(dash_pattern)):
            draw.line([(x, height * i // 3), (x + dash_pattern[0], height * i // 3)],
                      fill="#FF0000", width=2)

    # 为每个格子添加标记
    for i in range(3):
        for j in range(3):
            idx = i * 3 + j
            config = bagua_config[idx]

            # 计算当前格子中心坐标
            x_center = width * (j + 0.5) / 3
            y_center = height * (i + 0.5) / 3

            # 绘制半透明背景圆角矩形
            bg_width = width // 4
            bg_height = height // 8
            draw.rounded_rectangle(
                [(x_center - bg_width // 2, y_center - bg_height // 2),
                 (x_center + bg_width // 2, y_center + bg_height // 2)],
                radius=10, fill=(0, 0, 0, 50)  # 半透明黑色背景
            )

            # 第一行：分开渲染八卦符号（默认字体）和宫位名（黑体）
            symbol_width = draw.textlength(config['symbol'], font=symbol_font)
            total_width = symbol_width + draw.textlength(config['name'], font=cn_font)

            # 先绘制八卦符号
            draw.text(
                (x_center - total_width / 2, y_center - bg_height / 4),
                config['symbol'],
                font=symbol_font,
                fill="white",
                anchor="lt"
            )
            # 再绘制中文宫位名
            draw.text(
                (x_center - total_width / 2 + symbol_width, y_center - bg_height / 4),
                config['name'],
                font=cn_font,
                fill="white",
                anchor="lt"
            )

            # 第二行：方位 + 五行（如：北方·水）
            sub_text = f"{config['position']}方·{config['element']}"
            draw.text((x_center, y_center + bg_height // 5),
                      sub_text, font=cn_font, fill="#AAAAAA", anchor="mm")

            # 在格子角落添加小字提示（如：财运）
            corner_text = config["meaning"]
            corner_x = width * (j + 0.2) / 3
            corner_y = height * (i + 0.2) / 3
            draw.text((corner_x, corner_y), corner_text,
                      font=cn_font, fill="#FFCC00", anchor="lt")

    return grid_img



# 玄学分析逻辑核心函数
def analyze_avatar(image):
    luoshu_analyzer = LuoshuAnalyzer()
    wuxing_analyzer = WuxingDetector()

    ''' 1. 九宫格切割'''

    img = Image.fromarray(image)
    grid_img = draw_ninehalls(img)

    ''' 2. 五行属性分析 '''
    img_array = np.array(img)
    wuxing = wuxing_analyzer.analyze_wuxing(img_array)


    ''' 3. 方位吉凶分析'''
    results = luoshu_analyzer.analyze_image(image)

    ''' 4. 生成报告 '''

    # 格式化，不组织语言版
    formatter = ReportFormatter()
    report = formatter.generate(wuxing, results)

    # 组织语言版
    # generator = ReportGenerator()
    # report = generator.generate_report()
    # print(generator.generate_report())

    return grid_img, report, wuxing['name']


# Gradio界面设计
with gr.Blocks(title="赛博看相：头像玄学检测器", theme=gr.themes.Soft()) as app:
    gr.Markdown("## 🔮 你的头像在玄学中是好是坏？上传检测！")

    with gr.Row():
        with gr.Column():
            upload_btn = gr.UploadButton("📁 上传头像", file_types=["image"])
            img_input = gr.Image(label="原始头像", visible=False)
            with gr.Row():
                analyze_btn = gr.Button("🔄 开始分析", variant="primary")
                clear_btn = gr.Button("🧹 清空结果")

        with gr.Column():
            img_output = gr.Image(label="后天八卦九宫格（倒置）")
            result_text = gr.Textbox(label="玄学报告", interactive=False)
            wuxing_badge = gr.Label(label="五行属性")


    # 交互逻辑
    def update_image(file):
        if file is None:
            return None, None, None, None
        return file.name, file.name, None, None


    upload_btn.upload(
        fn=update_image,
        inputs=upload_btn,
        outputs=[img_input, img_output, result_text, wuxing_badge]
    )

    analyze_btn.click(
        fn=analyze_avatar,
        inputs=img_input,
        outputs=[img_output, result_text, wuxing_badge]
    )

    clear_btn.click(
        fn=lambda: [None, None, None, None],
        outputs=[img_input, img_output, result_text, wuxing_badge]
    )

    # 添加社交分享按钮
    gr.Markdown("""
    <div style="text-align: center">
        <p>分享你的分析结果：</p>
        <a href='https://twitter.com/intent/tweet?text=我的头像玄学报告：' target='_blank'>
            <img src='https://img.icons8.com/color/48/000000/twitter.png' width='30'/>
        </a>
    </div>
    """)

app.launch()