"""
config.py — Single source of truth for all paths, actor definitions, and constants.
Import this in every script. Never hardcode paths or actor names elsewhere.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT             = Path(__file__).parent.parent
DATA_RAW         = ROOT / "data" / "raw"
DATA_PROCESSED   = ROOT / "data" / "processed"
DATA_ANNOTATION  = ROOT / "data" / "annotation"
OUTPUTS_FIGURES  = ROOT / "outputs" / "figures"
OUTPUTS_TABLES   = ROOT / "outputs" / "tables"
DOCS             = ROOT / "docs"

CORPUS_CSV       = DATA_PROCESSED / "corpus.csv"
GOLD_A_CSV       = DATA_ANNOTATION / "gold_set_person_a.csv"
GOLD_B_CSV       = DATA_ANNOTATION / "gold_set_person_b.csv"
GOLD_MERGED_CSV  = DATA_ANNOTATION / "gold_set_merged.csv"
LABELED_CSV      = DATA_ANNOTATION / "labeled_full.csv"

# ── Corpus settings ────────────────────────────────────────────────────────────
CHATGPT_LAUNCH_DATE = "2022-11-30"

CONTEXTS  = ["commercial", "policy", "public"]
PLATFORMS = [
    "blog", "earnings_call", "testimony", "regulatory_doc",
    "interview", "speech", "press_release", "research_paper"
]

# ── Actor Registry ─────────────────────────────────────────────────────────────
# Each actor:
#   type:        individual / company / policymaker
#   positioning: capability / safety / infrastructure / contrarian / regulator
#   pair:        individual<->company pair for secondary analysis (None if none)
#   target:      total document target
#   contexts:    per-context doc targets
#   raw_subdir:  path under data/raw/
#   sources:     where to scrape per context

ACTORS = {

    # ── Individuals (6) — target ~2,100 docs total ─────────────────────────────
    "Sam Altman": {
        "type": "individual",
        "positioning": "capability",
        "pair": "OpenAI",
        "target": 380,
        "contexts": {"commercial": 130, "policy": 120, "public": 130},
        "raw_subdir": "individuals/sam_altman",
        "sources": {
            "commercial": ["blog.samaltman.com"],
            "policy": ["congress.gov", "senate.gov"],
            "public": ["lex fridman podcast", "dwarkesh podcast", "press interviews"],
        },
    },

    "Dario Amodei": {
        "type": "individual",
        "positioning": "safety",
        "pair": "Anthropic",
        "target": 360,
        "contexts": {"commercial": 120, "policy": 120, "public": 120},
        "raw_subdir": "individuals/dario_amodei",
        "sources": {
            "commercial": ["darioamodei.com", "anthropic.com/news", "anthropic.com/research"],
            "policy": ["senate.gov testimony", "cfr.org events", "anthropic.com/policy"],
            "public": ["dwarkesh podcast", "lex fridman podcast", "cfr speeches"],
        },
    },

    "Jensen Huang": {
        "type": "individual",
        "positioning": "infrastructure",
        "pair": "Nvidia",
        "target": 330,
        "contexts": {"commercial": 150, "policy": 60, "public": 120},
        "raw_subdir": "individuals/jensen_huang",
        "sources": {
            "commercial": ["blogs.nvidia.com", "GTC keynote transcripts",
                           "nvidia earnings calls"],
            "policy": ["CSIS fireside chats", "Senate Banking Committee",
                       "House Foreign Affairs meetings", "nvidia.com/en-us/government"],
            "public": ["Stanford SIEPR", "Stratechery interviews", "press",
                       "nvidianews.nvidia.com"],
        },
    },

    "Satya Nadella": {
        "type": "individual",
        "positioning": "capability",
        "pair": "Microsoft",
        "target": 300,
        "contexts": {"commercial": 120, "policy": 80, "public": 100},
        "raw_subdir": "individuals/satya_nadella",
        "sources": {
            "commercial": [
                "linkedin.com/in/satyanadella/",
                "blogs.microsoft.com",
                "microsoft.com/en-us/satyanadella",
            ],
            "policy": [
                "senate.gov testimony",
                "house committee transcripts",
                "microsoft.com/responsible-ai policy submissions",
                "on-the-issues",
            ],
            "public": [
                "press interviews",
                "podcast appearances",
                "keynote transcripts (Microsoft Build, Davos)",
                "microsoft.com/en-us/worklab/podcast",
            ],
        },
    },

    "Mark Zuckerberg": {
        "type": "individual",
        "positioning": "capability",
        "pair": "Meta AI",
        "target": 330,
        "contexts": {"commercial": 120, "policy": 60, "public": 150},
        "raw_subdir": "individuals/mark_zuckerberg",
        "sources": {
            "commercial": ["ai.meta.com", "Meta earnings calls (AI sections)"],
            "policy": ["House Judiciary testimony", "Senate testimony"],
            "public": ["Acquired podcast", "Lex Fridman", "press interviews"],
        },
    },

    "Demis Hassabis": {
        "type": "individual",
        "positioning": "safety",
        "pair": "Google DeepMind",
        "target": 300,
        "contexts": {"commercial": 100, "policy": 80, "public": 120},
        "raw_subdir": "individuals/demis_hassabis",
        "sources": {
            "commercial": ["deepmind.google/blog"],
            "policy": ["UK Parliament AI hearings", "AI Safety Summit transcripts",
                       "aisi.gov.uk reports"],
            "public": ["Nature interviews", "Nobel Prize lecture", "podcasts",
                       "deepmind.google/research"],
        },
    },

    # ── Companies (6) — target ~2,100 docs total ───────────────────────────────
    "OpenAI": {
        "type": "company",
        "positioning": "capability",
        "pair": "Sam Altman",
        "target": 370,
        "contexts": {"commercial": 170, "policy": 120, "public": 80},
        "raw_subdir": "companies/openai",
        "sources": {
            "commercial": ["openai.com/blog", "openai.com/research"],
            "policy": ["openai.com/government", "regulatory submissions"],
            "public": ["openai.com/news", "press releases"],
        },
    },

    "Anthropic": {
        "type": "company",
        "positioning": "safety",
        "pair": "Dario Amodei",
        "target": 350,
        "contexts": {"commercial": 150, "policy": 120, "public": 80},
        "raw_subdir": "companies/anthropic",
        "sources": {
            "commercial": ["anthropic.com/news", "anthropic.com/research"],
            "policy": ["anthropic.com/policy", "regulatory submissions"],
            "public": ["press releases"],
        },
    },

    "Google DeepMind": {
        "type": "company",
        "positioning": "capability",
        "pair": "Demis Hassabis",
        "target": 330,
        "contexts": {"commercial": 150, "policy": 100, "public": 80},
        "raw_subdir": "companies/google_deepmind",
        "sources": {
            "commercial": ["deepmind.google/blog", "deepmind.google/research"],
            "policy": ["AI principles docs", "regulatory submissions"],
            "public": ["research announcements", "press releases"],
        },
    },

    "Meta AI": {
        "type": "company",
        "positioning": "capability",
        "pair": "Mark Zuckerberg",
        "target": 320,
        "contexts": {"commercial": 150, "policy": 90, "public": 80},
        "raw_subdir": "companies/meta_ai",
        "sources": {
            "commercial": ["ai.meta.com/blog", "about.fb.com/news",
                           "about.fb.com/tag/artificial-intelligence"],
            "policy": ["about.fb.com/policy", "regulatory submissions"],
            "public": ["press releases"],
        },
    },

    "Microsoft": {
        "type": "company",
        "positioning": "capability",
        "pair": "Satya Nadella",
        "target": 320,
        "contexts": {"commercial": 140, "policy": 100, "public": 80},
        "raw_subdir": "companies/microsoft",
        "sources": {
            "commercial": ["blogs.microsoft.com/ai", "microsoft.com/en-us/research/blog"],
            "policy": ["microsoft.com/responsible-ai", "regulatory submissions"],
            "public": ["press releases", "research announcements"],
        },
    },

    "Nvidia": {
        "type": "company",
        "positioning": "infrastructure",
        "pair": "Jensen Huang",
        "target": 310,
        "contexts": {"commercial": 150, "policy": 80, "public": 80},
        "raw_subdir": "companies/nvidia",
        "sources": {
            "commercial": ["blogs.nvidia.com", "nvidia.com/en-us/research"],
            "policy": ["nvidia.com/en-us/government", "regulatory submissions"],
            "public": ["press releases", "nvidia.com/en-us/newsroom"],
        },
    },

    # ── Policymakers (4) — target ~1,800 docs total ────────────────────────────
    "EU Commission": {
        "type": "policymaker",
        "positioning": "regulator",
        "pair": None,
        "target": 480,
        "contexts": {"commercial": 0, "policy": 380, "public": 100},
        "raw_subdir": "policymakers/eu_commission",
        "sources": {
            "policy": ["europarl.europa.eu", "commission.europa.eu",
                       "AI Act official texts", "EU AI Strategy docs"],
            "public": ["press conferences", "official speeches"],
        },
    },

    "US Congress": {
        "type": "policymaker",
        "positioning": "regulator",
        "pair": None,
        "target": 450,
        "contexts": {"commercial": 0, "policy": 380, "public": 70},
        "raw_subdir": "policymakers/us_congress",
        "sources": {
            "policy": ["congress.gov AI hearings", "senate.gov AI committee transcripts",
                       "house committee on AI transcripts"],
            "public": ["official press statements on AI"],
        },
    },

    "UK DSIT": {
        "type": "policymaker",
        "positioning": "regulator",
        "pair": None,
        "target": 430,
        "contexts": {"commercial": 0, "policy": 350, "public": 80},
        "raw_subdir": "policymakers/uk_dsit",
        "sources": {
            "policy": ["gov.uk/dsit publications", "aisi.gov.uk reports",
                       "AI Safety Summit 2023/2024 outputs"],
            "public": ["official ministerial speeches on AI"],
        },
    },

    "White House OSTP": {
        "type": "policymaker",
        "positioning": "regulator",
        "pair": None,
        "target": 430,
        "contexts": {"commercial": 0, "policy": 350, "public": 80},
        "raw_subdir": "policymakers/white_house_ostp",
        "sources": {
            "policy": ["whitehouse.gov/ostp", "AI executive orders",
                       "Blueprint for AI Bill of Rights", "National AI Initiative"],
            "public": ["official White House AI press briefings"],
        },
    },
}

# ── Derived lookups ────────────────────────────────────────────────────────────
ACTOR_NAMES   = list(ACTORS.keys())
INDIVIDUALS   = [a for a, v in ACTORS.items() if v["type"] == "individual"]
COMPANIES     = [a for a, v in ACTORS.items() if v["type"] == "company"]
POLICYMAKERS  = [a for a, v in ACTORS.items() if v["type"] == "policymaker"]

PAIRS = {
    actor: meta["pair"]
    for actor, meta in ACTORS.items()
    if meta["pair"] is not None and meta["type"] == "individual"
}

POSITIONING_GROUPS = {}
for actor, meta in ACTORS.items():
    pos = meta["positioning"]
    POSITIONING_GROUPS.setdefault(pos, []).append(actor)

TOTAL_TARGET = sum(v["target"] for v in ACTORS.values())  # ~6,090

# ── Annotation ─────────────────────────────────────────────────────────────────
FRAMES = [
    "Innovation/Progress",
    "Economic Benefit",
    "Risk/Harm",
    "Regulation/Governance",
    "Existential/AGI",
]

KAPPA_THRESHOLD                  = 0.70
GOLD_SET_SIZE                    = 600   # 300 per annotator
LLM_VALIDATION_ACCURACY_TARGET   = 0.80

# ── Corpus schema ──────────────────────────────────────────────────────────────
CORPUS_COLUMNS = [
    "doc_id", "actor", "actor_type", "positioning", "context",
    "platform", "date", "post_chatgpt", "word_count", "text"
]

BALANCE_RULES = {
    "min_total_docs":               6000,
    "max_single_actor_share":       0.10,   # no actor > 10% of corpus
    "min_context_share":            0.15,   # no context < 15% of corpus
    "min_docs_per_actor_per_context": 50,   # policymakers exempt for commercial
    "target_type_split": {
        "individual":  0.35,
        "company":     0.35,
        "policymaker": 0.30,
    },
}

# ── Snowflake ──────────────────────────────────────────────────────────────────
SNOWFLAKE_CONFIG = {
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    "database":  os.getenv("SNOWFLAKE_DATABASE", "AI_FRAMING"),
    "schema":    os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
}
SNOWFLAKE_TABLE = "CORPUS"

# ── API ────────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NEWS_API_KEY      = os.getenv("NEWS_API_KEY")

LLM_MODEL      = "claude-sonnet-4-20250514"
LLM_BATCH_SIZE = 20
LLM_MAX_TOKENS = 1000

REGRESSION_DVS = ["risk_score", "innovation_score", "regulation_score"]
FIGURE_DPI     = 300
