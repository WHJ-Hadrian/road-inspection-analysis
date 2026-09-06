# -*- coding: utf-8 -*-
"""
机器学习：严重等级预测（审核优先级）+ 日案件量预测（排产）
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / 'data' / '模拟案件明细.csv', encoding='utf-8-sig')

# ====================================================================
# 模型1：严重等级预测（二分类 → 审核优先级排序）
# ====================================================================
# 业务目标：在案件进入审核队列前，预测哪些案件可能是"严重"等级，
#           让审核员优先处理高风险案件，缩短严重案件的响应时间。
#
# 关键设计决策：
#   - 目标变量：事件等级 == '严重' → 1，否则 0
#   - 正样本比例：686 / 21359 = 3.2%（严重不平衡）
#   - 评估指标：AUC（而非 accuracy）
#     原因：全预测非严重也能拿到96.8%准确率，accuracy在不平衡数据上无意义
#   - 类别权重：class_weight='balanced'，自动按样本比例加权
# ====================================================================

feat = ['病害大类', '数据来源', '星期', '道路名称']
X, y = df[feat], (df['事件等级'] == '严重').astype(int)

print("=" * 60)
print("模型1：严重等级预测（审核优先级）")
print(f"  样本总量: {len(y)}，正样本(严重): {y.sum()} ({y.mean()*100:.1f}%)")
print("=" * 60)

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

pre = ColumnTransformer([('oh', OneHotEncoder(handle_unknown='ignore'), feat)])

for name, mdl in [
    ('逻辑回归', LogisticRegression(max_iter=1000, class_weight='balanced')),
    ('随机森林', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)),
]:
    pipe = Pipeline([('pre', pre), ('m', mdl)]).fit(X_tr, y_tr)
    y_prob = pipe.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, y_prob)
    print(f"\n  [{name}] AUC = {auc:.3f}")

    if name == '随机森林':
        importances = pipe.named_steps['m'].feature_importances_
        feature_names = pipe.named_steps['pre'].get_feature_names_out()
        fi = pd.Series(importances, index=feature_names).sort_values(ascending=False)
        print(f"  特征重要性 Top5:")
        for fname, imp in fi.head(5).items():
            print(f"    {fname}: {imp:.4f}")

    if name == '逻辑回归':
        coefs = pipe.named_steps['m'].coef_[0]
        feature_names = pipe.named_steps['pre'].get_feature_names_out()
        top_idx = np.argsort(np.abs(coefs))[::-1][:5]
        print(f"  系数绝对值 Top5:")
        for idx in top_idx:
            print(f"    {feature_names[idx]}: {coefs[idx]:.4f}")

# ====================================================================
# 模型2：日案件量预测（时间序列回归 → 审核排产）
# ====================================================================
# 业务目标：预测未来每天的案件量，帮助审核主管安排次日人力。
#
# 关键发现：
#   - 基线模型（仅用时间趋势t）：MAPE = 21.9%
#   - 加入星期特征后：MAPE = 3.9%（降幅82%）
#   - 说明星期周期是案件量波动的第一驱动因素（众源车周五跑全域）
# ====================================================================

print("\n" + "=" * 60)
print("模型2：日案件量预测（审核排产）")
print("=" * 60)

daily = df.groupby('采集日期').size().reset_index(name='y')
daily['ds'] = pd.to_datetime(daily['采集日期'])
daily['t'] = (daily['ds'] - daily['ds'].min()).dt.days
daily['weekday'] = daily['ds'].dt.dayofweek

tr = daily[daily['t'] < 21].copy()
te = daily[daily['t'] >= 21].copy()

tr_d = pd.get_dummies(tr[['t', 'weekday']], columns=['weekday'], drop_first=True)
te_d = pd.get_dummies(te[['t', 'weekday']], columns=['weekday'], drop_first=True).reindex(
    columns=tr_d.columns, fill_value=0
)

m1 = LinearRegression().fit(tr[['t']], tr['y'])
m2 = LinearRegression().fit(tr_d, tr['y'])

mape = lambda a, p: (abs(a - p) / a).mean() * 100
mape_base = mape(te['y'], m1.predict(te[['t']]))
mape_full = mape(te['y'], m2.predict(te_d))

print(f"  训练集: {len(tr)}天, 测试集: {len(te)}天")
print(f"  基线MAPE（仅时间趋势）: {mape_base:.1f}%")
print(f"  完整MAPE（+星期特征）:   {mape_full:.1f}%")
print(f"  降幅: {(1 - mape_full/mape_base)*100:.0f}%")
