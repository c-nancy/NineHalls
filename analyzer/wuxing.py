import json

# 加载矩阵
with open('data/wuxing.json', 'r', encoding='utf-8') as f:
    wuxing_data = json.load(f)


def get_element_interaction(ideal, actual, percent):
    """ 获取五行相互作用详情 """
    rule = wuxing_data['matrix'][ideal][actual]

    # 动态计算修正值（安全执行公式）
    try:
        dynamic = eval(rule['formula'], {'x': percent / 100})
    except:
        dynamic = 1.0

    # 反克规则检查
    if percent > wuxing_data['special_rules']['反克阈值'] and rule.get('warning'):
        dynamic *= 1.3  # 反克补偿

    # 最终分数
    score = min(max(rule['base'] * dynamic, 0.1), 1.5)

    return {
        'score': round(score, 2),
        'description': rule['desc'],
        'suggestion': rule.get('suggestion', ''),
        'is_critical': rule.get('critical', False)
    }


def check_element_harmony(grid_element, grid_ideal_element, element_percent=95):
    """

    参数：
        grid_element: str - 实际检测到的五行（木/火/土/金/水）
        grid_ideal_element: str - 宫位理论五行
        element_percent: int - 该元素在宫位的占比（0-100，默认50）

    返回：
        {
            "is_harmony": bool,  # 是否和谐（score>=0.75）
            "score": float,      # 和谐度评分
            "relationship": str, # 关系描述
            "advice": str       # 优化建议
        }
    """
    # 1. 获取生克规则
    try:
        rule = wuxing_data['matrix'][grid_ideal_element][grid_element]
    except KeyError:
        return {
            "is_harmony": False,
            "score": 0,
            "relationship": "无效五行输入",
            "advice": "请检查元素名称是否符合木/火/土/金/水"
        }

    # 2. 计算动态评分
    try:
        dynamic_coeff = eval(rule['formula'], {'x': element_percent / 100})
    except:
        dynamic_coeff = 1.0

    score = min(max(rule['base'] * dynamic_coeff, 0.1), 1.5)

    # 反克规则检查
    if element_percent > wuxing_data['special_rules']['反克阈值'] and rule.get('warning'):
        dynamic_coeff *= 1.3  # 反克补偿

    # 3. 生成建议
    # 修正后的建议分级逻辑
    advice_map = [
        (1.0, 1.5, "完美契合，保持当前元素"),
        (0.9, 1.0, "轻微调整即可优化"),
        (0.75, 0.9, "基本和谐，细节可提升"),
        (0.5, 0.75, f"建议调整：{rule.get('suggestion', '参考五行生克')}"),
        (0.1, 0.5, "严重冲突，需重新设计")
    ]

    # 按顺序检查区间（从高到低）
    for min_score, max_score, advice_text in advice_map:
        if min_score < score <= max_score:  # 注意开闭区间
            advice = advice_text
            break
    else:
        advice = "能量状态异常"  # 默认值（理论上不会触发）
    return {
        "is_harmony": score >= 0.75,
        "score": round(score, 2),
        "relationship": rule['desc'],
        "advice": advice
    }
