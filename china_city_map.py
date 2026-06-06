# -*- coding: utf-8 -*-
"""
生成带指北针和比例尺的中国市级行政区划图。

数据来源：阿里 DataV GeoAtlas（在线下载，自动缓存到本地 data/ 目录）。
功能：
  - 自定义城市配色（通过下方字典配置）
  - 左下角图例（每种颜色的含义可自定义）
  - 指北针（北方向标）
  - 比例尺（基于等积投影，单位 km）
  - 输出高分辨率 PNG (300 dpi) + 矢量 PDF

依赖：geopandas, matplotlib, shapely, requests
"""

import os
import json
import time

import requests
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Patch, FancyArrow
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from shapely.geometry import shape

# =============================================================================
# 1. 用户自定义区域 —— 你主要修改这里
# =============================================================================

# --- 1.1 图例：每个“类别”对应一种颜色和一段含义说明（图例文字即类别名） ---
#     想增删类别 / 改颜色，直接改这个字典即可。
CATEGORY_COLORS = {
    "2020年进行了省以下财政事权划分改革的城市": "#b5e2a7",
    "2021年进行了省以下财政事权划分改革的城市": "#e7f5b8",
    "2022年进行了省以下财政事权划分改革的城市": "#ffc981",
}

# --- 1.2 省份 -> 类别 的映射。键是省/直辖市/自治区名，值是上面字典里的某个类别 ---
#     支持简写（如“广西”“内蒙古”“西藏”“宁夏”“新疆”），同省所有城市统一着色。
#     未列入下表的省份，其城市统一使用 DEFAULT_COLOR 显示。
PROVINCE_CATEGORY = {
    # 2020 年
    "北京市": "2020年进行了省以下财政事权划分改革的城市",
    "河北省": "2020年进行了省以下财政事权划分改革的城市",
    "广西壮族自治区": "2020年进行了省以下财政事权划分改革的城市",
    # 2021 年
    "天津市": "2021年进行了省以下财政事权划分改革的城市",
    "山西省": "2021年进行了省以下财政事权划分改革的城市",
    "内蒙古自治区": "2021年进行了省以下财政事权划分改革的城市",
    "辽宁省": "2021年进行了省以下财政事权划分改革的城市",
    "吉林省": "2021年进行了省以下财政事权划分改革的城市",
    "黑龙江省": "2021年进行了省以下财政事权划分改革的城市",
    "江苏省": "2021年进行了省以下财政事权划分改革的城市",
    "浙江省": "2021年进行了省以下财政事权划分改革的城市",
    "安徽省": "2021年进行了省以下财政事权划分改革的城市",
    "福建省": "2021年进行了省以下财政事权划分改革的城市",
    "江西省": "2021年进行了省以下财政事权划分改革的城市",
    "山东省": "2021年进行了省以下财政事权划分改革的城市",
    "河南省": "2021年进行了省以下财政事权划分改革的城市",
    "湖北省": "2021年进行了省以下财政事权划分改革的城市",
    "湖南省": "2021年进行了省以下财政事权划分改革的城市",
    "海南省": "2021年进行了省以下财政事权划分改革的城市",
    "重庆市": "2021年进行了省以下财政事权划分改革的城市",
    "四川省": "2021年进行了省以下财政事权划分改革的城市",
    "贵州省": "2021年进行了省以下财政事权划分改革的城市",
    "云南省": "2021年进行了省以下财政事权划分改革的城市",
    "西藏自治区": "2021年进行了省以下财政事权划分改革的城市",
    "陕西省": "2021年进行了省以下财政事权划分改革的城市",
    "甘肃省": "2021年进行了省以下财政事权划分改革的城市",
    "青海省": "2021年进行了省以下财政事权划分改革的城市",
    "宁夏回族自治区": "2021年进行了省以下财政事权划分改革的城市",
    "新疆维吾尔自治区": "2021年进行了省以下财政事权划分改革的城市",
    # 2022 年
    "上海市": "2022年进行了省以下财政事权划分改革的城市",
    "广东省": "2022年进行了省以下财政事权划分改革的城市",
}

# --- 1.3 未分类城市的默认填充色，以及是否在图例中显示“未分类” ---
DEFAULT_COLOR = "#f0f0f0"
SHOW_UNCLASSIFIED_IN_LEGEND = True
UNCLASSIFIED_LABEL = "没有进行省以下财政事权划分改革的城市"

# --- 1.4 输出设置 ---
OUTPUT_BASENAME = "china_city_map"   # 输出文件名（不含扩展名）
TITLE = "中国市级行政区划图"            # 图标题，设为 "" 可隐藏
SAVE_PNG = True
SAVE_PDF = True
DPI = 300

# =============================================================================
# 2. 数据下载（阿里 DataV GeoAtlas）
# =============================================================================

DATAV_URL = "https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json"
CHINA_ADCODE = "100000"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 直辖市、特别行政区、台湾：作为“一个单元”整体显示，不再下钻到区县
SINGLE_UNIT_ADCODES = {
    "110000",  # 北京市
    "120000",  # 天津市
    "310000",  # 上海市
    "500000",  # 重庆市
    "710000",  # 台湾省
    "810000",  # 香港特别行政区
    "820000",  # 澳门特别行政区
}


def is_cached(adcode):
    """判断某个行政区的数据是否已在本地缓存。"""
    return os.path.exists(os.path.join(DATA_DIR, f"{adcode}_full.json"))


def fetch_json(adcode, retries=3):
    """下载某个行政区的 _full GeoJSON，带本地缓存与重试。已有缓存则直接读取，不重新下载。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    cache = os.path.join(DATA_DIR, f"{adcode}_full.json")
    if os.path.exists(cache):
        with open(cache, "r", encoding="utf-8") as f:
            return json.load(f)

    url = DATAV_URL.format(adcode=adcode)
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return data
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"下载失败 adcode={adcode}: {last_err}")


def build_city_geodataframe():
    """组装全国市级 GeoDataFrame。"""
    print("读取缓存" if is_cached(CHINA_ADCODE) else "下载", "全国省级边界...")
    china = fetch_json(CHINA_ADCODE)

    records = []        # 市级记录
    province_geoms = [] # 省级边界（用于画粗的省界）
    boundary_lines = [] # 南海九段线等纯边界线

    for feat in china["features"]:
        props = feat.get("properties", {})
        adcode = str(props.get("adcode"))
        name = props.get("name")
        if not feat.get("geometry"):
            continue

        # 南海九段线：adcode 形如 "100000_JD"，名称为空，单独作为线绘制
        if "_JD" in adcode or not name:
            boundary_lines.append({"geometry": shape(feat["geometry"])})
            continue

        province_geoms.append({"name": name, "geometry": shape(feat["geometry"])})

        if adcode in SINGLE_UNIT_ADCODES:
            # 直辖市/特别行政区/台湾，整体作为一个“市”
            records.append({"city": name, "province": name, "adcode": adcode,
                            "geometry": shape(feat["geometry"])})
            continue

        # 普通省份：下钻获取地级市
        print(f"{'读取缓存' if is_cached(adcode) else '下载'} {name} 的市级边界...")
        try:
            prov = fetch_json(adcode)
        except RuntimeError as e:
            print(f"  跳过 {name}: {e}")
            records.append({"city": name, "province": name, "adcode": adcode,
                            "geometry": shape(feat["geometry"])})
            continue

        for city_feat in prov["features"]:
            if not city_feat.get("geometry"):
                continue
            cprops = city_feat.get("properties", {})
            records.append({
                "city": cprops.get("name"),
                "province": name,
                "adcode": str(cprops.get("adcode")),
                "geometry": shape(city_feat["geometry"]),
            })

    gdf_city = gpd.GeoDataFrame(records, crs="EPSG:4326")
    gdf_prov = gpd.GeoDataFrame(province_geoms, crs="EPSG:4326")
    gdf_line = (gpd.GeoDataFrame(boundary_lines, crs="EPSG:4326")
                if boundary_lines else None)
    return gdf_city, gdf_prov, gdf_line


# =============================================================================
# 3. 配色
# =============================================================================

def resolve_color(province_name):
    """根据所属省份返回填充色（支持省名简写的宽松匹配）。"""
    if not province_name:
        return DEFAULT_COLOR
    if province_name in PROVINCE_CATEGORY:
        return CATEGORY_COLORS.get(PROVINCE_CATEGORY[province_name], DEFAULT_COLOR)
    # 宽松匹配：去掉常见后缀后按前缀比较
    suffixes = ("壮族自治区", "回族自治区", "维吾尔自治区",
                "特别行政区", "自治区", "省", "市")

    def normalize(n):
        for s in suffixes:
            if n.endswith(s):
                return n[: -len(s)]
        return n

    target = normalize(province_name)
    for key, cat in PROVINCE_CATEGORY.items():
        if normalize(key) == target:
            return CATEGORY_COLORS.get(cat, DEFAULT_COLOR)
    return DEFAULT_COLOR


# =============================================================================
# 4. 装饰元素：指北针、比例尺、图例
# =============================================================================

def add_north_arrow(ax, x=0.06, y=0.90, size=0.05):
    """在坐标轴左上角添加菱形指北针。x/y/size 均为 axes 比例。"""
    # 菱形四个顶点：上、右、下、左
    top = (x, y + size)
    right = (x + size * 0.5, y)
    bottom = (x, y - size)
    left = (x - size * 0.5, y)

    # 上半部分填黑（指向北），下半部分填白
    upper = plt.Polygon([top, right, bottom, left], closed=True,
                        facecolor="none", edgecolor="black",
                        lw=1.4, transform=ax.transAxes, zorder=6)
    north_half = plt.Polygon([top, right, bottom], closed=True,
                            facecolor="black", edgecolor="black",
                            lw=1.0, transform=ax.transAxes, zorder=6)
    ax.add_patch(north_half)
    ax.add_patch(upper)

    ax.text(x, y + size + 0.012, "N", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=14, fontweight="bold")


def add_scale_bar(ax, length_km=1000, location=(0.62, 0.06), height=0.012):
    """
    添加比例尺（数据坐标须为投影后的米制坐标）。
    location 为 axes 比例坐标的左端起点；length_km 为总长度。
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x_range = xmax - xmin
    y_range = ymax - ymin

    x0 = xmin + location[0] * x_range
    y0 = ymin + location[1] * y_range
    bar_len = length_km * 1000.0          # km -> m
    bar_h = height * y_range

    half = bar_len / 2.0
    # 黑白相间两段
    ax.add_patch(plt.Rectangle((x0, y0), half, bar_h,
                               facecolor="black", edgecolor="black", zorder=5))
    ax.add_patch(plt.Rectangle((x0 + half, y0), half, bar_h,
                               facecolor="white", edgecolor="black", zorder=5))
    for frac, label in [(0, "0"), (0.5, f"{length_km//2}"), (1.0, f"{length_km}")]:
        ax.text(x0 + bar_len * frac, y0 + bar_h * 1.4, label,
                ha="center", va="bottom", fontsize=9, zorder=6)
    ax.text(x0 + bar_len + bar_len * 0.1, y0 + bar_h * 1.4, "km",
            ha="left", va="bottom", fontsize=9, zorder=6)


def build_legend_handles():
    """根据 CATEGORY_COLORS 生成图例句柄。"""
    handles = [Patch(facecolor=color, edgecolor="black", label=label)
               for label, color in CATEGORY_COLORS.items()]
    if SHOW_UNCLASSIFIED_IN_LEGEND:
        handles.append(Patch(facecolor=DEFAULT_COLOR, edgecolor="black",
                             label=UNCLASSIFIED_LABEL))
    return handles


# =============================================================================
# 5. 主流程
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

    gdf_city, gdf_prov, gdf_line = build_city_geodataframe()

    # 投影到中国常用的 Albers 等积投影（单位：米），让形状正确、比例尺有意义
    albers = ("+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 "
              "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")
    gdf_city = gdf_city.to_crs(albers)
    gdf_prov = gdf_prov.to_crs(albers)
    if gdf_line is not None:
        gdf_line = gdf_line.to_crs(albers)

    # 上色（按所属省份分类）
    gdf_city["fill"] = gdf_city["province"].apply(resolve_color)

    # 绘图
    fig, ax = plt.subplots(figsize=(12, 10))

    gdf_city.plot(ax=ax, color=gdf_city["fill"],
                  edgecolor="#888888", linewidth=0.35, zorder=1)
    # 南海九段线
    if gdf_line is not None:
        gdf_line.plot(ax=ax, color="#333333", linewidth=1.2, zorder=3)

    ax.set_aspect("equal")
    ax.axis("off")

    # 装饰元素
    add_north_arrow(ax)

    legend = ax.legend(
        handles=build_legend_handles(),
        loc="lower left",
        bbox_to_anchor=(0.01, 0.10),
        frameon=False,
        fontsize=11,
    )

    # 比例尺放在图例下方（左下角）
    add_scale_bar(ax, length_km=1000, location=(0.02, 0.04))

    fig.tight_layout()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figure")
    os.makedirs(out_dir, exist_ok=True)
    if SAVE_PNG:
        png = os.path.join(out_dir, OUTPUT_BASENAME + ".png")
        fig.savefig(png, dpi=DPI, bbox_inches="tight")
        print(f"已保存：{png}")
    if SAVE_PDF:
        pdf = os.path.join(out_dir, OUTPUT_BASENAME + ".pdf")
        fig.savefig(pdf, bbox_inches="tight")
        print(f"已保存：{pdf}")

    plt.close(fig)


if __name__ == "__main__":
    main()
