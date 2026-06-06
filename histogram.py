# -*- coding: utf-8 -*-
"""
生成可自定义的直方图（柱状图）。

功能：
  - 自定义横、纵轴名称
  - 纵轴网格线（grid）开关与样式
  - 横轴每个方块（柱子）的子名称（类别标签）
  - 自定义每根柱子的颜色、标题
  - 柱顶数值标注
  - 输出高分辨率 PNG (300 dpi) + 矢量 PDF 到 figure/ 目录

依赖：matplotlib
"""

import os

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# =============================================================================
# 1. 用户自定义区域 —— 你主要修改这里
# =============================================================================

# --- 1.0 图表类型："bar" 直方图 / "line" 折线图 ---
CHART_TYPE = "line"

# --- 1.1 数据：横轴每个方块的子名称 + 对应的数值（两者一一对应） ---
#     想增删柱子 / 改数值，直接改这两个列表即可（长度必须相同）。
BAR_LABELS = ["2020", "2021", "2022"]
BAR_VALUES = [3, 26, 2]

# --- 1.2 横、纵轴名称 ---
X_AXIS_NAME = "实施省以下财政事权划分改革年份"
Y_AXIS_NAME = "改革省份数目"

# --- 1.3 图标题 ---
SHOW_TITLE = False           # 是否显示标题
TITLE = "示例直方图"

# --- 1.4 柱子颜色 ---
#     给一个颜色 -> 所有柱子同色；给一个列表（长度与柱子数相同）-> 每根柱子单独配色。
BAR_COLORS = ["#00b141"]

# --- 1.4b 折线图样式（仅 CHART_TYPE = "line" 时生效） ---
LINE_COLOR = "#200101"      # 折线颜色
LINE_WIDTH = 2.0            # 折线线宽
LINE_STYLE = "-"           # 折线样式（'-' / '--' / ':' / '-.'）
MARKER = "o"               # 数据点标记（'o' 圆 / 's' 方 / '^' 三角 / '' 无）
MARKER_SIZE = 6            # 标记大小

# --- 1.5 网格线（grid）设置 ---
SHOW_Y_GRID = True          # 是否显示纵轴方向的网格线
GRID_COLOR = "#cccccc"      # 网格线颜色
GRID_LINESTYLE = "--"       # 网格线样式（'-' 实线 / '--' 虚线 / ':' 点线）
GRID_LINEWIDTH = 0.8        # 网格线宽度

# --- 1.6 柱顶数值标注 ---
SHOW_VALUE_LABELS = True  # 是否在每根柱子上方标出数值

# --- 1.7 其它外观 ---
BAR_WIDTH = 0.4             # 柱子宽度（0~1）
FIGSIZE = (10, 6)          # 画布尺寸（英寸）
OUTPUT_BASENAME = "histogram"  # 输出文件名（不含扩展名）
SAVE_PDF = True
DPI = 300

# =============================================================================
# 2. 绘图逻辑（一般无需修改）
# =============================================================================


def configure_chinese_font():
    """配置中文字体，避免乱码。"""
    candidates = ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC",
                  "WenQuanYi Zen Hei", "Source Han Sans SC"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False


def main():
    configure_chinese_font()

    if len(BAR_LABELS) != len(BAR_VALUES):
        raise ValueError(
            f"BAR_LABELS({len(BAR_LABELS)}) 与 BAR_VALUES({len(BAR_VALUES)}) 长度必须相同"
        )

    x = range(len(BAR_VALUES))

    fig, ax = plt.subplots(figsize=FIGSIZE)

    if CHART_TYPE == "line":
        ax.plot(list(x), BAR_VALUES, color=LINE_COLOR, linewidth=LINE_WIDTH,
                linestyle=LINE_STYLE, marker=MARKER, markersize=MARKER_SIZE,
                zorder=3)
        labeled = None
    elif CHART_TYPE == "bar":
        labeled = ax.bar(x, BAR_VALUES, width=BAR_WIDTH, color=BAR_COLORS,
                         edgecolor="black", linewidth=0.6, zorder=3)
    else:
        raise ValueError(f"未知 CHART_TYPE={CHART_TYPE!r}，只支持 'bar' 或 'line'")

    # 横轴每个方块的子名称
    ax.set_xticks(list(x))
    ax.set_xticklabels(BAR_LABELS, fontsize=11)

    # 横、纵轴名称
    ax.set_xlabel(X_AXIS_NAME, fontsize=13, fontweight="bold")
    ax.set_ylabel(Y_AXIS_NAME, fontsize=13, fontweight="bold")

    # 标题
    if SHOW_TITLE and TITLE:
        ax.set_title(TITLE, fontsize=16, fontweight="bold", pad=12)

    # 纵轴网格线
    if SHOW_Y_GRID:
        ax.grid(axis="y", color=GRID_COLOR, linestyle=GRID_LINESTYLE,
                linewidth=GRID_LINEWIDTH, zorder=0)
        ax.set_axisbelow(True)

    # 柱顶/点上数值标注
    if SHOW_VALUE_LABELS:
        if labeled is not None:
            ax.bar_label(labeled, fontsize=10, padding=3)
        else:
            for xi, yi in zip(x, BAR_VALUES):
                ax.annotate(str(yi), (xi, yi), textcoords="offset points",
                            xytext=(0, 6), ha="center", fontsize=10)

    # 去掉上、右边框，更清爽
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    # 输出
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figure")
    os.makedirs(out_dir, exist_ok=True)

    png = os.path.join(out_dir, OUTPUT_BASENAME + ".png")
    fig.savefig(png, dpi=DPI, bbox_inches="tight")
    print("已保存：", png)

    if SAVE_PDF:
        pdf = os.path.join(out_dir, OUTPUT_BASENAME + ".pdf")
        fig.savefig(pdf, bbox_inches="tight")
        print("已保存：", pdf)

    plt.close(fig)


if __name__ == "__main__":
    main()
