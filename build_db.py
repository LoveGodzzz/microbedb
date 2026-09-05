# -*- coding: utf-8 -*-
"""build_db.py —— 用 seed_core 生成的模拟数据构建 SQLite 数据库 microbe.db

运行一次即可：python build_db.py
生成的 microbe.db 直接提交到 GitHub，Streamlit Cloud 冷启动零等待。
"""
import os
import sqlite3

from seed_core import build

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "microbe.db")

SCHEMA = """
CREATE TABLE taxonomy (
  taxon_id  INTEGER PRIMARY KEY,
  tax_rank  TEXT NOT NULL CHECK (tax_rank IN ('kingdom','phylum','class','order','family','genus','species')),
  name      TEXT NOT NULL,
  parent_id INTEGER REFERENCES taxonomy(taxon_id),
  UNIQUE (tax_rank, name)
);
CREATE TABLE strains (
  strain_id     INTEGER PRIMARY KEY,
  isolate_code  TEXT NOT NULL UNIQUE,
  taxon_id      INTEGER NOT NULL REFERENCES taxonomy(taxon_id),
  source_type   TEXT NOT NULL CHECK (source_type IN ('clinical','environmental','food','animal','laboratory')),
  source_detail TEXT, location TEXT,
  collected_date TEXT, collector TEXT, storage_box TEXT, notes TEXT
);
CREATE INDEX idx_strain_taxon_source ON strains (taxon_id, source_type);
CREATE TABLE sequencing_runs (
  run_id     INTEGER PRIMARY KEY,
  strain_id  INTEGER NOT NULL REFERENCES strains(strain_id) ON DELETE CASCADE,
  platform   TEXT NOT NULL, read_type TEXT NOT NULL,
  read_count INTEGER NOT NULL, base_count INTEGER NOT NULL,
  q30_rate   REAL, fastq_dir TEXT, run_date TEXT,
  status     TEXT NOT NULL DEFAULT 'received'
             CHECK (status IN ('received','processing','completed','failed'))
);
CREATE TABLE assemblies (
  assembly_id  INTEGER PRIMARY KEY,
  run_id       INTEGER NOT NULL REFERENCES sequencing_runs(run_id) ON DELETE CASCADE,
  assembler    TEXT NOT NULL, assembler_ver TEXT,
  contig_count INTEGER NOT NULL, total_length INTEGER NOT NULL, n50 INTEGER NOT NULL,
  gc_content   REAL NOT NULL CHECK (gc_content BETWEEN 0 AND 100),
  completeness REAL CHECK (completeness IS NULL OR completeness BETWEEN 0 AND 100),
  contamination REAL CHECK (contamination IS NULL OR contamination BETWEEN 0 AND 100),
  status       TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','succeeded','failed'))
);
CREATE TABLE genes (
  gene_id      INTEGER PRIMARY KEY,
  assembly_id  INTEGER NOT NULL REFERENCES assemblies(assembly_id) ON DELETE CASCADE,
  locus_tag    TEXT NOT NULL,
  gene_name    TEXT, product TEXT NOT NULL,
  feature_type TEXT NOT NULL DEFAULT 'CDS' CHECK (feature_type IN ('CDS','tRNA','rRNA')),
  seq_start    INTEGER NOT NULL, seq_end INTEGER NOT NULL CHECK (seq_end >= seq_start),
  length_bp    INTEGER GENERATED ALWAYS AS (seq_end - seq_start + 1) STORED,
  strand       TEXT NOT NULL DEFAULT '+' CHECK (strand IN ('+','-')),
  length_aa    INTEGER, kegg_ko TEXT, cog_category TEXT,
  UNIQUE (assembly_id, locus_tag)
);
CREATE INDEX idx_gene_product ON genes (product);
CREATE TABLE amr_hits (
  hit_id      INTEGER PRIMARY KEY,
  assembly_id INTEGER NOT NULL REFERENCES assemblies(assembly_id) ON DELETE CASCADE,
  gene_symbol TEXT NOT NULL, database_name TEXT NOT NULL DEFAULT 'ResFinder',
  identity_pct REAL NOT NULL, coverage_pct REAL NOT NULL,
  drug_class  TEXT NOT NULL, mechanism TEXT
);
CREATE TABLE vf_hits (
  hit_id      INTEGER PRIMARY KEY,
  assembly_id INTEGER NOT NULL REFERENCES assemblies(assembly_id) ON DELETE CASCADE,
  vf_name     TEXT NOT NULL, vfdb_id TEXT, category TEXT NOT NULL,
  identity_pct REAL NOT NULL, description TEXT
);
CREATE TABLE phenotypes (
  pheno_id       INTEGER PRIMARY KEY,
  strain_id      INTEGER NOT NULL REFERENCES strains(strain_id) ON DELETE CASCADE,
  antibiotic     TEXT NOT NULL, method TEXT NOT NULL,
  mic_mg_l       REAL, zone_mm REAL,
  interpretation TEXT NOT NULL CHECK (interpretation IN ('S','I','R')),
  tested_at      TEXT, lab TEXT,
  UNIQUE (strain_id, antibiotic, tested_at)
);
CREATE TABLE pipeline_jobs (
  job_id      INTEGER PRIMARY KEY,
  strain_id   INTEGER NOT NULL REFERENCES strains(strain_id) ON DELETE CASCADE,
  pipeline    TEXT NOT NULL CHECK (pipeline IN ('QC','assembly','annotation','AMR','phylogeny','metadata')),
  tool_chain  TEXT, params TEXT,
  status      TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','succeeded','failed')),
  operator    TEXT,
  queued_at   TEXT NOT NULL, started_at TEXT, finished_at TEXT, log_summary TEXT
);
CREATE TABLE job_events (
  event_id   INTEGER PRIMARY KEY,
  job_id     INTEGER NOT NULL REFERENCES pipeline_jobs(job_id) ON DELETE CASCADE,
  old_status TEXT NOT NULL, new_status TEXT NOT NULL,
  changed_by TEXT NOT NULL DEFAULT 'system', changed_at TEXT NOT NULL
);

-- 真实 RefSeq 参考基因组（来自 NCBI Datasets API，见 fetch_reference.py）
CREATE TABLE reference_genomes (
  accession  TEXT PRIMARY KEY,
  species    TEXT NOT NULL,
  organism_name TEXT, strain TEXT,
  level      TEXT, refseq_category TEXT,
  size       INTEGER, gc REAL,
  contigs    INTEGER, n50 INTEGER,
  completeness REAL, release_date TEXT
);
CREATE INDEX idx_ref_species ON reference_genomes (species);

CREATE VIEW v_strain_overview AS
SELECT
  s.strain_id, s.isolate_code, t.name AS species_name,
  s.source_type, s.source_detail, s.location, s.collected_date,
  COALESCE(r.run_cnt, 0)   AS run_cnt,
  COALESCE(r.asm_cnt, 0)   AS asm_cnt,
  COALESCE(p.pheno_cnt, 0) AS pheno_cnt,
  COALESCE(a.amr_cnt, 0)   AS amr_cnt,
  COALESCE(v.vf_cnt, 0)    AS vf_cnt
FROM strains s
JOIN taxonomy t ON t.taxon_id = s.taxon_id
LEFT JOIN (
  SELECT sr.strain_id, COUNT(DISTINCT sr.run_id) AS run_cnt,
         COUNT(DISTINCT a.assembly_id) AS asm_cnt
  FROM sequencing_runs sr
  LEFT JOIN assemblies a ON a.run_id = sr.run_id
  GROUP BY sr.strain_id
) r ON r.strain_id = s.strain_id
LEFT JOIN (
  SELECT strain_id, COUNT(*) AS pheno_cnt FROM phenotypes GROUP BY strain_id
) p ON p.strain_id = s.strain_id
LEFT JOIN (
  SELECT sr.strain_id, COUNT(h.hit_id) AS amr_cnt
  FROM amr_hits h
  JOIN assemblies a ON a.assembly_id = h.assembly_id
  JOIN sequencing_runs sr ON sr.run_id = a.run_id
  GROUP BY sr.strain_id
) a ON a.strain_id = s.strain_id
LEFT JOIN (
  SELECT sr.strain_id, COUNT(v.hit_id) AS vf_cnt
  FROM vf_hits v
  JOIN assemblies a2 ON a2.assembly_id = v.assembly_id
  JOIN sequencing_runs sr ON sr.run_id = a2.run_id
  GROUP BY sr.strain_id
) v ON v.strain_id = s.strain_id;

CREATE VIEW v_amr_by_species AS
SELECT t.name AS species_name, h.gene_symbol, h.drug_class,
       COUNT(*) AS strain_cnt, ROUND(AVG(h.identity_pct), 2) AS avg_identity
FROM amr_hits h
JOIN assemblies a ON a.assembly_id = h.assembly_id
JOIN sequencing_runs r ON r.run_id = a.run_id
JOIN strains s ON s.strain_id = r.strain_id
JOIN taxonomy t ON t.taxon_id = s.taxon_id
GROUP BY t.name, h.gene_symbol, h.drug_class;

CREATE VIEW v_best_assembly AS
SELECT assembly_id, run_id, assembler, contig_count, total_length,
       n50, gc_content, completeness, contamination
FROM (
  SELECT a.*,
         ROW_NUMBER() OVER (
           PARTITION BY r.strain_id
           ORDER BY a.completeness DESC, a.contig_count ASC, a.n50 DESC) AS rn
  FROM assemblies a
  JOIN sequencing_runs r ON r.run_id = a.run_id
  WHERE a.status = 'succeeded'
) ranked
WHERE rn = 1;
"""

INSERTS = {
    "taxonomy": "INSERT INTO taxonomy (taxon_id, tax_rank, name, parent_id) VALUES (?,?,?,?)",
    "strains": "INSERT INTO strains (strain_id, isolate_code, taxon_id, source_type, source_detail, location, collected_date, collector, storage_box, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
    "sequencing_runs": "INSERT INTO sequencing_runs (run_id, strain_id, platform, read_type, read_count, base_count, q30_rate, fastq_dir, run_date, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
    "assemblies": "INSERT INTO assemblies (assembly_id, run_id, assembler, assembler_ver, contig_count, total_length, n50, gc_content, completeness, contamination, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
    "genes": "INSERT INTO genes (gene_id, assembly_id, locus_tag, gene_name, product, feature_type, seq_start, seq_end, strand, length_aa, kegg_ko, cog_category) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
    "amr_hits": "INSERT INTO amr_hits (hit_id, assembly_id, gene_symbol, database_name, identity_pct, coverage_pct, drug_class, mechanism) VALUES (?,?,?,?,?,?,?,?)",
    "vf_hits": "INSERT INTO vf_hits (hit_id, assembly_id, vf_name, vfdb_id, category, identity_pct, description) VALUES (?,?,?,?,?,?,?)",
    "phenotypes": "INSERT INTO phenotypes (pheno_id, strain_id, antibiotic, method, mic_mg_l, zone_mm, interpretation, tested_at, lab) VALUES (?,?,?,?,?,?,?,?,?)",
    "pipeline_jobs": "INSERT INTO pipeline_jobs (job_id, strain_id, pipeline, tool_chain, params, status, operator, queued_at, started_at, finished_at, log_summary) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
    "job_events": "INSERT INTO job_events (event_id, job_id, old_status, new_status, changed_by, changed_at) VALUES (?,?,?,?,?,?)",
}


def load_reference():
    """读取 fetch_reference.py 生成的 JSON，字段转成正确的数值类型"""
    import json
    path = os.path.join(HERE, "refseq_reference.json")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    out = []
    for r in rows:
        def num(v, cast=int):
            try:
                return cast(v) if v not in (None, "", "na") else None
            except (TypeError, ValueError):
                return None
        out.append((r["accession"], r["species"], r.get("organism_name"),
                    r.get("strain"), r.get("level"), r.get("refseq_category"),
                    num(r.get("size")), num(r.get("gc"), float),
                    num(r.get("contigs")), num(r.get("n50")),
                    num(r.get("completeness"), float), r.get("release_date")))
    return out


def main():
    data = build()
    if os.path.exists(DB):
        os.remove(DB)
    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)
    for table, sql in INSERTS.items():
        conn.executemany(sql, data[table])
    ref = load_reference()
    conn.executemany(
        "INSERT OR REPLACE INTO reference_genomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ref)
    conn.commit()
    for table in INSERTS:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:16s} {n}")
    conn.close()
    print(f"已生成 {DB} ({os.path.getsize(DB) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
