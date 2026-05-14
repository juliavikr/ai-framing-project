# AI Framing Research Project — CLAUDE.md
# Bocconi University · Language Technology · 2026

## Research Question
To what extent do actors adapt their framing of AI across contexts
(commercial, policy, public), controlling for time, platform, and actor type?

**Team:** 2 people | **Timeline:** 4 weeks | **Target documents: ~6,000

## Current Status — Week 4: Write-up (2026-05-11)

All data, annotation, and analysis stages are complete. Paper write-up is the remaining task.

| Milestone | State |
|-----------|-------|
| Data collection (5,946 docs, 16 actors) | COMPLETE |
| PDF ingestion (21 docs, ingest_pdf.py) | COMPLETE |
| Corpus loaded to Snowflake | COMPLETE — AI_FRAMING.PUBLIC.CORPUS |
| Sentence pool cleaned | COMPLETE — 63,546 sentences |
| Kappa Round 1 (κ = 0.36) | FAIL — guidelines revised |
| Kappa Round 2 (κ = 0.37) | FAIL — corpus noise identified |
| Corpus cleaning | COMPLETE — clean_corpus.py (208,320 → 63,546 sentences) |
| Kappa Round 3 (κ = 0.86) | PASS ✓ — 2026-05-09 |
| LLM labeling (Haiku, 63,546 sents) | COMPLETE — 2026-05-10 |
| LLM validation (macro F1 = 0.633) | COMPLETE — outputs/tables/llm_validation.csv |
| Cross-model robustness (3 alt LLMs) | COMPLETE — Haiku best at F1=0.633 |
| LLM consistency checks | COMPLETE — 39.5pp None spread; H1 robust |
| build_features.py (2,535 docs) | COMPLETE — analysis_dataset.csv |
| Regression (Models 1–3, 3 DVs) | COMPLETE — 2026-05-10; outputs/tables/ |
| Variance analysis | COMPLETE — H3 directionally supported; outputs/figures/ |
| Innovation sub-classification | COMPLETE — 12,426 sents, 16 actors (2026-05-11) |
| Paper write-up | IN PROGRESS |

**Paper write-up checklist (Week 4):**
- [ ] Introduction + motivation (strategic framing argument, why AI discourse)
- [ ] Related work (Entman 1993, computational framing studies, AI discourse lit)
- [ ] Data section (corpus stats, per-actor counts, balance check, structural limitations)
- [ ] Methodology (annotation protocol, κ=0.86, LLM validation F1=0.633, regression spec)
- [ ] Results (Model 1–3 tables, variance figure, H1/H2/H3 verdicts)
- [ ] Discussion (who adapts most, does positioning predict framing consistency?)
- [ ] Conclusion
- [ ] All figures finalized
- [ ] Submitted

**Key constraints for paper write-up (from consistency checks):**
- Do NOT compare raw framing scores across actors — 39.5pp None rate spread confounds
- Within-actor context contrasts (M2 interactions) ARE valid
- Cite only positioning/platform terms from M3 (actor_type and context[T.policy] are multicollinear)
- Drop Economic Benefit from H2 — LLM recall=0.00 in policy context
- H2 innovation finding is conservative (true commercial→innovation effect likely larger)

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
├── README.md
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
│       ├── clean_sentences.csv      ← 63,546 filtered sentences (clean_corpus.py)
│       ├── gold_set_person_a.csv
│       ├── gold_set_person_b.csv
│       ├── gold_set_merged.csv
│       ├── kappa_overlap_person_a_v3.xlsx  ← Round 3 overlap (clean pool)
│       ├── kappa_overlap_person_b_v3.xlsx
│       ├── labeled_sentences.csv           ← 63,546 LLM-labeled sentences
│       └── labeled_documents.csv          ← doc-level framing scores (regression input)
│
├── src/
│   ├── config.py
│   ├── scraping/
│   │   ├── scrape_individuals.py
│   │   ├── scrape_companies.py
│   │   ├── scrape_policy.py
│   │   ├── scrape_transcripts.py
│   │   ├── ingest_pdf.py
│   │   └── scrape_newsapi.py
│   ├── processing/
│   │   ├── clean_and_dedupe.py
│   │   ├── build_corpus.py
│   │   └── clean_corpus.py          ← sentence-level quality filters + v3 redraw
│   ├── annotation/
│   │   ├── prepare_gold_set.py
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
├── outputs/
│   ├── figures/
│   └── tables/
│
└── docs/
    ├── PROJECT_NOTES.md             ← full pipeline documentation: decisions, methods, results
    ├── annotation_guidelines.md
    └── sources.md                   ← per-actor source documentation
```

---

## Dataset Schema
Every row in corpus.csv — no extra columns, no missing columns.

| Column       | Type   | Values / notes                                                      |
|--------------|--------|---------------------------------------------------------------------|
| doc_id       | string | UUID4, auto-generated at ingest                                     |
| actor        | string | Exact name from ACTORS dict in config.py                            |
| actor_type   | string | individual / company / policymaker                                  |
| positioning  | string | capability / safety / infrastructure / regulator                    |
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

**Excluded:** Elon Musk — only 21 docs collected from accessible sources
(Tesla EDGAR earnings, Rev.com transcripts); xAI blocked by Cloudflare;
no accessible policy corpus. Raw files archived at data/raw/_excluded/elon_musk/.
**Replaced by:** Satya Nadella — full commercial/policy/public coverage,
clean individual↔company pair with Microsoft.

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

## Actual Corpus State (as of Week 3)

**Documents:** 5,946 (99.1% of target) — loaded to Snowflake and corpus.csv

| Actor type  | Docs  | Share | Target | Status |
|-------------|-------|-------|--------|--------|
| Individuals | 1,122 | 18.9% | 35%    | ✗ below target — arXiv inflates company share |
| Companies   | 3,111 | 52.5% | 35%    | ✗ above — ~1,300 arXiv papers counted as commercial |
| Policymakers| 1,692 | 28.5% | 30%    | ✓ |

| Context    | Docs  | Share | Target | Status |
|------------|-------|-------|--------|--------|
| Commercial | 3,661 | 61.8% | —      | — |
| Policy     | 2,027 | 34.2% | —      | — |
| Public     | 237   |  4.0% | ≥15%   | ✗ structural ceiling (YouTube/paywall) |

**Known limitations** (document in paper methodology section):
- arXiv papers inflate company commercial share — classified correctly per spec
- Public context at 4.0% — YouTube captions disabled for all 14 target videos;
  podcast sites JS-rendered; interview transcripts paywalled
- Elon Musk excluded: 21 docs only (Tesla EDGAR + Rev.com transcripts);
  replaced by Satya Nadella — full 3-context coverage, clean pair with Microsoft

**Clean sentence pool** (data/annotation/clean_sentences.csv):
- 208,320 raw sentences → 63,546 after filtering (30.5% retained)
- Filters applied by clean_corpus.py:
  1. Non-English (langdetect, confidence > 0.9): 712 removed
  2. Too short (< 8 words): 20,723 removed
  3. JSON/HTML fragments: 9,184 removed
  4. No AI keyword relevance: 114,049 removed
  5. Off-topic patterns (FEMA, trade stats, header fragments): 106 removed

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

Run Models 1–3 for each DV: risk_score, innovation_score, regulation_score

---

## Annotation Frames (5 labels)
5 frames (multi-label per sentence) + None. Full definitions, examples, and edge-case
rules: **docs/annotation_guidelines.md**. Kappa target: ≥ 0.70 before LLM labeling.

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
1. Start every session: read CLAUDE.md and docs/PROJECT_NOTES.md for current state
2. Raw data is sacred: never modify data/raw/ — cleaning only in src/processing/
3. Kappa gate: compute, log, and confirm >= 0.70 before LLM labeling
4. Regression outputs: always save to outputs/tables/ — never print only

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
