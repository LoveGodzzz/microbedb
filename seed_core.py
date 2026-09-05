# -*- coding: utf-8 -*-
"""seed_core.py —— 生成微生物生信模拟数据（与本地 MySQL 版 scripts/generate_seed.py 同源）

返回各表的行列表，供 build_db.py 写入 SQLite。
随机种子固定，生成的数据完全可复现。
"""
import random
from datetime import date, datetime, timedelta

TODAY = date(2026, 9, 1)
MIC_LEVELS = [0.03, 0.06, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128]

CORE_GENES = [
    ("dnaA", "Chromosomal replication initiator protein DnaA", "CDS", "K02341", "L", (1300, 1450)),
    ("gyrA", "DNA gyrase subunit A", "CDS", "K02470", "L", (2500, 2800)),
    ("gyrB", "DNA gyrase subunit B", "CDS", "K02471", "L", (2000, 2200)),
    ("rpoB", "DNA-directed RNA polymerase subunit beta", "CDS", "K03043", "K", (4000, 4200)),
    ("recA", "RecA protein", "CDS", "K03541", "L", (1000, 1100)),
    ("ftsZ", "Cell division protein FtsZ", "CDS", "K03589", "D", (1100, 1200)),
    ("tufA", "Elongation factor Tu", "CDS", "K02358", "J", (1150, 1250)),
    ("groL", "Chaperonin GroEL", "CDS", "K04077", "O", (1600, 1700)),
    ("dnaK", "Chaperone protein DnaK", "CDS", "K04043", "O", (1850, 1950)),
    ("atpA", "ATP synthase subunit alpha", "CDS", "K02111", "C", (1500, 1600)),
    ("rplB", "50S ribosomal protein L2", "CDS", "K02884", "J", (800, 830)),
    ("rpsL", "30S ribosomal protein S12", "CDS", "K02925", "J", (370, 380)),
    ("infB", "Translation initiation factor IF-2", "CDS", "K02971", "J", (2700, 2900)),
    ("icd", "Isocitrate dehydrogenase", "CDS", "K00029", "E", (1250, 1300)),
    ("mdh", "Malate dehydrogenase", "CDS", "K00024", "E", (950, 970)),
    ("gltA", "Citrate synthase", "CDS", "K01647", "E", (1280, 1300)),
    ("murA", "UDP-N-acetylglucosamine enolpyruvyl transferase", "CDS", "K01935", "M", (1250, 1300)),
    ("murF", "UDP-N-acetylmuramoyl-tripeptide--D-alanyl-D-alanine ligase", "CDS", "K01936", "M", (1350, 1420)),
    ("rrsA", "16S ribosomal RNA", "rRNA", None, None, (1500, 1560)),
    ("rrlA", "23S ribosomal RNA", "rRNA", None, None, (2850, 2950)),
    ("rrfA", "5S ribosomal RNA", "rRNA", None, None, (110, 125)),
    ("trnM", "tRNA-Met", "tRNA", None, None, (70, 90)),
    ("trnG", "tRNA-Gly", "tRNA", None, None, (70, 90)),
    ("trnK", "tRNA-Lys", "tRNA", None, None, (70, 90)),
    ("trnS", "tRNA-Ser", "tRNA", None, None, (70, 90)),
    ("trnL", "tRNA-Leu", "tRNA", None, None, (70, 90)),
]

SPECIES = {
    "ECOL": {
        "species_id": 7, "prefix": "ECOL", "cn": "大肠埃希菌",
        "size": (4600000, 5500000), "gc": (50.0, 51.5),
        "source_mix": [("clinical", 8), ("food", 5), ("animal", 4), ("environmental", 3)],
        "genes": [
            ("lacZ", "Beta-galactosidase", "CDS", "K01790", "G", (3000, 3100)),
            ("lacY", "Lactose permease", "CDS", "K01972", "G", (1250, 1300)),
            ("uidA", "Beta-glucuronidase", "CDS", "K01196", "G", (1800, 1850)),
            ("ompA", "Outer membrane protein A", "CDS", "K03568", "M", (1000, 1050)),
            ("ompC", "Outer membrane porin C", "CDS", "K03570", "M", (1050, 1100)),
            ("ompF", "Outer membrane porin F", "CDS", "K03571", "M", (1050, 1100)),
            ("fimH", "Type 1 fimbrial adhesin FimH", "CDS", None, "N", (850, 900)),
            ("fliC", "Flagellin", "CDS", "K02461", "N", (1450, 1550)),
            ("motA", "Flagellar motor protein MotA", "CDS", "K02556", "N", (850, 900)),
            ("sodA", "Superoxide dismutase Mn", "CDS", "K04565", "P", (600, 650)),
            ("katG", "Catalase-peroxidase", "CDS", "K03782", "P", (2180, 2230)),
            ("gadA", "Glutamate decarboxylase alpha", "CDS", "K01583", "E", (1350, 1400)),
            ("tnaA", "Tryptophanase", "CDS", "K01667", "E", (1400, 1450)),
            ("phoA", "Alkaline phosphatase", "CDS", "K01077", "P", (1450, 1500)),
            ("uspA", "Universal stress protein A", "CDS", "K06205", "T", (450, 500)),
            ("dps", "DNA protection during starvation protein", "CDS", None, "V", (500, 550)),
            ("sdhA", "Succinate dehydrogenase flavoprotein", "CDS", "K00239", "C", (1600, 1650)),
            ("glpK", "Glycerol kinase", "CDS", "K00850", "G", (1600, 1650)),
            ("livK", "Leucine-specific binding protein", "CDS", None, "E", (1100, 1150)),
            ("cysK", "Cysteine synthase A", "CDS", "K01738", "E", (950, 1000)),
            ("glnA", "Glutamine synthetase", "CDS", "K01915", "E", (1400, 1450)),
            ("acnB", "Aconitate hydratase B", "CDS", "K01681", "C", (2400, 2450)),
            ("kdpA", "Potassium-transporting ATPase A chain", "CDS", "K01596", "P", (1750, 1800)),
            ("tsx", "Nucleoside-specific channel-forming protein Tsx", "CDS", None, "M", (950, 1000)),
        ],
        "amr": [("blaTEM-1", .45, "Beta-lactam", "enzymatic hydrolysis"), ("blaCTX-M-15", .20, "Beta-lactam", "enzymatic hydrolysis"),
                ("blaCTX-M-55", .10, "Beta-lactam", "enzymatic hydrolysis"), ("tet(A)", .25, "Tetracycline", "efflux pump"),
                ("tet(B)", .10, "Tetracycline", "efflux pump"), ("sul1", .30, "Sulfonamide", "enzyme replacement"),
                ("sul2", .20, "Sulfonamide", "enzyme replacement"), ("qnrS1", .12, "Quinolone", "target protection"),
                ("aac(3)-II", .15, "Aminoglycoside", "modifying enzyme"), ("aph(3'')-Ib", .20, "Aminoglycoside", "modifying enzyme"),
                ("catA1", .10, "Phenicol", "enzyme inactivation"), ("dfrA17", .12, "Trimethoprim", "enzyme replacement")],
        "vf": [("eae", .18, "Adhesion", "Intimin outer membrane adhesin", "VF0183"),
               ("stx2A", .12, "Toxin", "Shiga toxin 2 subunit A", "VF0203"),
               ("ehxA", .10, "Toxin", "Enterohemolysin", "VF0186"),
               ("escJ", .18, "Secretion system", "T3SS inner membrane ring protein", "VF0178"),
               ("fimH", .80, "Adhesion", "Type 1 fimbrial adhesin", "VF0525"),
               ("chuA", .40, "Iron uptake", "Heme-utilizing outer membrane protein", "VF0122")],
        "panel": ["Ampicillin", "Ceftriaxone", "Ciprofloxacin", "Gentamicin", "Meropenem", "Cotrimoxazole", "Tetracycline"],
    },
    "SAUR": {
        "species_id": 19, "prefix": "SAUR", "cn": "金黄色葡萄球菌",
        "size": (2700000, 3000000), "gc": (32.3, 33.1),
        "source_mix": [("clinical", 12), ("food", 3), ("animal", 4), ("laboratory", 1)],
        "genes": [
            ("nuc", "Thermonuclease", "CDS", "K01284", "E", (700, 750)),
            ("spa", "Immunoglobulin G-binding protein A", "CDS", None, "V", (1500, 1900)),
            ("coa", "Coagulase", "CDS", None, "V", (1900, 2000)),
            ("hla", "Alpha-hemolysin", "CDS", None, "T", (900, 950)),
            ("clfA", "Clumping factor A", "CDS", None, "V", (2900, 3000)),
            ("fnbA", "Fibronectin-binding protein A", "CDS", None, "V", (3200, 3400)),
            ("aur", "Aureolysin", "CDS", None, "Q", (1550, 1600)),
            ("sspA", "Serine protease SplA", "CDS", None, "Q", (1500, 1550)),
            ("katA", "Catalase", "CDS", "K03781", "P", (1450, 1500)),
            ("sodM", "Superoxide dismutase", "CDS", "K04565", "P", (600, 640)),
            ("femA", "FemA protein", "CDS", None, "M", (1300, 1350)),
            ("agrD", "Quorum sensing peptide AgrD", "CDS", None, "T", (220, 240)),
            ("sarA", "Staphylococcal accessory regulator SarA", "CDS", None, "K", (370, 390)),
            ("sigB", "RNA polymerase sigma factor SigB", "CDS", None, "K", (780, 800)),
            ("grlA", "Topoisomerase IV subunit A GrlA", "CDS", None, "L", (2400, 2450)),
        ],
        "amr": [("mecA", .30, "Beta-lactam", "PBP replacement"), ("blaZ", .40, "Beta-lactam", "enzymatic hydrolysis"),
                ("tet(K)", .20, "Tetracycline", "efflux pump"), ("tet(M)", .15, "Tetracycline", "ribosomal protection"),
                ("ermA", .18, "Macrolide", "ribosomal methylation"), ("ermC", .22, "Macrolide", "ribosomal methylation"),
                ("aacA-aphD", .15, "Aminoglycoside", "modifying enzyme"), ("fosB", .10, "Fosfomycin", "enzyme inactivation"),
                ("dfrG", .12, "Trimethoprim", "enzyme replacement"), ("ant(4')-Ia", .10, "Aminoglycoside", "modifying enzyme")],
        "vf": [("hla", .75, "Toxin", "Alpha-toxin", "VF0100"),
               ("clfA", .70, "Adhesion", "Clumping factor A", "VF0103"),
               ("fnbA", .60, "Adhesion", "Fibronectin-binding protein A", "VF0106"),
               ("sea", .25, "Toxin", "Enterotoxin A", "VF0111"),
               ("seb", .15, "Toxin", "Enterotoxin B", "VF0112"),
               ("tst", .08, "Toxin", "Toxic shock syndrome toxin", "VF0116"),
               ("aur", .50, "Toxin", "Aureolysin metalloprotease", "VF0104")],
        "panel": ["Oxacillin", "Cefoxitin", "Vancomycin", "Erythromycin", "Clindamycin", "Tetracycline", "Linezolid", "Gentamicin"],
    },
    "SENT": {
        "species_id": 9, "prefix": "SENT", "cn": "肠炎沙门菌",
        "size": (4500000, 5000000), "gc": (52.0, 52.7),
        "source_mix": [("clinical", 6), ("food", 9), ("animal", 5)],
        "genes": [
            ("stn", "Enterotoxin", "CDS", None, "T", (700, 750)),
            ("fliC-i", "Flagellin phase 1", "CDS", "K02461", "N", (1450, 1550)),
            ("phoP", "Two-component system response regulator PhoP", "CDS", "K07672", "T", (670, 700)),
            ("ssrB", "T3SS-2 response regulator SsrB", "CDS", None, "T", (640, 680)),
            ("sseC", "T3SS effector SseC", "CDS", None, "T", (1000, 1100)),
            ("mig-5", "Invasion antigen Mig-5", "CDS", None, "T", (900, 950)),
            ("sitD", "Iron transporter SitD", "CDS", None, "P", (850, 900)),
            ("siiE", "Giant non-fimbrial adhesin SiiE", "CDS", None, "N", (3300, 3500)),
            ("ompD", "Outer membrane porin D", "CDS", None, "M", (1000, 1050)),
            ("katE", "Catalase HPII", "CDS", "K03782", "P", (2180, 2230)),
        ],
        "amr": [("blaTEM-1", .25, "Beta-lactam", "enzymatic hydrolysis"), ("blaCMY-2", .12, "Beta-lactam", "enzymatic hydrolysis"),
                ("tet(A)", .30, "Tetracycline", "efflux pump"), ("sul1", .25, "Sulfonamide", "enzyme replacement"),
                ("sul2", .18, "Sulfonamide", "enzyme replacement"), ("aac(6')-Iy", .20, "Aminoglycoside", "modifying enzyme"),
                ("qnrB19", .08, "Quinolone", "target protection"), ("floR", .12, "Phenicol", "efflux pump"),
                ("dfrA12", .10, "Trimethoprim", "enzyme replacement"), ("aph(3'')-Ib", .15, "Aminoglycoside", "modifying enzyme")],
        "vf": [("invA", .95, "Secretion system", "T3SS inner membrane protein InvA", "VF0497"),
               ("hilA", .90, "Invasion", "Invasion regulator HilA", "VF0500"),
               ("sopB", .85, "Toxin", "Inositol phosphatase effector SopB", "VF0521"),
               ("agfA", .70, "Adhesion", "Curli subunit AgfA", "VF0528"),
               ("sefA", .45, "Adhesion", "SefA fimbrial subunit", "VF0529"),
               ("stn", .80, "Toxin", "Enterotoxin Stn", "VF0526")],
        "panel": ["Ampicillin", "Ceftriaxone", "Ciprofloxacin", "Gentamicin", "Cotrimoxazole", "Chloramphenicol", "Tetracycline"],
    },
    "PAER": {
        "species_id": 13, "prefix": "PAER", "cn": "铜绿假单胞菌",
        "size": (6100000, 7100000), "gc": (65.5, 66.6),
        "source_mix": [("clinical", 10), ("environmental", 8), ("laboratory", 2)],
        "genes": [
            ("oprL", "Peptidoglycan-associated lipoprotein OprL", "CDS", None, "M", (600, 640)),
            ("oprF", "Major outer membrane protein OprF", "CDS", None, "M", (1000, 1050)),
            ("oprD", "Basic amino acid porin OprD", "CDS", None, "M", (1350, 1400)),
            ("toxA", "Exotoxin A", "CDS", None, "T", (1900, 1950)),
            ("lasR", "Quorum sensing regulator LasR", "CDS", None, "T", (720, 750)),
            ("lasI", "Autoinducer synthesis protein LasI", "CDS", None, "Q", (600, 630)),
            ("rhlR", "Quorum sensing regulator RhlR", "CDS", None, "T", (720, 750)),
            ("pvdA", "L-ornithine N5-oxygenase PvdA", "CDS", None, "H", (1000, 1050)),
            ("pchR", "Pyochelin regulator PchR", "CDS", None, "K", (950, 1000)),
            ("algD", "GDP-mannose 6-dehydrogenase AlgD", "CDS", None, "G", (1300, 1350)),
            ("phzS", "Phenazine biosynthesis protein PhzS", "CDS", None, "Q", (1200, 1250)),
            ("pilA", "Type 4 fimbrial pilin PilA", "CDS", None, "N", (450, 480)),
            ("katB", "Catalase B", "CDS", "K03781", "P", (1450, 1500)),
            ("sodB", "Superoxide dismutase Fe", "CDS", "K04564", "P", (600, 640)),
            ("phoB", "Two-component response regulator PhoB", "CDS", "K07680", "T", (680, 700)),
            ("gltB", "Glutamate synthase large subunit", "CDS", "K00265", "E", (4400, 4500)),
        ],
        "amr": [("blaPDC", .40, "Beta-lactam", "enzymatic hydrolysis"), ("blaOXA-50", .35, "Beta-lactam", "enzymatic hydrolysis"),
                ("mexB", .45, "Multidrug efflux", "efflux pump"), ("aac(6')-Ib-cr", .25, "Aminoglycoside", "modifying enzyme"),
                ("aph(3')-IIb", .20, "Aminoglycoside", "modifying enzyme"), ("sul1", .30, "Sulfonamide", "enzyme replacement"),
                ("cmlA1", .10, "Phenicol", "efflux pump")],
        "vf": [("toxA", .80, "Toxin", "Exotoxin A", "VF0232"),
               ("pilA", .85, "Adhesion", "Type IV pilus PilA", "VF0245"),
               ("lasB", .70, "Toxin", "Elastase LasB", "VF0236"),
               ("algD", .30, "Immune evasion", "Alginate biosynthesis", "VF0240"),
               ("phz1", .40, "Toxin", "Phenazine pigment operon", "VF0251")],
        "panel": ["Meropenem", "Pip/Tazo", "Ceftazidime", "Cefepime", "Ciprofloxacin", "Amikacin"],
    },
    "BSUB": {
        "species_id": 22, "prefix": "BSUB", "cn": "枯草芽孢杆菌",
        "size": (4000000, 4300000), "gc": (43.4, 43.7),
        "source_mix": [("environmental", 10), ("food", 2), ("laboratory", 8)],
        "genes": [
            ("amyE", "Alpha-amylase", "CDS", "K01176", "G", (1550, 1600)),
            ("aprE", "Subtilisin protease", "CDS", None, "Q", (1100, 1150)),
            ("srfA", "Surfactin synthetase subunit", "CDS", None, "Q", (9800, 10200)),
            ("sboA", "Subtilosin A precursor", "CDS", None, "V", (300, 330)),
            ("sacA", "Sucrose-6-phosphate hydrolase", "CDS", "K01190", "G", (1450, 1500)),
            ("citB", "Aconitate hydratase 2", "CDS", "K01681", "C", (2300, 2350)),
            ("gapA", "Glyceraldehyde-3-phosphate dehydrogenase", "CDS", "K00150", "G", (1000, 1030)),
            ("pta", "Phosphate acetyltransferase", "CDS", "K00630", "C", (1000, 1050)),
            ("ackA", "Acetate kinase", "CDS", "K00925", "C", (1200, 1250)),
            ("alsS", "Acetolactate synthase", "CDS", "K01652", "G", (1700, 1750)),
            ("hag", "Flagellin Hag", "CDS", "K02461", "N", (800, 850)),
            ("tasA", "Antibiotic protein TasA", "CDS", None, "V", (750, 800)),
            ("comC", "Competence protein ComC", "CDS", None, "T", (750, 800)),
            ("comEA", "Competence protein ComEA", "CDS", None, "L", (1000, 1050)),
            ("sigH", "RNA polymerase sigma factor SigH", "CDS", None, "K", (650, 680)),
            ("gerAA", "Germination protein GerAA", "CDS", None, "P", (1500, 1550)),
            ("spo0A", "Stage 0 sporulation protein A", "CDS", None, "T", (800, 850)),
        ],
        "amr": [("tet(L)", .08, "Tetracycline", "efflux pump"), ("ermD", .05, "Macrolide", "ribosomal methylation"),
                ("aadE", .04, "Aminoglycoside", "modifying enzyme")],
        "vf": [],
        "panel": ["Tetracycline", "Erythromycin", "Ampicillin", "Chloramphenicol"],
    },
    "LMON": {
        "species_id": 25, "prefix": "LMON", "cn": "单核细胞增生李斯特菌",
        "size": (2900000, 3000000), "gc": (37.8, 38.2),
        "source_mix": [("food", 12), ("clinical", 5), ("environmental", 3)],
        "genes": [
            ("iap", "Invasion-associated protein p60", "CDS", None, "V", (1450, 1500)),
            ("clpP", "ATP-dependent Clp protease", "CDS", "K01359", "O", (600, 620)),
            ("svpA", "Surface protein SvpA", "CDS", None, "V", (850, 900)),
            ("lap", "Listerial adhesion protein Lap", "CDS", None, "V", (1900, 2000)),
            ("gadA", "Glutamate decarboxylase", "CDS", "K01583", "E", (1350, 1400)),
            ("bsh", "Bile salt hydrolase", "CDS", None, "M", (950, 1000)),
            ("lmo0423", "Cold shock protein", "CDS", None, "T", (650, 680)),
            ("fri", "Ferritin-like protein Fri", "CDS", None, "P", (500, 530)),
            ("actA2", "Actin assembly-inducing protein homolog", "CDS", None, "V", (1800, 1900)),
        ],
        "amr": [("tet(M)", .15, "Tetracycline", "ribosomal protection"), ("ermB", .10, "Macrolide", "ribosomal methylation"),
                ("fosX", .12, "Fosfomycin", "enzymatic hydrolysis"), ("lmo2754", .08, "Biocide tolerance", "efflux pump")],
        "vf": [("hlyA", .95, "Toxin", "Listeriolysin O", "VF0208"),
               ("inlA", .90, "Adhesion", "Internalin A", "VF0210"),
               ("inlB", .88, "Adhesion", "Internalin B", "VF0211"),
               ("actA", .85, "Invasion", "Actin assembly protein ActA", "VF0209"),
               ("prfA", .92, "Invasion", "PrfA virulence regulator", "VF0212"),
               ("plcB", .80, "Toxin", "Phospholipase C", "VF0214")],
        "panel": ["Ampicillin", "Cotrimoxazole", "Tetracycline", "Erythromycin", "Meropenem"],
    },
}

TAXONOMY = [
    (1, "kingdom", "Bacteria", None),
    (2, "phylum", "Proteobacteria", 1), (3, "class", "Gammaproteobacteria", 2),
    (4, "order", "Enterobacterales", 3), (5, "family", "Enterobacteriaceae", 4),
    (6, "genus", "Escherichia", 5), (7, "species", "Escherichia coli", 6),
    (8, "genus", "Salmonella", 5), (9, "species", "Salmonella enterica", 8),
    (10, "order", "Pseudomonadales", 3), (11, "family", "Pseudomonadaceae", 10),
    (12, "genus", "Pseudomonas", 11), (13, "species", "Pseudomonas aeruginosa", 12),
    (14, "phylum", "Bacillota", 1), (15, "class", "Bacilli", 14),
    (16, "order", "Bacillales", 15),
    (17, "family", "Staphylococcaceae", 16), (18, "genus", "Staphylococcus", 17),
    (19, "species", "Staphylococcus aureus", 18),
    (20, "family", "Bacillaceae", 16), (21, "genus", "Bacillus", 20),
    (22, "species", "Bacillus subtilis", 21),
    (23, "family", "Listeriaceae", 16), (24, "genus", "Listeria", 23),
    (25, "species", "Listeria monocytogenes", 24),
]

LOCATIONS = ["北京市", "上海市", "广东省广州市", "浙江省杭州市", "江苏省南京市", "四川省成都市",
             "山东省青岛市", "湖北省武汉市", "陕西省西安市", "辽宁省沈阳市", "河南省郑州市",
             "福建省厦门市", "湖南省长沙市", "重庆市", "天津市"]
COLLECTORS = ["张伟", "李娜", "王强", "赵敏", "陈杰", "刘洋", "杨帆", "周婷"]
LABS = ["省疾控中心检验所", "高校微生物实验室", "第三方检测中心", "附属医院微生物科"]
OPERATORS = ["张伟", "李娜", "王强"]
SOURCE_DETAIL = {
    "clinical": ["血液", "痰液", "粪便", "伤口分泌物", "尿液", "脑脊液"],
    "environmental": ["污水处理厂", "河水", "土壤", "医院环境采样", "养殖场周边水体"],
    "food": ["生鸡肉", "生牛奶", "即食食品", "水产品", "冷鲜肉", "蔬菜沙拉"],
    "animal": ["猪粪", "牛乳", "鸡盲肠内容物", "养殖场环境", "宠物犬粪便"],
    "laboratory": ["保藏参考株", "诱变株", "模式菌株"],
}
REFERENCE_NOTES = {"ECOL": "K-12 MG1655 参考菌株", "SAUR": "NCTC 8325 参考菌株", "BSUB": "168 模式菌株"}
ILLUMINA_PLATFORMS = ["Illumina NovaSeq 6000", "Illumina NextSeq 2000", "MGI DNBSEQ-G400"]

CHAINS = {"QC": "fastp 0.23 → FastQC 0.11", "assembly": "SPAdes 3.15 → QUAST 5.2",
          "annotation": "Prokka 1.14 → Bakta 1.8", "AMR": "abricate 1.1 → ResFinder/CARD",
          "phylogeny": "Parsnp 1.6 → FastTree 2.1", "metadata": "mlst 2.23 → serotypefinder"}
PARAMS = {"QC": {"threads": 16, "min_len": 50, "qualified_quality_phred": 20},
          "assembly": {"kmer": 55, "threads": 16, "min_contig": 500},
          "annotation": {"kingdom": "Bacteria", "compliant": True},
          "AMR": {"db": "ResFinder", "identity": 90, "coverage": 60},
          "phylogeny": {"ref": "NC_000913", "min_cov": 0.4},
          "metadata": {"scheme": "auto"}}
DUR_H = {"QC": .5, "assembly": 3, "annotation": 1.5, "AMR": .3, "phylogeny": 2, "metadata": .2}


def build(seed=20260905):
    """构建全部模拟数据，返回 {表名: [行,...]}"""
    rng = random.Random(seed)
    data = {}

    data["taxonomy"] = list(TAXONOMY)

    # ---------- strains ----------
    strains = []
    strain_seq = {k: 0 for k in SPECIES}
    for key, sp in SPECIES.items():
        types = [t for t, n in sp["source_mix"] for _ in range(n)]
        rng.shuffle(types)
        for j, src in enumerate(types):
            strain_seq[key] += 1
            year = rng.choice([2023, 2024, 2025, 2026])
            code = f"{sp['prefix']}-{year}-{strain_seq[key]:03d}"
            coll = date(year, rng.randint(1, 12), rng.randint(1, 28))
            if coll > TODAY:
                coll = TODAY - timedelta(days=rng.randint(10, 200))
            note, code, src = None, code, src
            if j == 0 and key in REFERENCE_NOTES:
                note = REFERENCE_NOTES[key]
                code = f"{sp['prefix']}-{year}-REF"
                src = "laboratory"
            strains.append((len(strains) + 1, code, sp["species_id"], src,
                            rng.choice(SOURCE_DETAIL[src]), rng.choice(LOCATIONS),
                            coll.isoformat(), rng.choice(COLLECTORS),
                            f"{rng.choice('ABCDEF')}-{rng.randint(1, 12):02d}-{rng.randint(1, 8)}", note))
    data["strains"] = strains

    # ---------- sequencing_runs ----------
    runs = []
    run_species = {}
    for r_i, (si, code, taxon_id, *_rest) in enumerate(strains):
        key = [k for k, sp in SPECIES.items() if sp["species_id"] == taxon_id][0]
        sp = SPECIES[key]
        run_species[si] = key
        run_date = date.fromisoformat(strains[si - 1][6]) + timedelta(days=rng.randint(5, 45))
        if run_date > TODAY:
            run_date = TODAY - timedelta(days=rng.randint(1, 20))
        r_status = "completed" if rng.random() > 0.10 else rng.choice(["failed", "processing"])
        cov = rng.randint(40, 90)
        size0 = rng.randint(*sp["size"])
        runs.append((len(runs) + 1, si, rng.choice(ILLUMINA_PLATFORMS), "PE150",
                     int(size0 * cov / 300), int(size0 * cov),
                     round(rng.uniform(0.92, 0.974), 4),
                     f"/data/runs/{code}_PE150", run_date.isoformat(), r_status))
        if rng.random() < 0.25:
            ocov = rng.randint(25, 60)
            runs.append((len(runs) + 1, si, "Nanopore GridION", "ONT",
                         int(size0 * ocov / 9000), int(size0 * ocov), None,
                         f"/data/runs/{code}_ONT",
                         (run_date + timedelta(days=rng.randint(1, 10))).isoformat(), "completed"))
    data["sequencing_runs"] = runs

    # ---------- assemblies ----------
    assemblies = []
    pe_run = {r[1]: r[0] for r in runs if r[3] == "PE150" and r[9] == "completed"}
    has_ont = {r[1] for r in runs if r[3] == "ONT" and r[9] == "completed"}
    for si in sorted(pe_run):
        sp = SPECIES[run_species[si]]
        is_hybrid = si in has_ont
        a_status = "succeeded" if rng.random() > 0.10 else rng.choice(["running", "failed"])
        if a_status != "succeeded":
            contigs = n50 = total = 0
            gc, comp, contam = 0.0, None, None
            assembler, ver = ("Unicycler" if is_hybrid else "SPAdes"), None
        else:
            assembler = "Unicycler" if is_hybrid else rng.choice(["SPAdes", "Shovill"])
            ver = "0.5.0" if is_hybrid else rng.choice(["3.15.5", "1.1.0"])
            contigs = rng.randint(15, 70) if is_hybrid else rng.randint(90, 320)
            n50 = rng.randint(800000, 2200000) if is_hybrid else rng.randint(60000, 180000)
            total = rng.randint(*sp["size"])
            gc = round(rng.uniform(*sp["gc"]), 2)
            comp = round(rng.uniform(96.0, 100.0), 2)
            contam = round(rng.uniform(0.0, 1.8), 2)
        assemblies.append((len(assemblies) + 1, pe_run[si], assembler, ver, contigs, total,
                           n50, gc, comp, contam, a_status))
    data["assemblies"] = assemblies

    # ---------- genes ----------
    genes = []
    g_i = 0
    run_strain = {r[0]: r[1] for r in runs}   # run_id -> strain_id
    for a in assemblies:
        if a[10] != "succeeded":
            continue
        aid = a[0]
        sp = SPECIES[run_species[run_strain[a[1]]]]
        tag_prefix = f"{sp['prefix']}{a[1] % 1000}"
        pool = CORE_GENES + sp["genes"]
        chosen = pool[:] + rng.sample(pool, k=min(len(pool), rng.randint(120, 220)))
        rng.shuffle(chosen)
        pos = rng.randint(1000, 50000)
        n = 0
        for (gname, product, ftype, ko, cog, (lmin, lmax)) in chosen:
            n += 1
            ln = rng.randint(lmin, lmax)
            g_i += 1
            genes.append((g_i, aid, f"{tag_prefix}_{n:05d}", gname, product, ftype,
                          pos, pos + ln - 1,
                          "+" if rng.random() < 0.5 else "-",
                          ln // 3 - 1 if ftype == "CDS" else None,
                          ko if rng.random() < 0.7 else None,
                          cog if (cog and rng.random() < 0.6) else None))
            pos += ln + rng.randint(0, 200)
    data["genes"] = genes

    # ---------- 菌株级 AMR / VF -> 按组装展开 ----------
    amr, vf = [], []
    strain_amr, strain_vf = {}, {}
    for si in range(1, len(strains) + 1):
        sp = SPECIES[run_species[si]]
        strain_amr[si] = [h for h in sp["amr"] if rng.random() < h[1]]
        strain_vf[si] = [v for v in sp["vf"] if rng.random() < v[1]]
    a_i = 0
    for a in assemblies:
        if a[10] != "succeeded":
            continue
        si = run_strain[a[1]]
        for (sym, _, dclass, mech) in strain_amr[si]:
            a_i += 1
            amr.append((a_i, a[0], sym, rng.choice(["ResFinder", "CARD"]),
                        round(rng.uniform(96.0, 100.0), 2), round(rng.uniform(95.0, 100.0), 2),
                        dclass, mech))
        for (vname, _, cat, desc, vid) in strain_vf[si]:
            a_i += 1
            vf.append((a_i, a[0], vname, vid, cat, round(rng.uniform(95.0, 100.0), 2), desc))
    data["amr_hits"] = amr
    data["vf_hits"] = vf

    # ---------- phenotypes ----------
    def mic(lo, hi):
        return rng.choice([m for m in MIC_LEVELS if lo <= m <= hi])

    ZONE = {"S": (21, 35), "I": (16, 20), "R": (6, 15)}
    phenos = []
    p_i = 0
    for si, code, taxon_id, *_ in strains:
        sp = SPECIES[run_species[si]]
        g = {h[0] for h in strain_amr[si]}
        for ab in sp["panel"]:
            interp, lo, hi = "S", 0.03, 1.0
            if ab == "Ampicillin":
                if any(x.startswith("bla") for x in g):
                    interp, lo, hi = "R", 32, 128
                else:
                    interp, lo, hi = rng.choice([("S", .5, 2)] * 8 + [("I", 4, 8)] * 2)
            elif ab == "Ceftriaxone":
                if any(x.startswith("blaCTX-M") or x == "blaCMY-2" for x in g):
                    interp, lo, hi = "R", 16, 64
                else:
                    lo, hi = 0.03, 0.5
            elif ab in ("Oxacillin", "Cefoxitin"):
                interp, lo, hi = ("R", 4, 16) if "mecA" in g else ("S", 0.125, 0.5)
            elif ab == "Ciprofloxacin":
                if any(x.startswith("qnr") for x in g) or rng.random() < 0.08:
                    interp, lo, hi = "R", 4, 16
                else:
                    lo, hi = 0.008, 0.06
            elif ab == "Gentamicin":
                if any(x.startswith(("aac", "aph", "ant", "aad")) for x in g):
                    interp, lo, hi = "R", 8, 32
                else:
                    lo, hi = 0.25, 1
            elif ab == "Meropenem":
                if run_species[si] == "PAER" and rng.random() < 0.15:
                    interp, lo, hi = rng.choice([("I", 2, 4), ("R", 8, 16)])
                else:
                    lo, hi = 0.015, 0.12
            elif ab == "Cotrimoxazole":
                interp, lo, hi = ("R", 8, 64) if any(x.startswith("sul") for x in g) else ("S", 0.25, 1)
            elif ab == "Tetracycline":
                interp, lo, hi = ("R", 16, 64) if any(x.startswith("tet") for x in g) else ("S", 0.5, 2)
            elif ab in ("Erythromycin", "Clindamycin"):
                interp, lo, hi = ("R", 16, 64) if any(x.startswith("erm") for x in g) else ("S", 0.25, 1)
            elif ab == "Vancomycin":
                lo, hi = 0.5, 1
            elif ab == "Linezolid":
                lo, hi = 0.5, 2
            elif ab == "Chloramphenicol":
                interp, lo, hi = ("R", 32, 64) if ("floR" in g or "catA1" in g) else ("S", 2, 8)
            elif ab == "Pip/Tazo":
                interp, lo, hi = (rng.choice([("I", 32, 64), ("R", 128, 128)])
                                  if ("blaPDC" in g or "mexB" in g) else ("S", 8, 16))
            elif ab in ("Ceftazidime", "Cefepime"):
                interp, lo, hi = (rng.choice([("I", 8, 16), ("R", 32, 64)])
                                  if "blaPDC" in g else ("S", 1, 4))
            elif ab == "Amikacin":
                interp, lo, hi = ("R", 32, 64) if any(x.startswith(("aac", "aph")) for x in g) else ("S", 1, 4)
            method = " broth microdilution" if rng.random() < 0.7 else " disk diffusion"
            method = method.strip()
            zone = (round(rng.uniform(*ZONE[interp]), 1) if method == "disk diffusion" else None)
            tested = date.fromisoformat(strains[si - 1][6]) + timedelta(days=rng.randint(3, 60))
            if tested > TODAY:
                tested = TODAY - timedelta(days=rng.randint(1, 10))
            p_i += 1
            phenos.append((p_i, si, ab, method, mic(lo, hi), zone, interp,
                           tested.isoformat(), rng.choice(LABS)))
    data["phenotypes"] = phenos

    # ---------- pipeline_jobs & job_events ----------
    jobs, events = [], []
    j_i = e_i = 0
    for si in range(1, len(strains) + 1):
        for pipe in rng.sample(list(CHAINS), k=rng.randint(2, 5)):
            j_i += 1
            q_at = date.fromisoformat(strains[si - 1][6]) + timedelta(days=rng.randint(2, 90))
            q_at = datetime.combine(q_at, datetime.min.time())
            if q_at > datetime.combine(TODAY, datetime.min.time()):
                q_at = datetime.combine(TODAY, datetime.min.time()) - timedelta(days=rng.randint(1, 5))
            status = rng.choices(["succeeded", "failed", "running", "queued"],
                                 weights=[75, 7, 7, 11])[0]
            started = finished = log = None
            if status != "queued":
                started = q_at + timedelta(minutes=rng.randint(1, 30))
                if status == "succeeded":
                    finished = started + timedelta(hours=DUR_H[pipe] * rng.uniform(.6, 1.6))
                    log = rng.choice(["流程正常完成", "结果已归档", "质量指标达标", "输出文件已上传"])
                elif status == "failed":
                    log = rng.choice(["磁盘空间不足", "输入文件校验失败", "内存超限 OOM", "依赖版本冲突"])
            jobs.append((j_i, si, pipe, CHAINS[pipe], __import__("json").dumps(PARAMS[pipe]),
                         status, rng.choice(OPERATORS),
                         q_at.strftime("%Y-%m-%d %H:%M:%S"),
                         started.strftime("%Y-%m-%d %H:%M:%S") if started else None,
                         finished.strftime("%Y-%m-%d %H:%M:%S") if finished else None,
                         log))
            e_i += 1
            events.append((e_i, j_i, "queued", "queued", jobs[-1][6], jobs[-1][7]))
            if started:
                e_i += 1
                events.append((e_i, j_i, "queued", "running", jobs[-1][6], jobs[-1][8]))
                e_i += 1
                events.append((e_i, j_i, "running",
                               "succeeded" if finished else ("failed" if status == "failed" else status),
                               jobs[-1][6], finished or started))
    data["pipeline_jobs"] = jobs
    data["job_events"] = events
    return data
