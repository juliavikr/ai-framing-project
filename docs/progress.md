# Project Progress Log
# AI Strategic Framing Study — Bocconi Language Technology

Team: 2 people
Start date: ___________
Submission deadline: ___________

---

## Current Status
IN PROGRESS — Week 1 data collection

---

## Corpus Tracker — target ~6,090 docs

Update counts after every scraping session.

### Individuals — target ~2,000

| Actor           | Commercial  | Policy     | Public     | Total      | Status      |
|-----------------|-------------|------------|------------|------------|-------------|
| Sam Altman      | 121 / 130   | 0 / 120    | 0 / 130    | 121 / 380  | commercial done (blog exhausted at 121); policy/public: congress.gov+senate.gov 403; podcasts need transcript API — manual required |
| Dario Amodei    | 331 / 120   | 0 / 120    | 0 / 120    | 331 / 360  | commercial done ✓ (sitemap: 331 docs); policy/public: sitemap has 1 policy URL (already scraped); all podcast/CFR sources need manual collection |
| Jensen Huang    | 164 / 150   | 0 / 60     | 4 / 120    | 168 / 330  | commercial done ✓; policy: CSIS/Senate blocked + nvidia.com/gov JS-rendered; public: 4 from nvidianews — manual required for rest |
| Elon Musk       | —           | —          | —          | excluded   | excluded — insufficient corpus (21 docs archived to data/raw/_excluded/elon_musk/) |
| Satya Nadella   | 108 / 120   | 80 / 80    | 42 / 100   | 230 / 300  | all auto-scraped contexts done ✓ (author blog 108, on-the-issues 80, WorkLab 42); remaining public gap needs keynotes/press manually |
| Mark Zuckerberg | 125 / 120   | 0 / 60     | 0 / 150    | 125 / 330  | commercial done ✓; policy/public: all testimony + podcast sources need manual — Acquired/Lex transcripts not scrapable |
| Demis Hassabis  | 100 / 100   | 2 / 80     | 11 / 120   | 113 / 300  | commercial done ✓; policy: 2 from aisi.gov.uk, rest need UK Parliament manual; public: 11 from deepmind/research |
| **Subtotal**    |             |            |            | 1088 / 2000 |            |

### Companies — target ~2,000

| Actor           | Commercial  | Policy     | Public     | Total      | Status      |
|-----------------|-------------|------------|------------|------------|-------------|
| OpenAI          | 239 / 170   | 135 / 120  | 0 / 80     | 374 / 370  | commercial ✓ (239 via Wayback: blog/research/index patterns); policy ✓ (135 via index/*); public 0 — needs Wayback news/* pattern |
| Anthropic       | 233 / 150   | 1 / 120    | 0 / 80     | 234 / 350  | commercial ✓ (233 via sitemap /news + /research); policy: 1 URL only — all policy/public needs manual or alternative source |
| Google DeepMind | 155 / 150   | 0 / 100    | 0 / 80     | 155 / 330  | commercial ✓ (deepmind blog+research); policy/public: all sources are vague landing pages — needs specific URLs added manually |
| Meta AI         | 150 / 150   | 0 / 90     | 0 / 80     | 150 / 320  | commercial ✓ (trimmed to 150 most recent); policy dir deleted (was mislabeled news); policy/public needs manual re-collect |
| Microsoft       | 68 / 140    | 187 / 100  | 0 / 80     | 255 / 320  | policy ✓ (on-the-issues 187); commercial partial (68: blogs timeout before fetching); public sources too vague |
| Nvidia          | 73 / 150    | 0 / 80     | 0 / 80     | 73 / 310   | commercial partial (73 from blogs.nvidia.com); policy: nvidia.gov JS-rendered 0 candidates; public: newsroom JS-rendered 0 candidates |
| **Subtotal**    |             |            |            | ~1073      |             |

### Policymakers — target ~1,790 (no commercial context)

| Actor            | Policy      | Public     | Total      | Status      |
|------------------|-------------|------------|------------|-------------|
| EU Commission    | 305 / 380   | 12 / 100   | 317 / 480  | policy 80% ✓; public 12% — presscorner JS-blocked, audiovisual is video; manual or Wayback needed |
| US Congress      | 135 / 380   | 24 / 70    | 159 / 450  | policy 36% — all .senate.gov 403; only science.house.gov accessible; govinfo.gov JS-rendered; manual needed |
| UK DSIT          | 390 / 350   | 18 / 80    | 408 / 430  | policy ✓✓ 111% (gov.uk API 3s-delay pass got 186 more, total 390); public 22% — structural cap (18 DSIT AI speeches on gov.uk) |
| White House OSTP | 253 / 350   | 78 / 80    | 331 / 430  | policy 72% (Wayback CDX: 134 from ostp/* + 17 from ai/* = +151); public ✓ 98% |
| **Subtotal**     |             |            | 1215 / 1790 |            |

### TOTAL: ~3,283 / 6,090 (54%) — after dedup (balance report: outputs/tables/final_balance_report.txt)

---

## Balance Check

Run `python src/processing/build_corpus.py --balance-report` after each major scraping phase.

Last run: 2026-04-28  |  Full report: outputs/tables/final_balance_report.txt

| Rule                              | Target      | Actual                          | Pass? |
|-----------------------------------|-------------|---------------------------------|-------|
| Total documents                   | >= 6,000    | 3,283 (54.7%)                   | ✗     |
| Largest single actor share        | <= 10%      | UK DSIT 12.2%, Dario Amodei 10.1% | ✗  |
| Smallest context share            | >= 15%      | public 5.7% (186 docs)          | ✗     |
| Individuals share                 | ~35%        | 33.1% (1,087 docs)              | ✓     |
| Companies share                   | ~35%        | 35.6% (1,169 docs)              | ✓     |
| Policymakers share                | ~30%        | 31.3% (1,027 docs)              | ✓     |

**Critical gaps (end of automated scraping):**
- public context: 186 docs (5.7%) vs 15% minimum — needs ~750 more public docs across all actors
- UK DSIT policy over-represented at 12.2% — may need to trim ~72 docs before regression
- 24 actor/context pairs below 50-doc minimum (all are public or policy gaps)

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
