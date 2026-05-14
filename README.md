# AI Strategic Framing Study
### Bocconi University — Language Technology 2026

---

## TL;DR

This project tests whether AI industry actors — CEOs, tech companies, and government
institutions — strategically adapt how they frame AI depending on their audience.
We scraped 5,946 documents from 16 actors across commercial, policy, and public contexts,
annotated 63,546 sentences using Claude Haiku (κ = 0.86 inter-annotator agreement,
macro F1 = 0.633 vs. human gold), and ran OLS regressions on document-level framing proportions.

**Results:** Context is a significant predictor of framing (H1 confirmed, p < 0.001).
Policy documents contain more risk (+5.5pp) and regulation (+13.6pp) framing than commercial
documents. The individual-vs-institution variance hypothesis (H3) is directionally supported
but not formally testable due to the thin public context (4.0% of corpus). The strongest
single instance of strategic adaptation: Satya Nadella's policy documents are 27.1pp more
innovation-framed than his commercial ones.

---

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

### 1. Data collection — 5,946 documents

We built a scraping pipeline in Python using `requests` and `BeautifulSoup`,
collecting documents from 30+ distinct sources including company blogs, the Wayback
Machine CDX API (for sites blocked by Cloudflare or deleted by administrations),
arXiv, government document archives, podcast transcript sites, and 21 manually
downloaded PDFs of congressional testimony and regulatory submissions.

All documents are loaded into Snowflake (`AI_FRAMING.PUBLIC.CORPUS`). The master
dataset `corpus.csv` is gitignored (contains scraped content); reproduce it using
the pipeline steps below.

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
sentences. After two rounds of calibration (κ = 0.36, κ = 0.37) failed due to corpus
noise, 208,320 raw sentences were filtered to 63,546 clean sentences using five quality
filters. A third annotation round on the clean pool achieved κ = 0.86 (target: ≥ 0.70).

The full 63,546-sentence corpus was labeled using Claude Haiku (`claude-haiku-4-5-20251001`)
in batches of 15. LLM validation against the 100-sentence gold set achieved macro F1 = 0.633
(precision 0.847, recall 0.534). The LLM is conservative — high precision when it assigns a
frame, but defaults to None for ~47% of true positives. Framing scores are systematically
lower than human-assigned values but directionally unbiased; documented as a methodology
limitation.

Label distribution across 63,546 sentences: Innovation/Progress 18.7% | Regulation/Governance
11.5% | Risk/Harm 8.7% | Economic Benefit 6.0% | Existential/AGI 1.1% | None 58.1%.

### 3. Regression analysis

We estimate three OLS models using `statsmodels`, run separately for `risk_score`,
`innovation_score`, and `regulation_score`:

- **Model 1:** Does context predict framing? (`Frame ~ Context + PostChatGPT`)
- **Model 2:** Strategic adaptation — do actors shift across contexts?
  (`Frame ~ Actor + Context + Actor×Context`)
- **Model 3:** Full controls — actor type, positioning, platform, time
  (`Frame ~ ActorType + Context + Positioning + Platform + PostChatGPT`)

**Key findings (N=2,535 docs after quality filter):**

**H1 CONFIRMED** — Context is significant in Model 1 for all three DVs (p < 0.001).
Policy documents have substantially more risk (+0.055) and regulation (+0.136) framing
than commercial documents; public documents have the least risk framing (−0.043).

**H2 PARTIALLY CONFIRMED** — Policy → regulation (β=+0.136***) and policy → risk
(β=+0.055***) both confirmed. Commercial → innovation confirmed by inversion
(policy β=−0.023*). Commercial → economic benefit not significant in any model —
economic framing is low across all contexts, possibly due to LLM under-detection
(recall 0.375 in validation).

**H3 DIRECTIONALLY SUPPORTED, not formally testable** — Only 1 individual (Satya
Nadella) has sufficient multi-context coverage for variance analysis. Nadella shows
higher cross-context innovation variance (σ=0.129) than all qualifying companies,
substantially above his paired institution Microsoft (σ=0.031). Sample too small for
t-test; presented as illustrative.

**Notable interaction (Model 2):** Satya Nadella × policy context β=+0.271*** on
innovation score — his policy documents are far more innovation-framed than his
commercial ones, the strongest single instance of strategic adaptation in the corpus.

Model 2 is restricted to 3 actors (Microsoft, OpenAI, Satya Nadella) with ≥50 docs
in ≥2 contexts after the public-context ceiling. The public corpus at 4.0% is the
binding constraint on cross-context analysis. Regulation framing achieves the highest
explained variance of any DV (Model 3 R²=0.221), driven by positioning and platform
in addition to context. Note: M3 actor_type and context[T.policy] coefficients are
affected by multicollinearity and are not cited as primary findings (see PROJECT_NOTES §4.7).

---

## Repository structure

```
ai-framing-project/
├── CLAUDE.md                   ← AI assistant context (read first each session)
├── README.md                   ← this file
├── docs/
│   ├── PROJECT_NOTES.md        ← full pipeline documentation: decisions, methods, results
│   ├── annotation_guidelines.md ← frame definitions, examples, edge-case rules
│   └── sources.md              ← per-actor source list with URLs, methods, and status
├── data/
│   ├── raw/                    ← scraped files by actor (never modified)
│   ├── processed/
│   │   └── corpus.csv          ← master dataset (gitignored; reproduce via pipeline)
│   └── annotation/
│       ├── clean_sentences.csv      ← 63,546 filtered sentences
│       ├── gold_set_*.csv           ← stratified annotator samples
│       ├── kappa_overlap_person_*_v3.xlsx  ← Round 3 annotation overlap files
│       ├── labeled_sentences.csv    ← 63,546 LLM-labeled sentences
│       └── labeled_documents.csv   ← doc-level framing scores (regression input)
├── src/
│   ├── scraping/               ← scrapers for each source type + PDF ingest
│   ├── processing/             ← dedup, corpus builder, sentence cleaner
│   ├── annotation/             ← gold set prep, Kappa, LLM labeling, validation
│   ├── features/               ← framing score computation
│   ├── models/                 ← OLS regression, variance analysis
│   └── utils/                  ← Snowflake connector, text utilities
├── outputs/
│   ├── figures/                ← all plots (300 dpi PNG)
│   └── tables/                 ← regression output CSVs and validation results
└── requirements.txt
```

---

## Reproducing the pipeline

> **Note:** `corpus.csv` is gitignored. Steps 1–2 require Snowflake credentials
> (add to `.env`). Steps 3 onward can run from `data/annotation/` files checked
> into the repo.

```bash
pip install -r requirements.txt
cp .env.template .env            # add Snowflake + Anthropic credentials

# 1. Data collection
python src/scraping/scrape_individuals.py --actor "Sam Altman" --context commercial
python src/scraping/scrape_companies.py --actor openai --context commercial
python src/scraping/scrape_policy.py --actor "EU Commission"
python src/scraping/ingest_pdf.py           # 21 manually downloaded PDFs

# 2. Build corpus
python src/processing/clean_and_dedupe.py
python src/processing/build_corpus.py
python src/utils/snowflake_utils.py --load data/processed/corpus.csv

# 3. Annotation prep
python src/processing/clean_corpus.py          # 208,320 → 63,546 sentences + v3 overlap draw
python src/annotation/compute_kappa.py \
  --a data/annotation/kappa_overlap_person_a_v3.xlsx \
  --b data/annotation/kappa_overlap_person_b_v3.xlsx

# 4. LLM labeling (after κ ≥ 0.70)
python src/annotation/label_with_llm.py --input data/processed/corpus.csv
python src/annotation/validate_llm_labels.py --gold data/annotation/gold_set_merged.csv

# 5. Analysis
python src/features/build_features.py
python src/models/regression.py --dv risk_score
python src/models/regression.py --dv innovation_score
python src/models/regression.py --dv regulation_score
python src/models/variance_analysis.py
```
