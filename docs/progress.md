# Project Progress Log
# AI Strategic Framing Study — Bocconi Language Technology

Team: 2 people
Start date: ___________
Submission deadline: ___________

---

## Current Status
**Week 2 IN PROGRESS — LLM labeling running (2026-05-10)**
Kappa passed at κ = 0.86. LLM labeling ~85% complete (54,624 / 63,546 sentences done).
Full labeled_sentences.csv expected complete by end of day 2026-05-10.

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

### Individuals — updated counts after PDF ingestion

| Actor           | Commercial  | Policy  | Public | Total       |
|-----------------|-------------|---------|--------|-------------|
| Sam Altman      | 121         | 1       | 3      | **125**     |
| Dario Amodei    | 331         | 2       | 3      | **336**     |
| Jensen Huang    | 164         | 0       | 10     | **173**     |
| Satya Nadella   | 108         | 80      | 47     | **235**     |
| Mark Zuckerberg | 125         | 1       | 3      | **129**     |
| Demis Hassabis  | 105         | 3       | 16     | **124**     |
| **Subtotal**    |             |         |        | **1,122**   |

### TOTAL: **5,946 / 6,000 (99.1%)**  ← after PDF ingestion (21 new docs)

---

## Balance Check

Last run: 2026-05-08  |  corpus.csv written to data/processed/corpus.csv  |  5,946 rows

| Rule                              | Target      | Actual                    | Pass? |
|-----------------------------------|-------------|---------------------------|-------|
| Total documents                   | >= 6,000    | 5,946 (99.1%)             | ✗ (close) |
| Largest single actor share        | <= 10%      | Microsoft 10.0%           | ✓ (at cap) |
| Smallest context share            | >= 15%      | public 4.0% (237 docs)    | ✗     |
| Individuals share                 | ~35%        | 18.9% (1,122 docs)        | ✗     |
| Companies share                   | ~35%        | 52.3% (3,111 docs)        | ✗     |
| Policymakers share                | ~30%        | 28.8% (1,713 docs)        | ✓     |

**Methodology notes for analysis:**
- arXiv papers inflate company share to 52.3% — acknowledged limitation, noted in methodology section
- Public context at 4.0% — structural ceiling from YouTube/paywall blocks, supplemented by 21 manual PDFs; document in data section as research limitation
- 24 actor/context pairs below 50-doc minimum; individual policy contexts have 1–3 docs each (not enough for per-actor policy regression) — pool individual policy for H3 analysis
- See `docs/sources.md` for full source documentation

---

## Annotation Milestones

| Milestone                               | Target    | Actual       | Date       |
|-----------------------------------------|-----------|--------------|------------|
| Guidelines v1.0 agreed (both sign off)  | Day 8     | ✓            | 2026-05-09 |
| Gold set: Person A (300 sentences)      | 300       | 300 ✓        | 2026-05-09 |
| Gold set: Person B (300 sentences)      | 300       | 300 ✓        | 2026-05-09 |
| Kappa Round 1                           | >= 0.70   | κ = 0.36 ✗   | 2026-05-09 |
| Kappa Round 2 (after guideline fix)     | >= 0.70   | κ = 0.37 ✗   | 2026-05-09 |
| Corpus cleaning (clean_corpus.py)       | —         | 63,546 sents | 2026-05-09 |
| Kappa Round 3 (clean pool, v3 sheets)   | >= 0.70   | κ = 0.86 ✓   | 2026-05-09 |
| Kappa threshold passed                  | YES       | YES ✓        | 2026-05-09 |
| LLM pipeline test (50 docs, Haiku)      | working   | ✓ real labels | 2026-05-10 |
| Full LLM labeling complete              | 63,546    | IN PROGRESS 85% | 2026-05-10 |
| LLM validation accuracy (held-out 100)  | >= 80%    | —            | —          |

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
| Satya Nadella    | —      | —            | —            |
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

### Week 1 — Data Collection (Days 1–7) — COMPLETE

Person A — individuals + scraping pipeline:
  - [x] scrape_individuals.py ready and tested
  - [x] Sam Altman — commercial ✓ (121); policy 1 (PDF); public 3 (Lex + PDFs)
  - [x] Dario Amodei — commercial ✓ (331); policy 2 (PDFs); public 3 (transcripts + PDF)
  - [x] Jensen Huang — commercial ✓ (164); policy 0 (blocked); public 10 (Lex/Dwarkesh/PDF)
  - [x] Elon Musk — EXCLUDED (replaced by Satya Nadella); 21 docs archived
  - [x] Satya Nadella — commercial 108; policy ✓ (80); public 47 (WorkLab)
  - [x] Mark Zuckerberg — commercial ✓ (125); policy 1 (PDF); public 3 (Lex/Dwarkesh)
  - [x] Demis Hassabis — commercial ✓ (105); policy 3 (AISI + PDF); public 16

Person B — companies + policymakers + data pipeline:
  - [x] Snowflake: AI_FRAMING.PUBLIC.CORPUS table created ✓
  - [x] clean_and_dedupe.py tested on first batch
  - [x] build_corpus.py schema validation working (5,946 rows written)
  - [x] OpenAI — 546 docs (commercial Wayback + arXiv; policy Wayback + PDF)
  - [x] Anthropic — 529 docs (commercial sitemap + arXiv; public newsroom; policy PDF)
  - [x] Google DeepMind — 551 docs (commercial arXiv + blog; public blog.google)
  - [x] Meta AI — 533 docs (commercial arXiv + newsroom; policy 0 — source mislabeled)
  - [x] Microsoft — 592 docs (commercial arXiv + blog; policy on-the-issues + PDF)
  - [x] Nvidia — 360 docs (commercial arXiv + blog; public newsroom)
  - [x] EU Commission — 408 docs (digital-strategy scraper + 3 PDFs; public speeches)
  - [x] US Congress — 270 docs (science.house.gov; public press releases; 1 PDF)
  - [x] UK DSIT — 471 docs (gov.uk API + AISI + 2 PDFs; public speeches)
  - [x] White House OSTP — 564 docs (Biden archive + 3 PDFs)

Both — end of week:
  - [x] Balance report run — Microsoft at 10.0% cap ✓; public 4.0% (structural limitation)
  - [x] corpus.csv loaded to Snowflake ✓ (5,925 rows, 8.8s)
  - [x] No actor exceeds 10% of corpus ✓ (Microsoft at exactly 10.0%)

### Week 2 — Annotation (Days 8–14) — LLM LABELING IN PROGRESS

  - [x] Read annotation_guidelines.md together — both sign off verbally
  - [x] Agree gold set stratification: 100 sent/context, 5+ actors per context
  - [x] Person A: annotate 300 sentences → gold_set_person_a.csv
  - [x] Person B: annotate 300 sentences → gold_set_person_b.csv (independently)
  - [x] Kappa Round 1 → κ = 0.36 FAIL (28 disagreements, None/frame boundary)
  - [x] Guidelines revised — added "None Boundary" rules + 10 calibration examples
  - [x] Kappa Round 2 → κ = 0.37 FAIL (28 disagreements — corpus noise, not labels)
  - [x] Corpus cleaned — clean_corpus.py (208,320 → 63,546 sentences, 5 filters)
  - [x] Kappa Round 3 (clean pool, v3 sheets) → κ = 0.86 PASS ✓  (2026-05-09)
        Innovation/Progress 0.86 | Economic Benefit 0.93 | Risk/Harm 0.80
        Regulation/Governance 0.83 | Existential/AGI 0.88 | None 0.85
        14 residual disagreements (all genuine edge cases) → saved kappa_results_v3.csv
  - [~] Full LLM labeling — IN PROGRESS (2026-05-10) — 54,624 / 63,546 sentences (85.9%)
        Model: claude-haiku-4-5-20251001 | Batch size: 15 | ~21 failed batches (0.5%)
        Failed batches default to None; can be fixed with --resume after completion
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
