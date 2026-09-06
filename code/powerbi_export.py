# -*- coding: utf-8 -*-
"""
Power BI 看板数据导出
====================
导出3张CSV，Power BI Desktop → 获取数据 → CSV → 直接拖拽出图：
  1. chart1_channel_pass_rate.csv  — 渠道通过率（条形图）
  2. chart2_road_density.csv       — 道路案件密度（条形图）
  3. chart3_weekly_trend.csv       — 分星期案件量趋势（堆叠柱状图）
运行：python code/powerbi_export.py
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / 'data' / '模拟案件明细.csv', encoding='utf-8-sig')

# ---------- 图1：渠道通过率 ----------
ch = df.groupby('数据来源').agg(
    案件量=('案件ID', 'size'),
    通过量=('审核结论', lambda s: (s == '审核通过').sum()),
).reset_index()
ch['通过率%'] = (ch['通过量'] / ch['案件量'] * 100).round(1)
ch = ch.sort_values('通过率%', ascending=False)
ch.to_csv(OUT / 'chart1_channel_pass_rate.csv', index=False, encoding='utf-8-sig')
print("[OK] chart1_channel_pass_rate.csv")

# ---------- 图2：道路案件密度 ----------
rd = df.groupby(['道路名称', '里程km']).agg(
    案件总数=('案件ID', 'size')
).reset_index()
rd['案件密度_件每km'] = (rd['案件总数'] / rd['里程km']).round(1)
rd = rd.sort_values('案件密度_件每km', ascending=False)
rd.to_csv(OUT / 'chart2_road_density.csv', index=False, encoding='utf-8-sig')
print("[OK] chart2_road_density.csv")

# ---------- 图3：分星期趋势（分来源堆叠） ----------
wk = df.groupby(['星期', '数据来源']).size().reset_index(name='案件数')
wk_order = {'周一': 1, '周二': 2, '周三': 3, '周四': 4, '周五': 5, '周六': 6, '周日': 7}
wk['排序'] = wk['星期'].map(wk_order)
wk = wk.sort_values(['排序', '数据来源']).drop(columns='排序')
wk.to_csv(OUT / 'chart3_weekly_trend.csv', index=False, encoding='utf-8-sig')
print("[OK] chart3_weekly_trend.csv")

print(f"\n3张CSV已导出至 {OUT}")
print("打开 Power BI Desktop → 获取数据 → 文件夹/CSV → 选择上述文件 → 创建可视化")
