# AI Framing Research Project — CLAUDE.md
# Bocconi University · Language Technology · 2026

## Research Question
To what extent do actors adapt their framing of AI across contexts
(commercial, policy, public), controlling for time, platform, and actor type?

**Team:** 2 people | **Timeline:** 4 weeks | **Target documents: ~6,000

---

## Hypotheses
- H1: Context significantly affects framing (β_context ≠ 0)
- H2: Commercial contexts increase innovation/economic framing; policy contexts increase risk/regulation framing
- H3: Individual actors show greater cross-context framing variance than institutions

---

## Project Structure
```
ai-framing-project/
├── CLAUDE.md                        ← read this first, every session
├── .env                             ← API keys (never commit)
├── .gitignore
├── requirements.txt
│
├── data/
│   ├── raw/                         ← scraped files, never modified
│   │   ├── individuals/
│   │   │   ├── sam_altman/
│   │   │   ├── dario_amodei/
│   │   │   ├── jensen_huang/
│   │   │   ├── satya_nadella/
│   │   │   ├── mark_zuckerberg/
│   │   │   └── demis_hassabis/
│   │   ├── _excluded/
│   │   │   └── elon_musk/          ← removed from corpus; 21 docs archived
│   │   ├── companies/
│   │   │   ├── openai/
│   │   │   ├── anthropic/
│   │   │   ├── google_deepmind/
│   │   │   ├── meta_ai/
│   │   │   ├── microsoft/
│   │   │   └── nvidia/
│   │   └── policymakers/
│   │       ├── eu_commission/
│   │       ├── us_congress/
│   │       ├── uk_dsit/
│   │       └── white_house_ostp/
│   ├── processed/
│   │   └── corpus.csv               ← master dataset, one row per document
│   └── annotation/
│       ├── gold_set_person_a.csv
│       ├── gold_set_person_b.csv
│       ├── gold_set_merged.csv
│       └── labeled_full.csv
│
├── src/
│   ├── config.py
│   ├── scraping/
│   │   ├── scrape_individuals.py
│   │   ├── scrape_companies.py
│   │   ├── scrape_policy.py
│   │   └── scrape_newsapi.py
│   ├── processing/
│   │   ├── clean_and_dedupe.py
│   │   └── build_corpus.py
│   ├── annotation/
│   │   ├── label_with_llm.py
│   │   ├── compute_kappa.py
│   │   └── validate_llm_labels.py
│   ├── features/
│   │   └── build_features.py
│   ├── models/
│   │   ├── regression.py
│   │   └── variance_analysis.py
│   └── utils/
│       ├── snowflake_utils.py
│       └── text_utils.py
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_annotation_validation.ipynb
│   └── 03_results_visualization.ipynb
│
├── outputs/
│   ├── figures/
│   └── tables/
│
└── docs/
    ├── annotation_guidelines.md
    └── progress.md
```

---

## Dataset Schema
Every row in corpus.csv — no extra columns, no missing columns.

| Column       | Type   | Values / notes                                                      |
|--------------|--------|---------------------------------------------------------------------|
| doc_id       | string | UUID4, auto-generated at ingest                                     |
| actor        | string | Exact name from ACTORS dict in config.py                            |
| actor_type   | string | individual / company / policymaker                                  |
| positioning  | string | capability / safety / infrastructure / contrarian / regulator       |
| context      | string | commercial / policy / public                                        |
| platform     | string | blog / earnings_call / testimony / regulatory_doc /                 |
|              |        | interview / speech / press_release / research_paper                 |
| date         | date   | YYYY-MM-DD                                                          |
| post_chatgpt | int    | 1 if date >= 2022-11-30, else 0                                     |
| word_count   | int    | computed at ingest                                                   |
| text         | string | full cleaned document text                                          |

---

## Context Definitions — legal contract, never deviate

| Context    | Counts as                                                              | Does NOT count as                |
|------------|------------------------------------------------------------------------|----------------------------------|
| commercial | company blogs, product launches, earnings calls, investor letters,     | internal memos, job postings     |
|            | press releases, product announcements                                  |                                  |
| policy     | congressional testimony, regulatory submissions, parliamentary         | op-eds about policy, think-tank  |
|            | hearings, gov strategy docs, formal regulatory comments                | reports (unless official comment)|
| public     | media interviews, podcast appearances, public keynotes to general      | academic conference talks,       |
|            | audiences, commencement speeches, op-eds in mass media                 | investor-only calls              |

Ambiguity rule: if you debate a document's context for more than 30 seconds, discard it.

---

## Actor Registry

### Individuals (6)
| Actor            | CSV value         | positioning    | Paired company  |
|------------------|-------------------|----------------|-----------------|
| Sam Altman       | Sam Altman        | capability     | OpenAI          |
| Dario Amodei     | Dario Amodei      | safety         | Anthropic       |
| Jensen Huang     | Jensen Huang      | infrastructure | Nvidia          |
| Satya Nadella    | Satya Nadella     | capability     | Microsoft       |
| Mark Zuckerberg  | Mark Zuckerberg   | capability     | Meta AI         |
| Demis Hassabis   | Demis Hassabis    | safety         | Google DeepMind |

### Companies (6)
| Actor           | CSV value       | positioning    | Paired individual |
|-----------------|-----------------|----------------|-------------------|
| OpenAI          | OpenAI          | capability     | Sam Altman        |
| Anthropic       | Anthropic       | safety         | Dario Amodei      |
| Google DeepMind | Google DeepMind | capability     | Demis Hassabis    |
| Meta AI         | Meta AI         | capability     | Mark Zuckerberg   |
| Microsoft       | Microsoft       | capability     | Satya Nadella     |
| Nvidia          | Nvidia          | infrastructure | Jensen Huang      |

### Policymakers (4)
| Actor            | CSV value        | positioning | Primary sources                         |
|------------------|------------------|-------------|-----------------------------------------|
| EU Commission    | EU Commission    | regulator   | europarl.europa.eu, commission.europa.eu|
| US Congress      | US Congress      | regulator   | congress.gov, senate.gov                |
| UK DSIT          | UK DSIT          | regulator   | gov.uk/dsit, aisi.gov.uk                |
| White House OSTP | White House OSTP | regulator   | whitehouse.gov/ostp                     |

---

## Target Corpus Balance

### Individuals (~2,000 docs)
| Actor           | Commercial | Policy | Public | Target |
|-----------------|------------|--------|--------|--------|
| Sam Altman      | 130        | 120    | 130    | ~380   |
| Dario Amodei    | 120        | 120    | 120    | ~360   |
| Jensen Huang    | 150        | 60     | 120    | ~330   |
| Satya Nadella   | 120        | 80     | 100    | ~300   |
| Mark Zuckerberg | 120        | 60     | 150    | ~330   |
| Demis Hassabis  | 100        | 80     | 120    | ~300   |

### Companies (~2,000 docs)
| Actor           | Commercial | Policy | Public | Target |
|-----------------|------------|--------|--------|--------|
| OpenAI          | 170        | 120    | 80     | ~370   |
| Anthropic       | 150        | 120    | 80     | ~350   |
| Google DeepMind | 150        | 100    | 80     | ~330   |
| Meta AI         | 150        | 90     | 80     | ~320   |
| Microsoft       | 140        | 100    | 80     | ~320   |
| Nvidia          | 150        | 80     | 80     | ~310   |

### Policymakers (~1,790 docs)
| Actor            | Policy | Public | Target |
|------------------|--------|--------|--------|
| EU Commission    | 380    | 100    | ~480   |
| US Congress      | 380    | 70     | ~450   |
| UK DSIT          | 350    | 80     | ~430   |
| White House OSTP | 350    | 80     | ~430   |

### Total target: ~5,790 documents

Balance rules — verify before running regression:
- No single actor > 10% of corpus
- No single context < 15% of corpus
- Every actor has >= 50 docs in at least 2 contexts (policymakers exempt from commercial)
- Type split roughly 35% individual / 35% company / 30% policymaker

---

## Data Sources

### Individuals
| Actor           | Commercial                           | Policy                          | Public                          |
|-----------------|--------------------------------------|---------------------------------|---------------------------------|
| Sam Altman      | blog.samaltman.com                   | congress.gov testimony          | Lex Fridman, Dwarkesh podcasts  |
| Dario Amodei    | darioamodei.com, anthropic.com/news  | senate.gov testimony            | CFR events, Dwarkesh, Lex       |
| Jensen Huang    | blogs.nvidia.com, GTC keynote texts  | CSIS fireside, Senate Banking   | Stanford SIEPR, press           |
| Satya Nadella   | blogs.microsoft.com, LinkedIn        | Senate testimony, House cmte    | Press interviews, Build keynotes|
| Mark Zuckerberg | ai.meta.com, earnings calls          | House Judiciary testimony       | Acquired podcast, press         |
| Demis Hassabis  | deepmind.google/blog                 | UK parliament, AI Safety Summit | Nature interviews, podcasts     |

### Companies
| Actor           | Commercial                           | Policy                            | Public               |
|-----------------|--------------------------------------|-----------------------------------|----------------------|
| OpenAI          | openai.com/blog, openai.com/research | openai.com/government             | Press releases       |
| Anthropic       | anthropic.com/news, research papers  | anthropic.com/policy              | Press releases       |
| Google DeepMind | deepmind.google/blog                 | AI principles, submissions        | Research announcements|
| Meta AI         | ai.meta.com/blog                     | about.fb.com/policy               | Press releases       |
| Microsoft       | blogs.microsoft.com/ai               | microsoft.com/responsible-ai      | Press releases       |
| Nvidia          | blogs.nvidia.com                     | nvidia.com/government             | Press releases, GTC  |

### Policymakers
| Actor            | Sources                                                                  |
|------------------|--------------------------------------------------------------------------|
| EU Commission    | europarl.europa.eu, commission.europa.eu, AI Act official texts          |
| US Congress      | congress.gov, senate.gov/ai hearings, house committee transcripts        |
| UK DSIT          | gov.uk/dsit publications, aisi.gov.uk reports, AI Safety Summit outputs  |
| White House OSTP | whitehouse.gov/ostp, AI executive orders, AI Bill of Rights blueprint    |

---

## Regression Models

Model 1 — Baseline (does context matter at all?)
  Frame_d = β0 + β1·Context_d + β2·PostChatGPT_d + ε_d

Model 2 — Strategic adaptation (CORE MODEL, β3 is the headline)
  Frame_d = β0 + β1·Actor_d + β2·Context_d + β3·(Actor × Context)_d + ε_d

Model 3 — Full controls
  Frame_d = β0 + β1·ActorType_d + β2·Context_d + β3·Positioning_d
          + β4·Platform_d + β5·PostChatGPT_d + ε_d

Model 4 — Individual vs company pairs (bonus if time allows)
  Frame_d = β0 + β1·IsIndividual_d + β2·Context_d
          + β3·(IsIndividual × Context)_d + ε_d

Run Models 1–3 for each DV: risk_score, innovation_score, regulation_score

---

## Annotation Frames (5 labels)
| ID | Label                | Short definition                                      |
|----|----------------------|-------------------------------------------------------|
| 1  | Innovation/Progress  | AI as transformative, enabling, advancing society     |
| 2  | Economic Benefit     | Jobs, growth, productivity, competitive advantage     |
| 3  | Risk/Harm            | Near-term harms: bias, job loss, misuse, surveillance |
| 4  | Regulation/Governance| Policy, laws, oversight, compliance, governance       |
| 5  | Existential/AGI      | Long-term risk, superintelligence, x-risk, AGI        |

One sentence → one or more labels, or None
Full guidelines: docs/annotation_guidelines.md
Kappa target: >= 0.70 before LLM labeling begins

---

## Code Style
- Python 3.10+
- Libraries: pandas, statsmodels, sklearn, matplotlib, seaborn, nltk
- All scripts use argparse for CLI arguments
- All paths imported from src/config.py — never hardcode elsewhere
- All functions have docstrings
- Never commit .env, data/raw/, or data/processed/ to git
- Figures: outputs/figures/ as .png 300 dpi
- Tables: outputs/tables/ as .csv

---

## Snowflake
- Free trial 1 month — credentials in .env
- Database: AI_FRAMING | Schema: PUBLIC | Table: CORPUS
- Table schema mirrors corpus.csv exactly
- Use snowflake-connector-python via src/utils/snowflake_utils.py
- Heavy queries in Snowflake; corpus.csv is local cached export only

---

## Workflow Rules
1. Start every session: read docs/progress.md before touching any code
2. After every scraper run: log actor, context, doc count, date to progress.md
3. Raw data is sacred: never modify data/raw/ — cleaning only in src/processing/
4. Kappa gate: compute, log, and confirm >= 0.70 before LLM labeling
5. Regression outputs: always save to outputs/tables/ — never print only
6. Balance check: run after each major scraping session

---

## Commands
```bash
pip install -r requirements.txt
cp .env.template .env

python src/scraping/scrape_individuals.py --actor "Sam Altman" --context commercial --limit 400
python src/scraping/scrape_companies.py --actor openai --context commercial --limit 400
python src/scraping/scrape_policy.py --actor "EU Commission" --limit 700

python src/processing/clean_and_dedupe.py
python src/processing/build_corpus.py
python src/processing/build_corpus.py --balance-report

python src/annotation/compute_kappa.py \
  --a data/annotation/gold_set_person_a.csv \
  --b data/annotation/gold_set_person_b.csv
python src/annotation/label_with_llm.py --input data/processed/corpus.csv
python src/annotation/validate_llm_labels.py --gold data/annotation/gold_set_merged.csv

python src/features/build_features.py

python src/models/regression.py --dv risk_score
python src/models/regression.py --dv innovation_score
python src/models/regression.py --dv regulation_score
python src/models/variance_analysis.py
```
