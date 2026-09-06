# 道路巡查数据质量与病害分布分析

> 个人练习项目 · 求职方向：业务数据分析师
> 分析周期：2026-08-03 ~ 2026-09-03

## 项目背景

某市道路巡查管养平台通过作业车、两轮车、四轮专车、众源车四类渠道采集道路影像，经 AI 识别 + 人工审核后派单给养护单位。本项目基于 21,359 条脱敏模拟案件数据，完成从数据质量核验到业务建议的完整分析闭环。

## 工作流程

```
业务理解 → 数据获取 → 数据质量核验 → EDA探索分析 → 机器学习建模
    → 可视化(Python图 + Power BI看板) → SQL取数验证 → 输出业务建议
```

| 步骤 | 内容 | 工具 |
|---|---|---|
| 1. 业务理解 | 翻译模糊需求，定义4个可分析问题 | - |
| 2. 数据质量核验 | 四维质检：准确性/完整性/规范性/时效性，通过率89.1% | Pandas |
| 3. 帕累托分析 | 病害类型集中度，Top3占49%，长尾分布 | Pandas + Matplotlib |
| 4. 密度归一化 | 总量 vs 件/km 双口径对比，发现口径陷阱 | Pandas + Matplotlib |
| 5. 分组对比 | 4个渠道的通过率、时滞、驳回结构差异 | Pandas + Matplotlib |
| 6. 周期分析 | 一周内案件洪峰识别，周五+52% | Pandas + Matplotlib |
| 7. 机器学习 | 严重等级预测(AUC 0.52) + 日案件量预测(MAPE 3.9%) | scikit-learn |
| 8. Power BI看板 | 3张交互式可视化（渠道/密度/周期） | Power BI |
| 9. SQL取数验证 | 标准数仓SQL，核心指标交叉验证 | Hive/SparkSQL/MySQL |

## 核心发现

| # | 发现 | 建议 |
|---|---|---|
| 1 | 人行道大类占46.3%，路框差+井框差合计37.9% | 路框差/井框差专项批量治理 |
| 2 | 沙荷路密度148件/km为全区最高，被平台"总量排行"掩盖 | 排行增加「案件密度(件/km)」口径 |
| 3 | 众源车通过率仅74%，平均时滞8天，54%超7天 | T+3审核SLA + 机审预筛 |
| 4 | 周五众源跑全域，案件量+52%且质量最差 | 审核排产周五倾斜 + 快审模式 |
| 5 | 两轮车24%因模糊被驳回 | 采集防抖/补光规范 |

## 快速开始

```bash
pip install -r requirements.txt

# 运行描述性分析（输出图表至 report/figures/）
python code/analysis.py

# 运行机器学习模型
python code/analysis_model.py

# 导出Power BI看板数据
python code/powerbi_export.py

# SQL本地验证（将CSV加载到内存SQLite，执行sql/下的脚本验证结论）
python code/analysis_sql.py
```

## 目录结构

```
├── README.md
├── requirements.txt
├── data/
│   └── 模拟案件明细.csv            # 21,359条脱敏模拟数据
├── code/
│   ├── analysis.py                # 核心EDA：帕累托/密度/渠道/周期
│   ├── analysis_model.py          # 机器学习：分类预测 + 回归预测
│   ├── analysis_sql.py            # SQL本地验证（加载CSV到SQLite执行）
│   └── powerbi_export.py          # Power BI看板数据导出
├── sql/
│   ├── 01_ddl.sql                 # 建表语句（Hive/SparkSQL/MySQL兼容）
│   └── 02_analysis.sql            # 分析查询（窗口函数/CTE/行转列）
├── output/                        # 运行时生成（已gitignore）
└── report/
    ├── 道路病害分析看板.pbix       # Power BI交互式看板
    └── figures/                   # 分析图表
        ├── 图1.png                # 病害帕累托分析
        ├── 图2.png                # 道路案件密度排行
        ├── 图3.png                # 渠道质量与时效对比
        ├── 图4.png                # 分星期案件量与来源结构
        ├── 图5.png                # KPI看板复现
        └── 道路病害分析看板.pdf    # Power BI看板导出PDF
```

## SQL说明

`sql/` 目录下的SQL脚本使用标准数仓语法（Hive/SparkSQL/MySQL 8.0+），包含：
- **DDL**：建表语句，字段注释完整，按日期分区
- **分析查询**：7个核心分析问题，使用 CTE、窗口函数（`RANK()`、`SUM() OVER()`）、`CASE WHEN` 行转列、`HAVING` 过滤等

`code/analysis_sql.py` 是本地验证脚本，将CSV加载到内存SQLite后执行等价SQL，验证与Pandas分析结论一致。实际工作中SQL脚本直接在数仓环境执行。

## 数据说明

数据为按平台真实统计口径脱敏模拟的数据（案件总数、病害分布、道路排行、车型结构均锚定真实平台看板），个体案件为随机生成。字段结构与平台导出一致，替换 `data/模拟案件明细.csv` 即可复用分析流程。

## 技术栈

Python（Pandas / Matplotlib / scikit-learn）· SQL（Hive / SparkSQL / MySQL）· Power BI
