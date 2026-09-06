-- ============================================================
-- 道路巡查案件表 DDL
-- 语法兼容：Hive / SparkSQL / MySQL 8.0+
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_road_case (
    case_id         STRING      COMMENT '案件ID，平台唯一编号',
    disease_sub     STRING      COMMENT '病害小类，31种',
    disease_main    STRING      COMMENT '病害大类，7种归并',
    road_name       STRING      COMMENT '道路名称',
    road_length_km  DECIMAL(5,1) COMMENT '道路管养里程(km)',
    source_channel  STRING      COMMENT '数据来源：作业车/两轮车/四轮专车/众源车',
    collect_date    DATE        COMMENT '采集日期',
    weekday         STRING      COMMENT '星期：周一~周日',
    audit_result    STRING      COMMENT '审核结论：审核通过/驳回',
    reject_reason   STRING      COMMENT '驳回原因：AI误报/模糊不清/框选不规范/超过时效',
    event_level     STRING      COMMENT '事件等级：严重/轻微',
    audit_delay_days INT        COMMENT '审核时滞天数：采集日期→审核完成日期间隔'
)
COMMENT '道路巡查案件明细表'
PARTITIONED BY (dt STRING COMMENT '数据日期分区')
STORED AS PARQUET;
