# -*- coding: utf-8 -*-
"""fetch_reference.py —— 从 NCBI Datasets API 拉取 6 个物种的真实 RefSeq 基因组元数据

生成 refseq_reference.json（随仓库提交，Streamlit Cloud 冷启动无需再访问 NCBI）。
字段：accession / 物种 / 菌株名 / 组装级别 / 总长 / GC% / contigs / N50 / 释放日期 / 完整度
"""
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refseq_reference.json")

SPECIES_TAXIDS = {
    "Escherichia coli": 562,
    "Staphylococcus aureus": 1280,
    "Salmonella enterica": 28901,
    "Pseudomonas aeruginosa": 208964,
    "Bacillus subtilis": 1423,
    "Listeria monocytogenes": 1639,
}
PER_SPECIES = 30   # 每个物种取多少个真实基因组
URL = ("https://api.ncbi.nlm.nih.gov/datasets/v2/genome/taxon/{tax}/dataset_report"
       "?page_size=200&filters.refseq_only=true")


def fetch(tax):
    req = urllib.request.Request(URL.format(tax=tax),
                                 headers={"User-Agent": "MicrobeDB-demo/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main():
    result = []
    for species, tax in SPECIES_TAXIDS.items():
        data = fetch(tax)
        reports = data.get("reports", [])
        rows = []
        for r in reports:
            if r.get("source_database") != "SOURCE_DATABASE_REFSEQ":
                continue
            stats = r.get("assembly_stats", {}) or {}
            info = r.get("assembly_info", {}) or {}
            org = r.get("organism", {}) or {}
            size = stats.get("total_sequence_length")
            if not size:
                continue
            rows.append({
                "accession": r.get("current_accession") or r.get("accession"),
                "species": species,
                "organism_name": org.get("organism_name"),
                "strain": (org.get("infraspecific_names") or {}).get("strain"),
                "level": info.get("assembly_level"),
                "refseq_category": info.get("refseq_category") or "na",
                "size": size,
                "gc": stats.get("gc_percent"),
                "contigs": stats.get("number_of_contigs"),
                "n50": stats.get("contig_n50"),
                "completeness": (r.get("checkm_info") or {}).get("completeness"),
                "release_date": info.get("release_date"),
            })
        # 优先完整基因组，其次按 N50 降序，取前 PER_SPECIES 个
        rows.sort(key=lambda x: (x["level"] != "Complete Genome",
                                 -(x["n50"] or 0)))
        result += rows[:PER_SPECIES]
        print(f"{species:26s} {len(reports):>4} 个报告 -> 取 {min(PER_SPECIES, len(rows))} 个")
        time.sleep(1.2)   # 尊重 API 限流

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"已写入 {OUT}，共 {len(result)} 个真实基因组")


if __name__ == "__main__":
    main()
