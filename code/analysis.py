# -*- coding: utf-8 -*-
"""
道路巡查数据质量与病害分布分析
================================
数据源：data/模拟案件明细.csv（按平台真实统计口径脱敏模拟，可整体替换为真实导出数据）
运行：  python code/analysis.py   （图表输出至 report/figures/）
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / 'report' / 'figures'
FIG.mkdir(parents=True, exist_ok=True)
C = ['#2E86DE','#10AC84','#EE5253','#FF9F43','#5F27CD','#48DBFB','#F36886','#576574']

df = pd.read_csv(ROOT / 'data' / '模拟案件明细.csv', encoding='utf-8-sig')
total_n = len(df)

# ---------- 1. 数据质量核验 ----------
audit = df['审核结论'].value_counts()
print(f"总案件 {total_n}，审核通过 {audit.get('审核通过',0)}（{audit.get('审核通过',0)/total_n*100:.1f}%）")
print("\n驳回原因分布：")
print(df.loc[df['审核结论']=='驳回','驳回原因'].value_counts())

# ---------- 2. 病害类型帕累托 ----------
tc = df.groupby('病害小类').size().sort_values(ascending=False)
cum = tc.cumsum() / tc.sum() * 100
fig, ax = plt.subplots(figsize=(11, 5.2))
top10 = tc.head(10)
ax.bar(top10.index, top10.values, color=C[0])
ax2 = ax.twinx()
ax2.plot(range(10), cum.head(10), color=C[2], marker='o', lw=2)
ax2.axhline(80, ls='--', color='grey', lw=1)
ax.set_ylabel('案件数'); ax2.set_ylabel('累计占比 %')
ax.set_title('图1  病害类型帕累托分析（Top10）')
ax.tick_params(axis='x', rotation=30)
plt.tight_layout(); plt.savefig(FIG / '图1.png', dpi=150); plt.close()
print(f"\nTop3 病害累计占比 {cum.iloc[2]:.1f}%，Top5 {cum.iloc[4]:.1f}%")

# ---------- 3. 道路案件密度 ----------
rd = df.groupby(['道路名称','里程km']).size().reset_index(name='案件数')
rd['案件密度(件/km)'] = (rd['案件数'] / rd['里程km']).round(1)
rd = rd.sort_values('案件密度(件/km)')
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.barh(rd['道路名称'], rd['案件密度(件/km)'], color=C[1])
ax.set_xlabel('案件密度（件/km）'); ax.set_title('图2  道路案件密度排行')
plt.tight_layout(); plt.savefig(FIG / '图2.png', dpi=150); plt.close()
print("\n案件密度 Top3 道路：")
print(rd.tail(3).iloc[::-1].to_string(index=False))

# ---------- 4. 数据来源质量与时效 ----------
g = df.groupby('数据来源').agg(
    案件量=('案件ID', 'size'),
    通过率=('审核结论', lambda s: round((s=='审核通过').mean()*100, 1)),
    平均时滞天=('审核时滞天', 'mean')).round(1)
reason = (df[df['审核结论']=='驳回'].groupby(['数据来源','驳回原因']).size()
          .unstack(fill_value=0))
reason_pct = (reason.div(reason.sum(axis=1), axis=0)*100).round(1)
order = ['作业车','四轮专车','两轮车','众源车']
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
axes[0].bar(order, g.loc[order,'通过率'], color=C[:4]); axes[0].set_ylim(0, 105)
axes[0].set_title('各车型来源 · 审核通过率')
bottom = np.zeros(4)
for j, col in enumerate(reason_pct.columns):
    axes[1].bar(order, reason_pct.loc[order, col], bottom=bottom, label=col, color=C[j+2])
    bottom += reason_pct.loc[order, col].values
axes[1].set_title('驳回原因构成（%）'); axes[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(FIG / '图3.png', dpi=150); plt.close()
print("\n渠道质量："); print(g.loc[order])
print("\n驳回原因构成 %："); print(reason_pct.loc[order])

# ---------- 5. 周期规律 ----------
wk = (df.groupby(['星期','数据来源']).size().unstack(fill_value=0)
        .reindex(['周一','周二','周三','周四','周五','周六','周日']))
fig, ax = plt.subplots(figsize=(10, 4.6))
bottom = np.zeros(7)
for j, s in enumerate(['作业车','两轮车','四轮专车','众源车']):
    ax.bar(wk.index, wk[s], bottom=bottom, label=s, color=C[j])
    bottom += wk[s].values
ax.set_ylabel('案件数'); ax.legend(ncol=4, fontsize=9)
ax.set_title('图4  分星期案件量与来源结构')
plt.tight_layout(); plt.savefig(FIG / '图4.png', dpi=150); plt.close()
zy = df[df['数据来源']=='众源车']
print(f"\n众源车平均时滞 {zy['审核时滞天'].mean():.1f} 天，时滞>7天占比 {(zy['审核时滞天']>7).mean()*100:.1f}%")

print("\n分析完成，图表已输出至 report/figures/")
