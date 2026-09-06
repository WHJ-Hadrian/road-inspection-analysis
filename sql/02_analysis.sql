-- ============================================================
-- 道路巡查数据质量与病害分布分析
-- 语法：Hive / SparkSQL / MySQL 8.0+（仅需微调方言差异）
-- ============================================================

-- ************************************************************
-- Q1 数据质量核验：总体通过率 + 驳回原因分布
-- 知识点：CASE WHEN 条件聚合、窗口函数 SUM() OVER()
-- ************************************************************
SELECT
    COUNT(*)                                          AS total_cases,
    SUM(CASE WHEN audit_result = '审核通过' THEN 1 ELSE 0 END) AS pass_cases,
    ROUND(SUM(CASE WHEN audit_result = '审核通过' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pass_rate
FROM dim_road_case;

SELECT
    reject_reason,
    COUNT(*)                                          AS reject_cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS reject_pct
FROM dim_road_case
WHERE audit_result = '驳回'
GROUP BY reject_reason
ORDER BY reject_cnt DESC;


-- ************************************************************
-- Q2 帕累托分析：病害类型 Top10 + 累计占比
-- 知识点：GROUP BY + 窗口函数 SUM() OVER(ORDER BY) 做累计求和
-- ************************************************************
WITH disease_stats AS (
    SELECT
        disease_sub,
        COUNT(*) AS case_cnt
    FROM dim_road_case
    GROUP BY disease_sub
)
SELECT
    disease_sub,
    case_cnt,
    ROUND(SUM(case_cnt) OVER (ORDER BY case_cnt DESC) * 100.0
          / SUM(case_cnt) OVER (), 1) AS cum_pct
FROM disease_stats
ORDER BY case_cnt DESC
LIMIT 10;


-- ************************************************************
-- Q3 道路案件密度：总量 vs 密度双口径对比
-- 知识点：GROUP BY 多字段 + 窗口函数 RANK() 做排名
-- ************************************************************
WITH road_stats AS (
    SELECT
        road_name,
        road_length_km,
        COUNT(*) AS total_cases,
        ROUND(COUNT(*) * 1.0 / road_length_km, 1) AS case_density
    FROM dim_road_case
    GROUP BY road_name, road_length_km
)
SELECT
    road_name,
    road_length_km,
    total_cases,
    case_density,
    RANK() OVER (ORDER BY total_cases DESC)   AS rank_by_total,
    RANK() OVER (ORDER BY case_density DESC)  AS rank_by_density
FROM road_stats
ORDER BY case_density DESC;


-- ************************************************************
-- Q4 渠道质量对比：通过率 + 时滞 + 驳回结构
-- 知识点：多维 GROUP BY + 子查询拼接 + CASE WHEN 行转列
-- ************************************************************
-- 4a. 各渠道通过率与时滞
SELECT
    source_channel,
    COUNT(*) AS case_cnt,
    ROUND(SUM(CASE WHEN audit_result = '审核通过' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pass_rate,
    ROUND(AVG(audit_delay_days), 1) AS avg_delay_days,
    SUM(CASE WHEN audit_delay_days > 7 THEN 1 ELSE 0 END) AS delay_over_7d,
    ROUND(SUM(CASE WHEN audit_delay_days > 7 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS delay_over_7d_pct
FROM dim_road_case
GROUP BY source_channel
ORDER BY pass_rate DESC;

-- 4b. 各渠道驳回原因构成（行转列）
SELECT
    source_channel,
    ROUND(SUM(CASE WHEN reject_reason = 'AI误报'     THEN 1 ELSE 0 END) * 100.0
          / NULLIF(SUM(CASE WHEN audit_result = '驳回' THEN 1 ELSE 0 END), 0), 1) AS pct_ai_error,
    ROUND(SUM(CASE WHEN reject_reason = '模糊不清'   THEN 1 ELSE 0 END) * 100.0
          / NULLIF(SUM(CASE WHEN audit_result = '驳回' THEN 1 ELSE 0 END), 0), 1) AS pct_blur,
    ROUND(SUM(CASE WHEN reject_reason = '框选不规范' THEN 1 ELSE 0 END) * 100.0
          / NULLIF(SUM(CASE WHEN audit_result = '驳回' THEN 1 ELSE 0 END), 0), 1) AS pct_bad_frame,
    ROUND(SUM(CASE WHEN reject_reason = '超过时效'   THEN 1 ELSE 0 END) * 100.0
          / NULLIF(SUM(CASE WHEN audit_result = '驳回' THEN 1 ELSE 0 END), 0), 1) AS pct_timeout
FROM dim_road_case
GROUP BY source_channel
ORDER BY source_channel;


-- ************************************************************
-- Q5 周期分析：分星期 × 分来源案件量
-- 知识点：CASE WHEN 行转列做交叉表
-- ************************************************************
SELECT
    weekday,
    SUM(CASE WHEN source_channel = '作业车'   THEN 1 ELSE 0 END) AS 作业车,
    SUM(CASE WHEN source_channel = '两轮车'   THEN 1 ELSE 0 END) AS 两轮车,
    SUM(CASE WHEN source_channel = '四轮专车' THEN 1 ELSE 0 END) AS 四轮专车,
    SUM(CASE WHEN source_channel = '众源车'   THEN 1 ELSE 0 END) AS 众源车,
    COUNT(*) AS total
FROM dim_road_case
GROUP BY weekday
ORDER BY CASE weekday
    WHEN '周一' THEN 1 WHEN '周二' THEN 2 WHEN '周三' THEN 3
    WHEN '周四' THEN 4 WHEN '周五' THEN 5 WHEN '周六' THEN 6 WHEN '周日' THEN 7
END;


-- ************************************************************
-- Q6 严重案件分布：哪些病害+道路的严重案件最多
-- 知识点：多维聚合 + HAVING 过滤 + 排名
-- ************************************************************
SELECT
    disease_main,
    road_name,
    COUNT(*) AS severe_cnt
FROM dim_road_case
WHERE event_level = '严重'
GROUP BY disease_main, road_name
HAVING COUNT(*) >= 10
ORDER BY severe_cnt DESC
LIMIT 15;


-- ************************************************************
-- Q7 众源车时效风险：超时案件的时间分布
-- 知识点：日期函数 + 条件过滤 + 窗口函数
-- ************************************************************
SELECT
    collect_date,
    COUNT(*) AS total,
    SUM(CASE WHEN audit_result = '驳回' THEN 1 ELSE 0 END) AS rejected,
    SUM(CASE WHEN reject_reason = '超过时效' THEN 1 ELSE 0 END) AS timeout_cnt,
    ROUND(AVG(audit_delay_days), 1) AS avg_delay
FROM dim_road_case
WHERE source_channel = '众源车'
GROUP BY collect_date
ORDER BY collect_date;
