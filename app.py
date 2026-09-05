# -*- coding: utf-8 -*-
"""MicrobeDB —— 微生物生信数据库在线演示（Streamlit + SQLite）

GitHub 仓库入口：app.py | 数据：microbe.db（由 build_db.py 预生成，模拟数据）
"""
import os
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="MicrobeDB 微生物生信数据库", page_icon="🧫", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "microbe.db")

ACCENT = "#0e7490"
PALETTE = ["#0e7490", "#16697a", "#2563eb", "#7c3aed", "#d97706", "#16a34a", "#dc2626", "#64748b"]


# ---------------- 数据访问 ----------------
@st.cache_data(ttl=60)
def q(sql, params=()) -> pd.DataFrame:
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def exec_sql(sql, params=()):
    with sqlite3.connect(DB) as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def lineage_of(taxon_id):
    rows = q("""WITH RECURSIVE up AS (
                    SELECT taxon_id, tax_rank, name, parent_id FROM taxonomy WHERE taxon_id=?
                    UNION ALL
                    SELECT t.taxon_id, t.tax_rank, t.name, t.parent_id
                    FROM taxonomy t JOIN up u ON t.taxon_id = u.parent_id)
                SELECT tax_rank, name FROM up ORDER BY taxon_id""", (taxon_id,))
    cn = {"kingdom": "界", "phylum": "门", "class": "纲", "order": "目",
          "family": "科", "genus": "属", "species": "种"}
    return " ＞ ".join(f"{cn[r.tax_rank]}{r.name}" for r in rows.itertuples())


def fmt_mb(n):
    return f"{n / 1e6:.2f} Mb" if n and n >= 1e6 else "0 Mb"


# ---------------- 页面：总览 ----------------
def page_dashboard():
    c = q("""SELECT
        (SELECT COUNT(*) FROM strains) strains,
        (SELECT COUNT(*) FROM sequencing_runs) runs,
        (SELECT COUNT(*) FROM assemblies WHERE status='succeeded') assemblies,
        (SELECT COUNT(*) FROM genes) genes,
        (SELECT COUNT(*) FROM amr_hits) amr,
        (SELECT COUNT(DISTINCT strain_id) FROM phenotypes WHERE interpretation='R') resistant,
        (SELECT COALESCE(SUM(base_count),0)/1e9 FROM sequencing_runs) gb,
        (SELECT COUNT(*) FROM pipeline_jobs WHERE status IN ('running','queued')) active""").iloc[0]

    cols = st.columns(4)
    items = [("🧪", int(c.strains), "菌株总数"), ("📡", int(c.runs), "测序批次"),
             ("🧬", int(c.assemblies), "成功组装基因组"), ("🧫", int(c.genes), "基因注释条数"),
             ("💊", int(c.amr), "耐药基因检出"), ("⚠️", int(c.resistant), "携带耐药表型菌株"),
             ("💾", f"{float(c.gb):.1f} Gb", "测序数据总量"), ("⚙️", int(c.active), "进行中任务")]
    for col, (ico, num, label) in zip(cols * 2, items):
        with col:
            st.markdown(f"### {ico} {num}\n{label}" if not isinstance(num, str)
                        else f"### {ico} {num}\n{label}")

    left, right = st.columns(2)
    with left:
        st.subheader("菌株物种分布")
        df = q("""SELECT t.name AS 物种, COUNT(*) AS 菌株数 FROM strains s
                  JOIN taxonomy t ON t.taxon_id = s.taxon_id
                  WHERE t.tax_rank='species' GROUP BY t.name""")
        st.plotly_chart(px.pie(df, names="物种", values="菌株数", hole=0.45,
                               color_discrete_sequence=PALETTE),
                        use_container_width=True)
    with right:
        st.subheader("样本来源类型")
        df = q("SELECT source_type AS 来源, COUNT(*) AS 数量 FROM strains GROUP BY 1 ORDER BY 2 DESC")
        st.plotly_chart(px.bar(df, x="来源", y="数量", color_discrete_sequence=[ACCENT]),
                        use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("采样趋势（按月）")
        df = q("""SELECT substr(collected_date, 1, 7) AS 月份, COUNT(*) AS 菌株数
                  FROM strains WHERE collected_date IS NOT NULL GROUP BY 1 ORDER BY 1""")
        st.plotly_chart(px.line(df, x="月份", y="菌株数", markers=True,
                                color_discrete_sequence=[ACCENT]),
                        use_container_width=True)
    with right:
        st.subheader("最近分析任务")
        df = q("""SELECT j.job_id AS 任务号, s.isolate_code AS 菌株, t.name AS 物种,
                         j.pipeline AS 流程, j.status AS 状态, j.queued_at AS 提交时间
                  FROM pipeline_jobs j
                  JOIN strains s ON s.strain_id = j.strain_id
                  JOIN taxonomy t ON t.taxon_id = s.taxon_id
                  ORDER BY j.queued_at DESC LIMIT 8""")
        st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------- 页面：菌株库 ----------------
def page_strains():
    st.subheader("菌株库")
    f1, f2, f3 = st.columns([2, 2, 1.4])
    kw = f1.text_input("搜索（编号 / 来源细节 / 地点）", key="sq")
    species = f2.selectbox("物种", ["全部"] + list(
        q("SELECT name FROM taxonomy WHERE tax_rank='species' ORDER BY name").name))
    source = f3.selectbox("来源", ["全部", "clinical", "environmental", "food", "animal", "laboratory"])

    where, params = ["1=1"], []
    if kw:
        where.append("(s.isolate_code LIKE ? OR s.source_detail LIKE ? OR s.location LIKE ?)")
        params += [f"%{kw}%"] * 3
    if species != "全部":
        where.append("t.name = ?")
        params.append(species)
    if source != "全部":
        where.append("s.source_type = ?")
        params.append(source)
    W = " AND ".join(where)

    df = q(f"""
        SELECT o.strain_id, o.isolate_code AS 编号, o.species_name AS 物种,
               o.source_type AS 来源, o.source_detail AS 来源细节, o.location AS 地点,
               o.collected_date AS 采样日期, o.run_cnt AS 测序, o.asm_cnt AS 组装,
               o.pheno_cnt AS 药敏, o.amr_cnt AS 耐药基因, o.vf_cnt AS 毒力因子
        FROM v_strain_overview o
        JOIN strains s ON s.strain_id = o.strain_id
        JOIN taxonomy t ON t.taxon_id = s.taxon_id
        WHERE {W} ORDER BY o.strain_id""", params)
    st.caption(f"共 {len(df)} 株")
    st.dataframe(df.drop(columns=["strain_id"]), use_container_width=True,
                 height=420, hide_index=True)

    st.divider()
    sid = st.selectbox("选择菌株查看详情", df["编号"],
                       index=0 if len(df) else None,
                       disabled=not len(df))
    if not sid:
        return
    detail_strain(int(df.loc[df["编号"] == sid, "strain_id"].iloc[0]))


def detail_strain(sid):
    s = q("""SELECT s.*, t.name AS species_name
             FROM strains s JOIN taxonomy t ON t.taxon_id = s.taxon_id
             WHERE s.strain_id=?""", (sid,)).iloc[0]
    st.markdown(f"### `{s.isolate_code}`　<i>{s.species_name}</i>", unsafe_allow_html=True)
    st.caption(lineage_of(int(s.taxon_id)))

    t1, t2, t3, t4 = st.tabs(["🧪 基本信息", "📡 测序与组装", "💊 药敏表型", "🧬 耐药与毒力"])
    with t1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("来源类型", s.source_type)
        c2.metric("来源细节", s.source_detail or "-")
        c3.metric("采样地点", s.location or "-")
        c4.metric("采样日期", str(s.collected_date or "-"))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("采样人", s.collector or "-")
        c2.metric("冻存位置", s.storage_box or "-")
        c3.metric("备注", (s.notes or "-"))
    with t2:
        runs = q("SELECT * FROM sequencing_runs WHERE strain_id=? ORDER BY run_id", (sid,))
        asms = q("""SELECT a.*, r.platform FROM assemblies a
                    JOIN sequencing_runs r ON r.run_id = a.run_id
                    WHERE r.strain_id=? ORDER BY a.assembly_id""", (sid,))
        st.markdown("**测序批次**")
        st.dataframe(runs[["run_id", "platform", "read_type", "read_count", "base_count",
                           "q30_rate", "run_date", "status"]]
                     .rename(columns={"run_id": "批次", "platform": "平台", "read_type": "类型",
                                      "read_count": "读段数", "base_count": "碱基数",
                                      "q30_rate": "Q30", "run_date": "日期", "status": "状态"}),
                     use_container_width=True, hide_index=True)
        st.markdown("**基因组组装**")
        if len(asms):
            asms["总长"] = asms.total_length.map(fmt_mb)
            asms["N50"] = (asms.n50 / 1000).round(0).astype(int).astype(str) + " kb"
            st.dataframe(asms[["assembly_id", "platform", "assembler", "contig_count",
                               "总长", "N50", "gc_content", "completeness", "status"]]
                         .rename(columns={"assembly_id": "组装", "platform": "平台",
                                          "assembler": "软件", "contig_count": "Contigs",
                                          "gc_content": "GC%", "completeness": "完整度%",
                                          "status": "状态"}),
                         use_container_width=True, hide_index=True)
        else:
            st.info("该菌株暂无成功组装")
    with t3:
        ph = q("""SELECT antibiotic AS 药物, method AS 方法, mic_mg_l AS 'MIC(mg/L)',
                         zone_mm AS '抑菌圈(mm)', interpretation AS 判读, tested_at AS 日期, lab AS 实验室
                  FROM phenotypes WHERE strain_id=? ORDER BY antibiotic""", (sid,))
        if len(ph):
            def color_i(v):
                return {"S": "background:#dcfce7", "I": "background:#fef3c7",
                        "R": "background:#fee2e2"}.get(v, "")
            st.dataframe(ph.style.map(color_i, subset=["判读"]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("无药敏数据")
    with t4:
        l, r = st.columns(2)
        with l:
            st.markdown("**耐药基因（AMR）**")
            am = q("""SELECT gene_symbol AS 基因, drug_class AS 类别, mechanism AS 机制,
                             identity_pct AS '一致性%', database_name AS 数据库
                      FROM amr_hits h
                      JOIN assemblies a ON a.assembly_id = h.assembly_id
                      JOIN sequencing_runs r ON r.run_id = a.run_id
                      WHERE r.strain_id=?""", (sid,))
            if len(am):
                st.dataframe(am, use_container_width=True, hide_index=True)
            else:
                st.info("未检出")
        with r:
            st.markdown("**毒力因子（VF）**")
            vf = q("""SELECT vf_name AS 因子, category AS 类别, description AS 说明,
                             identity_pct AS '一致性%'
                      FROM vf_hits v
                      JOIN assemblies a ON a.assembly_id = v.assembly_id
                      JOIN sequencing_runs r ON r.run_id = a.run_id
                      WHERE r.strain_id=?""", (sid,))
            if len(vf):
                st.dataframe(vf, use_container_width=True, hide_index=True)
            else:
                st.info("未检出")


# ---------------- 页面：基因组注释 ----------------
def page_genes():
    st.subheader("基因组注释浏览")
    asms = q("""SELECT a.assembly_id, s.isolate_code, t.name AS species, a.status,
                       a.assembler, a.contig_count, a.total_length, a.n50, a.gc_content,
                       a.completeness, r.platform
                FROM assemblies a
                JOIN sequencing_runs r ON r.run_id = a.run_id
                JOIN strains s ON s.strain_id = r.strain_id
                JOIN taxonomy t ON t.taxon_id = s.taxon_id
                WHERE a.status='succeeded' ORDER BY s.isolate_code""")
    pick = st.selectbox("选择基因组",
                        asms.apply(lambda r: f"{r.isolate_code}　({r.species}，{r.platform})", axis=1))
    row = asms.iloc[list(asms.index).index(
        [i for i, v in enumerate(asms.apply(lambda r: f"{r.isolate_code}　({r.species}，{r.platform})", axis=1)) if v == pick][0])]
    aid = int(row.assembly_id)

    m = st.columns(6)
    m[0].metric("总长", fmt_mb(row.total_length))
    m[1].metric("GC 含量", f"{row.gc_content}%")
    m[2].metric("Contigs", row.contig_count)
    m[3].metric("N50", f"{row.n50 // 1000} kb")
    m[4].metric("完整度", f"{row.completeness}%")
    m[5].metric("组装软件", row.assembler)

    g1, g2 = st.columns([3, 1.2])
    kw = g1.text_input("搜索基因名 / 产物 / locus_tag", key="gq")
    ftype = g2.selectbox("类型", ["全部", "CDS", "tRNA", "rRNA"])
    where, params = ["assembly_id=?"], [aid]
    if kw:
        where.append("(locus_tag LIKE ? OR gene_name LIKE ? OR product LIKE ?)")
        params += [f"%{kw}%"] * 3
    if ftype != "全部":
        where.append("feature_type=?")
        params.append(ftype)
    W = " AND ".join(where)

    st.session_state.setdefault("gpage", 1)
    total = q(f"SELECT COUNT(*) n FROM genes WHERE {W}", params).n.iloc[0]
    per = 25
    pages = max(1, -(-total // per))
    st.session_state.gpage = min(st.session_state.gpage, pages)
    c1, c2, c3 = st.columns([1, 3, 1])
    if c1.button("← 上一页", disabled=st.session_state.gpage <= 1):
        st.session_state.gpage -= 1
    c2.markdown(f"<center>第 {st.session_state.gpage} / {pages} 页　·　共 {total:,} 条</center>",
                unsafe_allow_html=True)
    if c3.button("下一页 →", disabled=st.session_state.gpage >= pages):
        st.session_state.gpage += 1

    genes = q(f"""SELECT locus_tag AS 基因座标签, gene_name AS 基因名, product AS 产物功能,
                         feature_type AS 类型, seq_start, seq_end, length_bp AS 长度bp,
                         strand AS 链, length_aa AS aa, kegg_ko AS KEGG, cog_category AS COG
                  FROM genes WHERE {W} ORDER BY seq_start LIMIT ? OFFSET ?""",
              params + [per, (st.session_state.gpage - 1) * per])
    st.dataframe(genes, use_container_width=True, hide_index=True, height=480)


# ---------------- 页面：耐药分析 ----------------
def page_amr():
    st.subheader("耐药与毒力分析")
    rates = q("""SELECT antibiotic AS 药物, COUNT(*) AS 检测数,
                        SUM(interpretation='R') AS 耐药数,
                        ROUND(SUM(interpretation='R')*100.0/COUNT(*), 1) AS 耐药率
                 FROM phenotypes GROUP BY antibiotic ORDER BY 耐药率 DESC""")
    l, r = st.columns(2)
    with l:
        st.markdown("**各药物耐药率**")
        st.plotly_chart(px.bar(rates.sort_values("耐药率"), x="耐药率", y="药物",
                               orientation="h", color_discrete_sequence=["#dc2626"],
                               text="耐药率"),
                        use_container_width=True)
    with r:
        st.markdown("**耐药机制分布**")
        mech = q("""SELECT mechanism AS 机制, COUNT(*) AS 检出 FROM amr_hits
                    WHERE mechanism IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""")
        st.plotly_chart(px.pie(mech, names="机制", values="检出", hole=0.45,
                               color_discrete_sequence=PALETTE),
                        use_container_width=True)

    st.markdown("**物种 × 药物 耐药率矩阵（%）**")
    matrix = q("""SELECT t.name AS 物种, p.antibiotic AS 药物,
                         ROUND(SUM(p.interpretation='R')*100.0/COUNT(*), 1) AS 耐药率,
                         COUNT(*) AS 检测数
                  FROM phenotypes p
                  JOIN strains s ON s.strain_id = p.strain_id
                  JOIN taxonomy t ON t.taxon_id = s.taxon_id
                  GROUP BY 1, 2""")
    if len(matrix):
        piv = matrix.pivot(index="物种", columns="药物", values="耐药率")

        def cell_color(v):
            if pd.isna(v):
                return ""
            if v >= 30:
                return "background:#fecaca"
            if v >= 10:
                return "background:#fef3c7"
            return "background:#dcfce7"

        try:
            st.dataframe(piv.style.map(cell_color), use_container_width=True)
        except AttributeError:      # 旧版 pandas 没有 Styler.map，退化为无着色表格
            st.dataframe(piv, use_container_width=True)

    l, r = st.columns(2)
    with l:
        st.markdown("**检出最多的耐药基因 Top 15**")
        top = q("""SELECT gene_symbol AS 基因, COUNT(DISTINCT assembly_id) AS 基因组数
                   FROM amr_hits GROUP BY 1 ORDER BY 2 DESC LIMIT 15""")
        st.plotly_chart(px.bar(top.sort_values("基因组数"), x="基因组数", y="基因",
                               orientation="h", color_discrete_sequence=["#dc2626"]),
                        use_container_width=True)
    with r:
        st.markdown("**耐药基因 × 物种 明细**")
        gd = q("""SELECT species_name AS 物种, gene_symbol AS 基因, drug_class AS 类别,
                         strain_cnt AS 携带基因组数, avg_identity AS '平均一致性%'
                  FROM v_amr_by_species ORDER BY 携带基因组数 DESC LIMIT 25""")
        st.dataframe(gd, use_container_width=True, hide_index=True)


# ---------------- 页面：分析任务 ----------------
def page_jobs():
    st.subheader("分析任务管理")
    st.caption("写入的是 SQLite 演示库；Streamlit Cloud 沙盒重建后改动会还原。")
    f1, f2, f3 = st.columns([2, 1.4, 1.4])
    kw = f1.text_input("按菌株编号搜索", key="jq")
    status = f2.selectbox("状态", ["全部", "queued", "running", "succeeded", "failed"])
    pipe = f3.selectbox("流程", ["全部", "QC", "assembly", "annotation", "AMR", "phylogeny", "metadata"])

    where, params = ["1=1"], []
    if kw:
        where.append("s.isolate_code LIKE ?")
        params.append(f"%{kw}%")
    if status != "全部":
        where.append("j.status=?")
        params.append(status)
    if pipe != "全部":
        where.append("j.pipeline=?")
        params.append(pipe)
    jobs = q(f"""SELECT j.job_id AS 任务号, s.isolate_code AS 菌株, t.name AS 物种,
                        j.pipeline AS 流程, j.tool_chain AS 工具链, j.status AS 状态,
                        j.operator AS 操作人, j.queued_at AS 提交时间, j.finished_at AS 完成时间
                 FROM pipeline_jobs j
                 JOIN strains s ON s.strain_id = j.strain_id
                 JOIN taxonomy t ON t.taxon_id = s.taxon_id
                 WHERE {' AND '.join(where)}
                 ORDER BY j.queued_at DESC LIMIT 100""", params)
    st.caption(f"显示 {len(jobs)} 条")
    st.dataframe(jobs, use_container_width=True, hide_index=True, height=380)

    st.divider()
    a1, a2 = st.columns(2)
    with a1:
        st.markdown("#### ➕ 提交任务")
        codes = q("SELECT strain_id, isolate_code FROM strains ORDER BY isolate_code")
        sel = st.selectbox("菌株", codes.isolate_code, key="new_code")
        pipe_new = st.selectbox("流程", ["QC", "assembly", "annotation", "AMR", "phylogeny", "metadata"],
                                key="new_pipe")
        if st.button("提交", type="primary"):
            sid = int(codes.loc[codes.isolate_code == sel, "strain_id"].iloc[0])
            jid = exec_sql(
                "INSERT INTO pipeline_jobs (strain_id, pipeline, status, operator, queued_at)"
                " VALUES (?,?,'queued','web-demo',datetime('now','localtime'))", (sid, pipe_new))
            exec_sql("INSERT INTO job_events (job_id, old_status, new_status, changed_by, changed_at)"
                     " VALUES (?, 'queued','queued','web-demo',datetime('now','localtime'))", (jid,))
            st.success(f"已创建任务 #{jid}")
            st.cache_data.clear()
    with a2:
        st.markdown("#### 🔄 状态流转")
        jid = st.number_input("任务号", min_value=1, value=int(jobs["任务号"].max()) if len(jobs) else 1)
        new_status = st.selectbox("改为", ["running", "succeeded", "failed"])
        if st.button("更新状态", type="primary"):
            jid_i = int(jid)
            old = q("SELECT status FROM pipeline_jobs WHERE job_id=?", (jid_i,)).status
            if len(old) == 0:
                st.error("任务不存在")
            else:
                exec_sql("UPDATE pipeline_jobs SET status=?,"
                         " finished_at=CASE WHEN ? IN ('succeeded','failed')"
                         " THEN datetime('now','localtime') ELSE finished_at END WHERE job_id=?",
                         (new_status, new_status, jid_i))
                exec_sql("INSERT INTO job_events (job_id, old_status, new_status, changed_by, changed_at)"
                         " VALUES (?,?,?,?,datetime('now','localtime'))",
                         (jid_i, old.iloc[0], new_status, "web-demo"))
                st.success(f"任务 #{jid_i}：{old.iloc[0]} → {new_status}（触发审计日志）")
                st.cache_data.clear()
        ev = q("""SELECT event_id AS 事件, old_status AS 原, new_status AS 新,
                         changed_by AS 操作人, changed_at AS 时间
                  FROM job_events WHERE job_id=? ORDER BY event_id DESC LIMIT 8""", (int(jid),))
        st.markdown("**该任务最近状态日志**")
        st.dataframe(ev, use_container_width=True, hide_index=True)


# ---------------- 页面：关于 ----------------
def page_about():
    st.subheader("关于本项目")
    st.markdown("""
这是一个**微生物生信数据管理**的教学演示项目：以菌株、测序、基因组组装、基因注释、
耐药基因/毒力因子、药敏表型、分析任务为核心业务，展示一个典型的生信数据库如何设计与使用。

> ⚠️ 全部数据由脚本生成的**模拟数据**（数值参考真实生物学范围，如基因组大小、GC 含量、
> 耐药基因与药敏结果的生物学一致性），不可用于真实研究。

**数据模型**

```
taxonomy(自引用分类树) ─┬─→ strains(菌株) ─┬─→ sequencing_runs(测序) ─→ assemblies(组装)
                        │                  │        ├─→ genes(基因注释，1.1万条)
                        │                  │        ├─→ amr_hits(耐药基因)
                        │                  │        └─→ vf_hits(毒力因子)
                        │                  ├─→ phenotypes(药敏 S/I/R)
                        │                  └─→ pipeline_jobs(任务) ─→ job_events(审计)
```

**本在线版的数据库要点**
- SQLite（云端无 MySQL 环境），保留 CHECK 约束、生成列（`length_bp`）、递归 CTE、窗口函数视图
- 本地完整版使用 MySQL 8.0，额外含触发器审计、存储过程、FULLTEXT 全文索引

**本地完整版**：MySQL + Flask + 原生 JS，见项目仓库 `README.md`。
""")
    st.divider()
    st.caption("Made with Streamlit · SQLite · Plotly · 模拟数据")


# ---------------- 页面：真实数据对比 ----------------
def page_reference():
    st.subheader("模拟数据 vs 真实数据")
    st.caption("真实数据：NCBI RefSeq 参考基因组元数据（每物种 30 个，"
               "经 Datasets API 拉取，见 fetch_reference.py）。"
               "用于检验模拟数据的生物学合理性——不代表任何真实监测结论。")

    refs = q("""SELECT species AS 物种, size AS 总长, gc AS 'GC含量', n50 AS N50,
                       contigs AS Contigs, level AS 组装级别, accession AS 登记号,
                       organism_name AS 菌株名, strain AS 菌株, completeness AS 完整度
                FROM reference_genomes""").copy()
    refs["数据来源"] = "RefSeq 真实"
    sim = q("""SELECT t.name AS 物种, a.total_length AS 总长, a.gc_content AS 'GC含量',
                      a.n50 AS N50, a.contig_count AS Contigs, a.completeness AS 完整度
               FROM assemblies a
               JOIN sequencing_runs r ON r.run_id = a.run_id
               JOIN strains s ON s.strain_id = r.strain_id
               JOIN taxonomy t ON t.taxon_id = s.taxon_id
               WHERE a.status='succeeded'""").copy()
    sim["数据来源"] = "模拟数据"
    sim["组装级别"] = "succeeded"

    both = pd.concat([refs[["物种", "总长", "GC含量", "N50", "Contigs", "数据来源"]],
                      sim[["物种", "总长", "GC含量", "N50", "Contigs", "数据来源"]]])
    both["Mb"] = both["总长"] / 1e6

    l, r = st.columns(2)
    with l:
        st.markdown("**基因组大小（Mb）**")
        st.plotly_chart(px.box(both, x="物种", y="Mb", color="数据来源",
                               color_discrete_map={"RefSeq 真实": "#dc2626",
                                                   "模拟数据": ACCENT}),
                        use_container_width=True)
    with r:
        st.markdown("**GC 含量（%）**")
        st.plotly_chart(px.box(both, x="物种", y="GC含量", color="数据来源",
                               color_discrete_map={"RefSeq 真实": "#dc2626",
                                                   "模拟数据": ACCENT}),
                        use_container_width=True)

    st.markdown("**N50 对比（对数轴）—— 真实 RefSeq 多为完整基因组（单 contig，N50≈全长），"
                "模拟数据模拟的是短读长/混合组装的效果**")
    st.plotly_chart(px.box(both, x="物种", y="N50", color="数据来源", log_y=True,
                           color_discrete_map={"RefSeq 真实": "#dc2626",
                                               "模拟数据": ACCENT}),
                    use_container_width=True)

    st.markdown("**分物种统计摘要**")
    summary = (both.groupby(["物种", "数据来源"])
               .agg(数量=("总长", "count"),
                    大小中位Mb=("Mb", "median"),
                    大小最小Mb=("Mb", "min"),
                    大小最大Mb=("Mb", "max"),
                    GC中位=("GC含量", "median"))
               .round(2).reset_index())
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("**真实参考基因组示例（RefSeq，前 12 条）**")
    show = refs.drop(columns=["数据来源"]).head(12)
    st.dataframe(show, use_container_width=True, hide_index=True)


# ---------------- 页面：上传比对 ----------------
def parse_fasta(text):
    """纯 Python 解析 FASTA：返回 (总长, GC%, contig数, N50)"""
    lengths, cur, gc_total = [], 0, 0
    for line in text.splitlines():
        if line.startswith(">"):
            if cur:
                lengths.append(cur)
            cur = 0
        else:
            seq = line.strip().upper()
            cur += len(seq)
            gc_total += seq.count("G") + seq.count("C")
    if cur:
        lengths.append(cur)
    total = sum(lengths)
    if not total:
        return None
    lengths.sort(reverse=True)
    half = 0
    n50 = 0
    for L in lengths:
        half += L
        if half >= total / 2:
            n50 = L
            break
    return {"size": total, "gc": round(gc_total / total * 100, 2),
            "contigs": len(lengths), "n50": n50}


def percentile_rank(values, x):
    """x 在 values 中的百分位（0~100）"""
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(sum(1 for v in vals if v < x) / len(vals) * 100)


def page_upload():
    st.subheader("上传你的数据与数据库比对")
    st.caption("上传的文件只在内存中处理，不会被保存。对比基准：库内模拟组装 + RefSeq 真实基因组。")

    with st.expander("📥 没有自己的数据？下载示例文件试一试", expanded=True):
        d1, d2 = st.columns(2)
        import os
        fna_path = os.path.join(HERE, "sample_genome.fna.gz")
        csv_path = os.path.join(HERE, "sample_assembly_stats.csv")
        with d1:
            if os.path.exists(fna_path):
                st.download_button(
                    "下载示例基因组 sample_genome.fna.gz（2.4 MB）",
                    data=open(fna_path, "rb").read(),
                    file_name="sample_genome.fna.gz",
                    mime="application/gzip")
                st.caption("模拟的 96-contig 细菌基因组，直接上传到左侧 FASTA 标签页测试")
        with d2:
            if os.path.exists(csv_path):
                st.download_button(
                    "下载示例统计表 sample_assembly_stats.csv",
                    data=open(csv_path, "rb").read(),
                    file_name="sample_assembly_stats.csv",
                    mime="text/csv")
                st.caption("8 个基因组的组装统计（含 6 个物种），上传到右侧 CSV 标签页测试")

    mode = st.tabs(["🧬 上传 FASTA（单个基因组）", "📄 上传 CSV/TSV（批量统计表）"])

    with mode[0]:
        up = st.file_uploader("选择 FASTA 文件（.fna / .fa / .fasta，支持 gzip）",
                              type=["fna", "fa", "fasta", "gz"])
        if not up:
            st.info("把你的 contig/scaffold 序列文件拖进来即可，例如 SPAdes 组装出的 contigs.fasta")
        else:
            import gzip
            raw = up.read()
            if up.name.endswith(".gz"):
                raw = gzip.decompress(raw)
            text = raw.decode("utf-8", "replace")
            with st.spinner("正在计算组装指标..."):
                stats = parse_fasta(text)
            if not stats:
                st.error("没有解析到序列：请确认是 FASTA 格式（以 > 开头的行分隔）")
                return
            m = st.columns(4)
            m[0].metric("基因组大小", f"{stats['size'] / 1e6:.2f} Mb")
            m[1].metric("GC 含量", f"{stats['gc']:.2f}%")
            m[2].metric("Contigs", stats["contigs"])
            m[3].metric("N50", f"{stats['n50'] / 1000:.0f} kb")

            refs = q("SELECT species, size, gc, n50 FROM reference_genomes")
            sim = q("""SELECT t.name AS species, a.total_length AS size, a.gc_content AS gc,
                              a.n50 AS n50
                       FROM assemblies a
                       JOIN sequencing_runs r ON r.run_id = a.run_id
                       JOIN strains s ON s.strain_id = r.strain_id
                       JOIN taxonomy t ON t.taxon_id = s.taxon_id
                       WHERE a.status='succeeded'""")
            pool = pd.concat([refs, sim], ignore_index=True)

            # 自动推荐最接近的物种（按大小和 GC 的中位偏差）
            med = pool.groupby("species").agg(ms=("size", "median"), mg=("gc", "median"),
                                              ss=("size", lambda x: x.quantile(.75) - x.quantile(.25)),
                                              sg=("gc", lambda x: x.quantile(.75) - x.quantile(.25)))
            score = ((med.ms - stats["size"]).abs() / med.ss + (med.mg - stats["gc"]).abs() / med.sg)
            best = score.idxmin()

            species = st.selectbox("对比哪个物种？（已按你的数据自动推荐）",
                                   sorted(pool.species.unique()),
                                   index=sorted(pool.species.unique()).index(best))
            sub = pool[pool.species == species]
            sub_real = refs[refs.species == species]

            st.markdown(f"**你的基因组 vs {species}（含 {len(sub_real)} 个真实 RefSeq 基因组 + "
                        f"{len(sub) - len(sub_real)} 个库内模拟组装）**")
            plot_df = sub[["size", "gc", "n50", "species"]].copy()
            plot_df["数据来源"] = "库内数据"
            yours = pd.DataFrame([{"size": stats["size"], "gc": stats["gc"],
                                   "n50": stats["n50"], "species": species,
                                   "数据来源": "你的数据"}])
            all_df = pd.concat([plot_df, yours], ignore_index=True)
            all_df["Mb"] = all_df["size"] / 1e6
            l, r = st.columns(2)
            with l:
                st.plotly_chart(px.box(all_df, x="数据来源", y="Mb", color="数据来源",
                                       color_discrete_map={"你的数据": "#f59e0b",
                                                           "库内数据": ACCENT},
                                       points="all"),
                                use_container_width=True)
            with r:
                st.plotly_chart(px.box(all_df, x="数据来源", y="gc", color="数据来源",
                                       color_discrete_map={"你的数据": "#f59e0b",
                                                           "库内数据": ACCENT},
                                       points="all"),
                                use_container_width=True)

            pr_size = percentile_rank(sub["size"], stats["size"])
            pr_gc = percentile_rank(sub["gc"], stats["gc"])
            pr_n50 = percentile_rank(sub["n50"], stats["n50"])
            c1, c2, c3 = st.columns(3)
            c1.metric("大小百分位", f"{pr_size}%",
                      f"超过 {pr_size}% 的{species}基因组")
            c2.metric("GC 百分位", f"{pr_gc}%", f"库内中位 {sub.gc.median():.2f}%")
            c3.metric("N50 百分位", f"{pr_n50}%",
                      "越大说明组装越连续" if pr_n50 else "-")
            st.caption(f"推荐依据：你的基因组与 **{best}** 的分布最接近。"
                       f"GC {'在' if 40 <= stats['gc'] <= 60 else '超出'}常见细菌范围(40~60%)。")

    with mode[1]:
        up2 = st.file_uploader("上传组装统计表（CSV/TSV，需含物种、大小、GC 列）",
                               type=["csv", "tsv", "txt"], key="csv")
        if up2:
            raw2 = up2.read().decode("utf-8", "replace")
            sep = "\t" if (up2.name.endswith(".tsv") or "\t" in raw2.splitlines()[0]) else ","
            user_df = pd.read_csv(pd.io.common.StringIO(raw2), sep=sep)
            st.caption(f"已读取 {len(user_df)} 行，列名如下，请映射到对比字段")
            c1, c2, c3, c4 = st.columns(4)
            cols = ["（跳过）"] + list(user_df.columns)
            m_species = c1.selectbox("物种列", cols, index=1 if len(cols) > 1 else 0)
            m_size = c2.selectbox("基因组大小列（bp）", cols, index=0)
            m_gc = c3.selectbox("GC 含量列（%）", cols, index=0)
            m_n50 = c4.selectbox("N50 列（bp）", cols, index=0)
            if m_size == "（跳过）":
                st.warning("至少映射基因组大小列才能对比")
                return
            pool = q("""SELECT t.name AS species, a.total_length AS size, a.gc_content AS gc,
                               a.n50 AS n50
                        FROM assemblies a
                        JOIN sequencing_runs r ON r.run_id = a.run_id
                        JOIN strains s ON s.strain_id = r.strain_id
                        JOIN taxonomy t ON t.taxon_id = s.taxon_id
                        WHERE a.status='succeeded'""")
            refs = q("SELECT species, size, gc, n50 FROM reference_genomes")
            pool = pd.concat([pool, refs], ignore_index=True)

            user_df = user_df[user_df[m_size].apply(lambda v: str(v).replace(".", "").isdigit())]
            user_df = user_df.assign(
                species=user_df[m_species] if m_species != "（跳过）" else "未知物种",
                size=user_df[m_size].astype(float),
                gc=user_df[m_gc].astype(float) if m_gc != "（跳过）" else None,
                n50=user_df[m_n50].astype(float) if m_n50 != "（跳过）" else None)
            user_df["数据来源"] = "上传数据"
            pool["数据来源"] = "库内数据"
            both = pd.concat([pool[["species", "size", "gc", "n50", "数据来源"]],
                              user_df[["species", "size", "gc", "n50", "数据来源"]]],
                             ignore_index=True)
            both["Mb"] = both["size"] / 1e6
            st.plotly_chart(px.box(both, x="species", y="Mb", color="数据来源",
                                   color_discrete_map={"上传数据": "#f59e0b",
                                                       "库内数据": ACCENT},
                                   points="all"),
                            use_container_width=True)
            out = user_df[["species", "size", "gc", "n50"]].copy()
            out["大小百分位"] = [
                percentile_rank(pool[pool.species == s]["size"], x) for s, x in zip(out.species, out.size)]
            st.markdown("**你上传的每一行 vs 库内同物种分布**")
            st.dataframe(out, use_container_width=True, hide_index=True)


# ---------------- 主入口 ----------------
PAGES = {
    "📊 总览仪表盘": page_dashboard,
    "🧪 菌株库": page_strains,
    "🧬 基因组注释": page_genes,
    "💊 耐药分析": page_amr,
    "🔬 真实数据对比": page_reference,
    "📤 上传比对": page_upload,
    "⚙️ 分析任务": page_jobs,
    "ℹ️ 关于": page_about,
}

page = st.sidebar.radio("导航", list(PAGES.keys()), label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("🧫 **MicrobeDB**\n\n微生物生信数据库演示\n\nSQLite · Streamlit · 模拟数据")
PAGES[page]()
