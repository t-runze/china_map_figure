# 中国市级行政区划图生成工具

使用 Python 生成带**指北针**、**比例尺**、**自定义配色**和**图例**的完整中国市级行政区划图，输出高分辨率 PNG 与矢量 PDF，适合论文排版。

边界数据来自[阿里 DataV GeoAtlas](https://datav.aliyun.com/portal/school/atlas/area_selector)，首次运行时在线下载并自动缓存到 `data/` 目录。

## 环境要求

- Python 3.12+
- 依赖见 [requirements.txt](requirements.txt)：`geopandas`、`matplotlib`、`shapely`、`requests`

## 安装依赖

### 方式一：使用 uv（推荐，速度快）

```powershell
# 安装 uv（若尚未安装）：https://docs.astral.sh/uv/
# 创建虚拟环境
uv venv .venv --python 3.12

# 安装依赖
uv pip install -r requirements.txt
```

### 方式二：使用 venv + pip

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活（Windows PowerShell）
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

> macOS / Linux 激活命令为 `source .venv/bin/activate`

## 运行

```powershell
.venv\Scripts\python.exe china_city_map.py
```

首次运行会下载全国省市边界（约 30 个文件，缓存到 `data/`），之后再次运行会直接读取缓存，秒出图。

输出文件保存在 `figure/` 目录：

- `figure/china_city_map.png`（300 dpi）
- `figure/china_city_map.pdf`（矢量）

## 自定义

打开 [china_city_map.py](china_city_map.py)，修改顶部「用户自定义区域」：

| 配置项 | 作用 |
| --- | --- |
| `CATEGORY_COLORS` | 每个类别 → 颜色 + 图例文字 |
| `CITY_CATEGORY` | 城市 → 类别映射（支持带/不带「市」后缀） |
| `DEFAULT_COLOR` | 未分类城市的填充色 |
| `UNCLASSIFIED_LABEL` | 未分类城市的图例标签 |
| `TITLE` | 图标题（设为 `""` 可隐藏） |
| `OUTPUT_BASENAME` | 输出文件名（不含扩展名） |
| `DPI` / `SAVE_PNG` / `SAVE_PDF` | 分辨率与输出格式 |

修改后重新运行脚本即可。

## 直方图生成工具

[histogram.py](histogram.py) 用于生成可自定义的直方图（柱状图），同样输出高分辨率 PNG 与矢量 PDF 到 `figure/` 目录。

### 运行

```powershell
.venv\Scripts\python.exe histogram.py
```

输出文件：

- `figure/histogram.png`（300 dpi）
- `figure/histogram.pdf`（矢量）

### 自定义

打开 [histogram.py](histogram.py)，修改顶部「用户自定义区域」：

| 配置项 | 作用 |
| --- | --- |
| `BAR_LABELS` | 横轴每个方块的子名称（类别标签） |
| `BAR_VALUES` | 每根柱子对应的数值（与 `BAR_LABELS` 一一对应） |
| `X_AXIS_NAME` / `Y_AXIS_NAME` | 横、纵轴名称 |
| `SHOW_TITLE` | 是否显示标题 |
| `TITLE` | 图标题 |
| `BAR_COLORS` | 柱子颜色（单色或与柱子数等长的列表） |
| `SHOW_Y_GRID` | 是否显示纵轴网格线 |
| `GRID_COLOR` / `GRID_LINESTYLE` / `GRID_LINEWIDTH` | 网格线颜色 / 样式 / 宽度 |
| `SHOW_VALUE_LABELS` | 是否在柱顶标注数值 |
| `BAR_WIDTH` / `FIGSIZE` | 柱宽 / 画布尺寸 |
| `OUTPUT_BASENAME` / `DPI` / `SAVE_PDF` | 输出文件名 / 分辨率 / 是否输出 PDF |

修改后重新运行脚本即可。

## 数据来源

行政区划边界数据版权归阿里 DataV 所有，仅供学习与研究使用。
