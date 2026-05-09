# AI Strategic Framing Study
### Bocconi University — Language Technology 2026

## What this project is about

When Sam Altman testifies before the US Senate, he emphasizes risk and the need for
regulation. When he speaks at a startup conference, he emphasizes innovation and
economic opportunity. When he gives a podcast interview, he talks about AI's potential
to solve humanity's greatest problems.

Is this strategic? Or does everyone do it?

This project tests whether AI discourse is **strategically adaptive** — whether the
same actors frame artificial intelligence differently depending on who they are talking
to. We study 16 major actors in the AI landscape: CEOs, technology companies, and
government institutions — and analyze how they frame AI across three contexts:

- **Commercial** — company blogs, product launches, investor communications
  (talking to investors and customers)
- **Policy** — congressional testimony, regulatory submissions, government strategy
  documents (talking to regulators)
- **Public** — podcast interviews, keynote speeches, media appearances
  (talking to general audiences)

If actors shift their framing significantly across these contexts, that tells us
something important: public AI discourse is not a neutral description of technology.
It is a strategic communication tool shaped by audience and institutional incentives.

---

## Research question

> To what extent do actors adapt their framing of AI across commercial, policy, and
> public contexts, controlling for time, platform, and actor type?

## Hypotheses

**H1:** Context significantly predicts framing — actors emphasize different frames
in different settings.

**H2:** Commercial contexts increase innovation and economic framing; policy contexts
increase risk and regulation framing.

**H3:** Individual actors show greater cross-context framing variance than institutions
— people adapt more flexibly than organizations.

---

## The actors we study

### Individuals
| Actor | Organization | Positioning |
|-------|-------------|-------------|
| Sam Altman | OpenAI | Capability-first |
| Dario Amodei | Anthropic | Safety-first |
| Jensen Huang | Nvidia | Infrastructure |
| Satya Nadella | Microsoft | Capability-first |
| Mark Zuckerberg | Meta | Capability-first |
| Demis Hassabis | Google DeepMind | Safety-first |

*Elon Musk was initially included but excluded — only 21 documents available from
accessible sources, insufficient for cross-context analysis.*

### Companies
| Actor | Positioning |
|-------|-------------|
| OpenAI | Capability-first |
| Anthropic | Safety-first |
| Google DeepMind | Capability-first |
| Meta AI | Capability-first |
| Microsoft | Capability-first |
| Nvidia | Infrastructure |

### Policymakers
| Actor | Region |
|-------|--------|
| EU Commission | Europe |
| US Congress | United States |
| UK DSIT / AISI | United Kingdom |
| White House OSTP | United States |

---

## How we built it

### 1. Data collection — 5,925 documents

We built a scraping pipeline in Python using `requests` and `BeautifulSoup`,
collecting documents from 30+ distinct sources including company blogs, the Wayback
Machine CDX API (for sites blocked by Cloudflare or deleted by administrations),
arXiv, government document archives, podcast transcript sites, and 21 manually
downloaded PDFs of congressional testimony and regulatory submissions.

All documents are stored in Snowflake (`AI_FRAMING.PUBLIC.CORPUS`) and locally as
`data/processed/corpus.csv`.

**Known limitations:**
- Public context at only 4.0% (target: ≥15%) — YouTube captions disabled for all
  14 target videos; major podcast sites are JS-rendered or require transcript APIs
- ~1,300 arXiv research papers inflate company share to 52.5% — classified correctly
  as commercial (company-authored research), noted as methodology limitation

### 2. Annotation — 5 framing categories

We defined 5 framing dimensions derived from the computational framing literature
(Entman 1993; Card et al. 2015):

| Frame | Definition |
|-------|-----------|
| Innovation/Progress | AI as transformative — advancing science or society |
| Economic Benefit | Jobs, growth, productivity, national competitiveness |
| Risk/Harm | Near-term harms: bias, misuse, job loss, surveillance |
| Regulation/Governance | Policy frameworks, laws, oversight mechanisms |
| Existential/AGI | Long-term civilizational risk, AGI, superintelligence |

**Sentence-level unit of analysis.** Before annotation, we filtered 208,320 raw
sentences down to 63,546 clean sentences using five quality filters (non-English
detection, length threshold, JSON/HTML fragment removal, AI relevance keyword
matching, off-topic pattern matching).

Two human annotators independently labeled a stratified gold set of 100 shared
sentences. After two rounds of calibration (κ = 0.36, κ = 0.37), corpus cleaning
removed garbage sentences that had been suppressing agreement artificially. A third
round targets κ ≥ 0.70. Once the threshold is passed, the full corpus is labeled
using the Claude API and validated against the human gold set.

### 3. Regression analysis

We estimate three OLS models using `statsmodels`:

- **Model 1:** Does context predict framing? (`Frame ~ Context + PostChatGPT`)
- **Model 2:** Strategic adaptation — do actors shift across contexts?
  (`Frame ~ Actor + Context + Actor×Context`)
- **Model 3:** Full controls — actor type, positioning, platform, time
  (`Frame ~ ActorType + Context + Positioning + Platform + PostChatGPT`)

Each model is estimated separately for `risk_score`, `innovation_score`, and
`regulation_score` as dependent variables. We also compute per-actor framing
variance across contexts to directly test H3.

---

## Repository structure

```
ai-framing-project/
├── CLAUDE.md                   ← AI assistant context (read first each session)
├── README.md                   ← this file
├── docs/
│   ├── annotation_guidelines.md
│   ├── progress.md             ← corpus tracker and week-by-week checklist
│   ├── PROJECT_NOTES.md        ← chronological log of decisions and problems
│   └── sources.md              ← per-actor source documentation
├── data/
│   ├── raw/                    ← scraped files by actor (never modified)
│   ├── processed/
│   │   └── corpus.csv          ← master dataset (5,925 docs)
│   └── annotation/
│       ├── clean_sentences.csv ← 63,546 filtered sentences
│       ├── gold_set_*.csv      ← stratified annotator samples
│       └── labeled_full.csv    ← LLM-labeled corpus (pending)
├── src/
│   ├── scraping/               ← scrapers for each source type + PDF ingest
│   ├── processing/             ← dedup, corpus builder, sentence cleaner
│   ├── annotation/             ← gold set prep, Kappa, LLM labeling, validation
│   ├── features/               ← framing score computation
│   ├── models/                 ← OLS regression, variance analysis
│   └── utils/                  ← Snowflake connector, text utilities
├── outputs/
│   ├── figures/                ← all plots (300 dpi PNG)
│   └── tables/                 ← regression output CSVs
└── requirements.txt
```

---

## Reproducing the pipeline

```bash
pip install -r requirements.txt
cp .env.template .env            # add Snowflake + Anthropic credentials

# Data collection
python src/scraping/scrape_individuals.py --actor "Sam Altman" --context commercial
python src/scraping/scrape_companies.py --actor openai --context commercial
python src/scraping/scrape_policy.py --actor "EU Commission"
python src/scraping/ingest_pdf.py

# Build corpus
python src/processing/clean_and_dedupe.py
python src/processing/build_corpus.py
python src/utils/snowflake_utils.py --load data/processed/corpus.csv

# Annotation prep
python src/processing/clean_corpus.py          # build clean sentence pool + draw v3 overlap
python src/annotation/compute_kappa.py \
  --a data/annotation/kappa_overlap_person_a_v3.xlsx \
  --b data/annotation/kappa_overlap_person_b_v3.xlsx

# LLM labeling (after κ ≥ 0.70)
python src/annotation/label_with_llm.py --input data/processed/corpus.csv
python src/annotation/validate_llm_labels.py --gold data/annotation/gold_set_merged.csv

# Analysis
python src/features/build_features.py
python src/models/regression.py --dv risk_score
python src/models/regression.py --dv innovation_score
python src/models/regression.py --dv regulation_score
python src/models/variance_analysis.py
```

---

## Team
2 students — Bocconi University, Language Technology 2026

## Status
- [x] Week 1 — Data collection (5,925 docs, 16 actors)
- [~] Week 2 — Annotation (Kappa Round 3 in progress)
- [ ] Week 3 — Analysis
- [ ] Week 4 — Write-up
