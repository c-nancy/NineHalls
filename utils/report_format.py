from datetime import datetime
from pathlib import Path


class ReportFormatter:
    def __init__(self):
        self.template = Path("data/result_template.txt").read_text(encoding="utf-8")

    def generate(self, wuxing, grid_wuxing):
        analysis = self._prepare_data(wuxing, grid_wuxing)
        return self.template.format(**analysis)

    def _prepare_data(self, wuxing, grids):
        """处理数据为模板需要的格式"""
        return {
            # 展开wuxing字典
            "wuxing_name": wuxing["name"],
            "wuxing_score": min(wuxing["score"], 1) * 100,
            "wuxing_reason": wuxing["reason"],

            # 其他数据保持不变
            "grid_analysis": self._format_grids(grids),
            "overall_suggestion": self._generate_suggestion(grids),
            "fortune_tip": self._generate_fortune_tip(wuxing, grids),
            # "report_time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def _format_grids(self, grids):
        """格式化九宫格数据"""
        return "\n".join(
            f"{g['symbol']} {g['bagua_name']}({g['position']}):\n"
            f"- 检测：{g['detected_element']} → 需{g['expected_element']} "
            f"{'✓' if g['is_harmony'] else '✗'}\n"
            f"- 建议：{g['suggestion']}\n"
            for g in grids
        )

    def _generate_suggestion(self, grids):
        """生成整体建议"""
        conflicts = [g for g in grids if not g['is_harmony']]
        if not conflicts:
            return "九宫能量和谐，保持当前布局即可"

        tips = []
        for g in conflicts[:2]:  # 最多提示2个主要冲突
            reason = f"{g['detected_element']}克{g['expected_element']}" if not g['is_harmony'] else ""
            tips.append(f"「{g['position']}」{reason}：{g['suggestion'].split(',')[0]}")
        return "重点调整：\n• " + "\n• ".join(tips)

    def _generate_fortune_tip(self, wuxing, grids):
        """生成运势提示"""
        element = wuxing["name"]
        if element == "火":
            return "火主礼，近期宜主动社交拓展人脉"
        elif element == "水":
            return "水主智，适合学习深造或策划决策"
        # 其他五行判断...

        # 默认根据冲突宫位判断
        conflict_count = sum(1 for g in grids if not g['is_harmony'])
        if conflict_count > 3:
            return "多宫位能量冲突，建议佩戴五行调和饰品"
        return "整体运势平稳，注意劳逸结合"
