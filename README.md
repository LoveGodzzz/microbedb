# 🧫 MicrobeDB — 微生物生信数据库在线演示

一个以**微生物生信数据**为业务背景的数据库应用：菌株档案 → 测序 → 基因组组装 →
基因注释 / 耐药基因 / 毒力因子，外加药敏表型与分析任务管理。
**在线版**（本仓库）使用 SQLite + Streamlit；**本地完整版**使用 MySQL 8.0 + Flask（见下）。

> ⚠️ 所有数据由脚本生成（固定随机种子，可复现），数值参考真实生物学范围——
> 基因组大小、GC 含量符合物种实际区间，**耐药基因与药敏结果保持生物学一致性**
> （如 mecA ↔ 苯唑西林耐药）。仅为教学演示，不可用于真实研究。

## 在线运行（Streamlit Cloud）

1. Fork 或推送本仓库到 GitHub
2. 打开 [share.streamlit.io](https://share.streamlit.io) → New app → 选择仓库
   - Main file path: `app.py`
3. 部署完成，获得 `https://<你的应用名>.streamlit.app`

数据文件 `microbe.db`（约 1.5 MB）已随仓库提供，冷启动无需重建。
想改数据量：修改 `seed_core.py` 后运行 `python build_db.py` 重新生成。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 功能页面

| 页面 | 内容 |
|------|------|
| 📊 总览仪表盘 | 菌株/测序/组装/基因/耐药统计卡片，物种分布、来源分布、采样趋势图 |
| 🧪 菌株库 | 多条件检索（编号/物种/来源），菌株详情：分类谱系（递归 CTE）、测序与组装、药敏表型（S/I/R 着色）、耐药与毒力 |
| 🧬 基因组注释 | 组装质量指标（N50/GC/完整度），基因列表分页浏览与功能检索 |
| 💊 耐药分析 | 耐药率排行、耐药机制分布、物种×药物耐药率矩阵、耐药基因 Top 榜 |
| 🔬 真实数据对比 | 导入 NCBI RefSeq 真实参考基因组元数据（每物种 30 个），与模拟数据对比大小/GC/N50 分布 |
| 📤 上传比对 | **访客上传自己的数据直接比对**：FASTA 文件现场计算大小/GC/N50 并给出百分位与物种推荐；或上传 CSV/TSV 批量统计表对比。文件只在内存中处理，不保存 |
| ⚙️ 分析任务 | 任务列表/筛选、提交任务、状态流转并记录审计日志 |

## 数据模型

```
taxonomy(自引用分类树) ─┬─→ strains(菌株) ─┬─→ sequencing_runs(测序) ─→ assemblies(组装)
                        │                  │        ├─→ genes(基因注释, 8k+ 条, 生成列 length_bp)
                        │                  │        ├─→ amr_hits(耐药基因)
                        │                  │        └─→ vf_hits(毒力因子)
                        │                  ├─→ phenotypes(药敏 S/I/R)
                        │                  └─→ pipeline_jobs(任务) ─→ job_events(审计日志)
```

11 张表 + 3 个视图，保留 CHECK 约束、UNIQUE 约束、生成列、递归 CTE、窗口函数等特性；
SQL 查询散布在 `app.py` 中，从单表筛选到多表 JOIN、条件聚合、递归 CTE 都有实际用例。

## 本地完整版（MySQL + Flask）

同一数据模型还有一版**本地全栈实现**（不在本仓库内）：便携版 MySQL 8.0（端口 3307）+
Flask REST API + 原生 JS/ECharts 前端，额外演示触发器审计、存储过程、FULLTEXT 全文索引、
JSON 字段等 MySQL 特性，并附 ER 图、数据字典与 20 道 SQL 练习题。

## 目录结构

```
├── app.py              # Streamlit 应用（全部页面与 SQL 查询）
├── seed_core.py        # 模拟数据生成逻辑（固定种子，可复现）
├── build_db.py         # 构建 SQLite：schema(约束/视图) + 数据
├── fetch_reference.py  # 从 NCBI Datasets API 拉取真实 RefSeq 元数据
├── refseq_reference.json  # 真实参考基因组数据（已随仓库提供）
├── microbe.db          # 预生成的 SQLite 数据库（可直接用）
├── sample_genome.fna.gz   # 示例基因组（可用于测试上传比对）
└── requirements.txt
```

## 更新真实参照数据

```bash
python fetch_reference.py   # 重新从 NCBI 拉取（每个物种 30 个 RefSeq 基因组）
python build_db.py          # 重建 microbe.db
```
