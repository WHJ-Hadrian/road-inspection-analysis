# -*- coding: utf-8 -*-
"""
SQL 分析本地验证
===============
本脚本仅用于本地验证 sql/ 目录下的SQL脚本结论一致性。
实际工作中，SQL脚本直接在 Hive/SparkSQL/MySQL 数仓环境执行。
"""
import pandas as pd
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / 'data' / '模拟案件明细.csv', encoding='utf-8-sig')
con = sqlite3.connect(':memory:')
df.to_sql('dim_road_case', con, index=False)

QUERIES = [
    ("Q1 总体通过率", """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN "审核结论"='审核通过' THEN 1 ELSE 0 END) AS pass_cnt,
               ROUND(SUM(CASE WHEN "审核结论"='审核通过' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS pass_rate
        FROM dim_road_case"""),

    ("Q2 驳回原因分布", """
        SELECT "驳回原因", COUNT(*) AS cnt,
               ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct
        FROM dim_road_case WHERE "审核结论"='驳回'
        GROUP BY "驳回原因" ORDER BY cnt DESC"""),

    ("Q3 帕累托Top10", """
        SELECT "病害小类", COUNT(*) AS cnt,
               ROUND(SUM(COUNT(*)) OVER(ORDER BY COUNT(*) DESC)*100.0/SUM(COUNT(*)) OVER(),1) AS cum_pct
        FROM dim_road_case GROUP BY "病害小类" ORDER BY cnt DESC LIMIT 10"""),

    ("Q4 道路密度双口径", """
        SELECT "道路名称","里程km", COUNT(*) AS total,
               ROUND(COUNT(*)*1.0/"里程km",1) AS density,
               RANK() OVER (ORDER BY COUNT(*) DESC) AS rank_total,
               RANK() OVER (ORDER BY COUNT(*)*1.0/"里程km" DESC) AS rank_density
        FROM dim_road_case GROUP BY "道路名称","里程km" ORDER BY density DESC"""),

    ("Q5 渠道质量", """
        SELECT "数据来源", COUNT(*) AS cnt,
               ROUND(SUM(CASE WHEN "审核结论"='审核通过' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS pass_rate,
               ROUND(AVG("审核时滞天"),1) AS avg_delay,
               ROUND(SUM(CASE WHEN "审核时滞天">7 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS delay_gt7d_pct
        FROM dim_road_case GROUP BY "数据来源" ORDER BY pass_rate DESC"""),

    ("Q6 分星期案件量", """
        SELECT "星期",
               SUM(CASE WHEN "数据来源"='作业车' THEN 1 ELSE 0 END) AS 作业车,
               SUM(CASE WHEN "数据来源"='两轮车' THEN 1 ELSE 0 END) AS 两轮车,
               SUM(CASE WHEN "数据来源"='四轮专车' THEN 1 ELSE 0 END) AS 四轮专车,
               SUM(CASE WHEN "数据来源"='众源车' THEN 1 ELSE 0 END) AS 众源车,
               COUNT(*) AS 合计
        FROM dim_road_case GROUP BY "星期"
        ORDER BY CASE "星期" WHEN '周一' THEN 1 WHEN '周二' THEN 2 WHEN '周三' THEN 3
                 WHEN '周四' THEN 4 WHEN '周五' THEN 5 WHEN '周六' THEN 6 WHEN '周日' THEN 7 END"""),
]

if __name__ == '__main__':
    print("以下SQL结果可与 analysis.py 的 Pandas 分析结果交叉验证\n")
    for title, sql in QUERIES:
        print(f"===== {title} =====")
        print(pd.read_sql(sql, con).to_string(index=False))
        print()
    con.close()
