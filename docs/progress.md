# Project Progress Log
# AI Strategic Framing Study — Bocconi Language Technology

Team: 2 people
Start date: ___________
Submission deadline: ___________

---

## Current Status
IN PROGRESS — Week 1 data collection COMPLETE (automated scraping done)

---

## Corpus Tracker — target ~6,000 docs

### Individuals — target ~2,000

| Actor           | Commercial  | Policy  | Public | Total       | Status      |
|-----------------|-------------|---------|--------|-------------|-------------|
| Sam Altman      | 121 / 130   | 0 / 120 | 1 / 130 | 122 / 380  | commercial done (blog exhausted); policy/public: congress.gov 403, podcasts YouTube-only — structural gap |
| Dario Amodei    | 331 / 120   | 0 / 120 | 2 / 120 | 333 / 360  | commercial ✓ (331 via Anthropic sitemap + blog); policy/public: CFR/podcasts YouTube-only — structural gap |
| Jensen Huang    | 164 / 150   | 0 / 60  | 9 / 120 | 172 / 330  | commercial done ✓; policy: CSIS/Senate 403, nvidia.gov JS-rendered; public: Lex Fridman + nvidianews |
| Satya Nadella   | 108 / 120   | 80 / 80 | 47 / 100| 235 / 300  | ✓ commercial (author blog), ✓ policy (on-the-issues 80), public 47% (WorkLab) |
| Mark Zuckerberg | 125 / 120   | 0 / 60  | 3 / 150 | 128 / 330  | commercial done ✓; policy/public: all testimony + podcast YouTube-only — structural gap |
| Demis Hassabis  | 105 / 100   | 2 / 80  | 16 / 120| 123 / 300  | commercial done ✓; policy: 2 from aisi; public: Lex Fridman + Nobel PDF + DeepMind research |
| **Subtotal**    |             |         |        | **1,113 / 2,000** |       |

### Companies — target ~2,000

| Actor           | Commercial  | Policy  | Public  | Total       | Status      |
|-----------------|-------------|---------|---------|-------------|-------------|
| OpenAI          | ~545 / 170  | ~135/120| 0 / 80  | 545 / 370   | commercial/policy ✓ (Wayback + sitemap); public: openai.com 403 — structural gap |
| Anthropic       | ~520 / 150  | 1 / 120 | 35 / 80 | 528 / 350   | commercial ✓ (arXiv + sitemap); policy 404; public from anthropic.com/news |
| Google DeepMind | ~500 / 150  | 0 / 100 | 51 / 80 | 551 / 330   | commercial ✓ (arXiv + blog); policy: all sources vague; public from blog.google |
| Meta AI         | ~533 / 150  | 0 / 90  | 0 / 80  | 533 / 320   | commercial ✓ (arXiv + ai.meta.com); policy/public: about.meta.com redirects — structural gap |
| Microsoft       | ~520 / 140  | ~39/100 | 39 / 80 | 591 / 320   | commercial ✓ (arXiv + blogs); policy partial (on-the-issues); public from news.microsoft.com |
| Nvidia          | ~354 / 150  | 0 / 80  | 6 / 80  | 360 / 310   | commercial ✓ (arXiv + blogs); policy: nvidia.gov 404; public: nvidianews 6 docs |
| **Subtotal**    |             |         |         | **3,108 / 2,000** |      |

### Policymakers — target ~1,790 (no commercial context)

| Actor            | Policy      | Public   | Total       | Status      |
|------------------|-------------|----------|-------------|-------------|
| EU Commission    | ~395 / 380  | 10 / 100 | 405 / 480   | policy ✓ (europarl + commission + EUR-Lex); public: presscorner JS-blocked — structural gap |
| US Congress      | ~246 / 380  | 23 / 70  | 269 / 450   | policy partial (all senate.gov 403; only science.house.gov); public partial |
| UK DSIT          | ~450 / 350  | 19 / 80  | 469 / 430   | policy ✓ (gov.uk API + AISI); public structural cap (19 DSIT AI speeches — exhausted) |
| White House OSTP | ~561 / 350  | 0 / 80   | 561 / 430   | policy ✓ (Biden archive + Biden OSTP + EOs); public deleted (non-AI speeches scraped in error) |
| **Subtotal**     |             |          | **1,704 / 1,790** |        |

### TOTAL: **5,925 / 6,000 (98.8%)**

---

## Balance Check

Run `python src/processing/build_corpus.py --balance-report` after each major scraping phase.

Last run: 2026-04-28  |  corpus.csv written to data/processed/corpus.csv

| Rule                              | Target      | Actual                    | Pass? |
|-----------------------------------|-------------|---------------------------|-------|
| Total documents                   | >= 6,000    | 5,925 (98.8%)             | ✗ (close) |
| Largest single actor share        | <= 10%      | Microsoft 10.0%           | ✓ (at cap) |
| Smallest context share            | >= 15%      | public 3.9% (233 docs)    | ✗     |
| Individuals share                 | ~35%        | 18.8% (1,113 docs)        | ✗     |
| Companies share                   | ~35%        | 52.5% (3,108 docs)        | ✗     |
| Policymakers share                | ~30%        | 28.8% (1,704 docs)        | ✓     |

**Structural limitations (end of automated scraping — 2026-04-28):**
- public context 3.9% vs 15% target: YouTube transcripts disabled, interview sites JS-rendered or paywalled, congressional testimony 403, EU presscorner blocked
- individual type 18.8% vs 35% target: caused by 1,300+ arXiv research papers inflating company count to 52.5%
- 24 actor/context pairs below 50-doc minimum: mostly policy/public gaps (individual policy all 0 except Satya Nadella 80, Demis Hassabis 2)
- These are inherent limits of automated scraping; manual collection or transcript API access needed for individual policy/public contexts

---

## Annotation Milestones

| Milestone                               | Target    | Actual  | Date |
|-----------------------------------------|-----------|---------|------|
| Guidelines v1.0 agreed (both sign off)  | Day 8     | —       | —    |
| Gold set: Person A (300 sentences)      | 300       | —       | —    |
| Gold set: Person B (300 sentences)      | 300       | —       | —    |
| Cohen's Kappa computed                  | >= 0.70   | κ = —   | —    |
| Kappa threshold passed                  | YES       | —       | —    |
| Guidelines revised (if needed)          | —         | —       | —    |
| LLM pipeline test (50 sentences)        | >= 80%    | —       | —    |
| Full LLM labeling complete              | ~6,000    | —       | —    |
| LLM validation accuracy (held-out 100)  | >= 80%    | —       | —    |

---

## Model Results

### DV: risk_score

| Model | Key coefficient          | Value | p-value | File |
|-------|--------------------------|-------|---------|------|
| M1    | β_policy                 | —     | —       | —    |
| M2    | β_(Actor × Context) sig? | —     | —       | —    |
| M3    | β_positioning            | —     | —       | —    |

### DV: innovation_score

| Model | Key coefficient          | Value | p-value | File |
|-------|--------------------------|-------|---------|------|
| M1    | β_commercial             | —     | —       | —    |
| M2    | β_(Actor × Context) sig? | —     | —       | —    |
| M3    | β_positioning            | —     | —       | —    |

### DV: regulation_score

| Model | Key coefficient          | Value | p-value | File |
|-------|--------------------------|-------|---------|------|
| M1    | β_policy                 | —     | —       | —    |
| M2    | β_(Actor × Context) sig? | —     | —       | —    |
| M3    | β_positioning            | —     | —       | —    |

### Variance Analysis (H3)

| Actor            | Risk σ | Innovation σ | Regulation σ |
|------------------|--------|--------------|--------------|
| Sam Altman       | —      | —            | —            |
| Dario Amodei     | —      | —            | —            |
| Jensen Huang     | —      | —            | —            |
| Elon Musk        | —      | —            | —            |
| Mark Zuckerberg  | —      | —            | —            |
| Demis Hassabis   | —      | —            | —            |
| OpenAI           | —      | —            | —            |
| Anthropic        | —      | —            | —            |
| Google DeepMind  | —      | —            | —            |
| Meta AI          | —      | —            | —            |
| Microsoft        | —      | —            | —            |
| Nvidia           | —      | —            | —            |
| EU Commission    | —      | —            | —            |
| US Congress      | —      | —            | —            |
| UK DSIT          | —      | —            | —            |
| White House OSTP | —      | —            | —            |

H3 verdict (individuals > institutions in variance?): PENDING

---

## Week-by-Week Checklist

### Week 1 — Data Collection (Days 1–7)

Person A — individuals + scraping pipeline:
  - [ ] scrape_individuals.py ready and tested
  - [ ] Sam Altman — all 3 contexts (~380 docs)
  - [ ] Dario Amodei — all 3 contexts (~360 docs)
  - [ ] Jensen Huang — all 3 contexts (~330 docs)
  - [ ] Elon Musk — all 3 contexts (~300 docs)
  - [ ] Mark Zuckerberg — all 3 contexts (~330 docs)
  - [ ] Demis Hassabis — all 3 contexts (~300 docs)

Person B — companies + policymakers + data pipeline:
  - [ ] Snowflake: AI_FRAMING.PUBLIC.CORPUS table created
  - [ ] clean_and_dedupe.py tested on first batch
  - [ ] build_corpus.py schema validation working
  - [ ] OpenAI — all 3 contexts (~370 docs)
  - [ ] Anthropic — all 3 contexts (~350 docs)
  - [ ] Google DeepMind — all 3 contexts (~330 docs)
  - [ ] Meta AI — all 3 contexts (~320 docs)
  - [ ] Microsoft — all 3 contexts (~320 docs)
  - [ ] Nvidia — all 3 contexts (~310 docs)
  - [ ] EU Commission — policy + public (~480 docs)
  - [ ] US Congress — policy + public (~450 docs)
  - [ ] UK DSIT — policy + public (~430 docs)
  - [ ] White House OSTP — policy + public (~430 docs)

Both — end of week:
  - [ ] Balance report: all actors >= 80% of target
  - [ ] corpus.csv loaded to Snowflake
  - [ ] No actor exceeds 10% of corpus

### Week 2 — Annotation (Days 8–14)

  - [ ] Read annotation_guidelines.md together — both sign off verbally
  - [ ] Agree gold set stratification: 100 sent/context, 4+ actors per context
  - [ ] Person A: annotate 300 sentences → gold_set_person_a.csv
  - [ ] Person B: annotate 300 sentences → gold_set_person_b.csv (independently)
  - [ ] compute_kappa.py → κ = ___
  - [ ] κ >= 0.70? If NO: identify disagreements, revise guidelines, re-annotate
  - [ ] LLM pipeline: test on 50 sentences, accuracy = ___%
  - [ ] Full LLM labeling run on all ~6,000 docs
  - [ ] validate_llm_labels.py on held-out 100 → accuracy = ___%

### Week 3 — Analysis (Days 15–21)

Person A:
  - [ ] build_features.py — framing scores for all documents
  - [ ] regression.py --dv risk_score (Models 1, 2, 3)
  - [ ] regression.py --dv innovation_score
  - [ ] regression.py --dv regulation_score
  - [ ] All tables saved to outputs/tables/

Person B:
  - [ ] variance_analysis.py — actor variance plot
  - [ ] Individual vs company pairs analysis
  - [ ] Robustness check (re-run Model 2 excluding actors < 150 docs)
  - [ ] All figures saved to outputs/figures/ at 300 dpi

Both:
  - [ ] H1 verdict: is β_context significant? YES / NO
  - [ ] H2 verdict: commercial → innovation, policy → regulation? YES / NO
  - [ ] H3 verdict: individuals show more variance than institutions? YES / NO

### Week 4 — Write-up (Days 22–28)

  - [ ] Introduction + motivation (Altman example, strategic framing argument)
  - [ ] Related work (Entman 1993, computational framing studies, AI discourse lit)
  - [ ] Data section (corpus stats table, balance check, data sources)
  - [ ] Methodology (annotation protocol, Kappa score, LLM validation, regression spec)
  - [ ] Results (Model 1–3 tables, variance figure, H1/H2/H3 verdicts)
  - [ ] Discussion (who adapts most, does positioning predict consistency?)
  - [ ] Conclusion
  - [ ] All figures finalized
  - [ ] Submitted

---

## Daily Log — copy block for each day

### Day ___ — ___________

Person A:

Person B:

Corpus total end of day: ___ / 6,090

Blockers:

---
