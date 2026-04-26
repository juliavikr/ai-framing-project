# Project Progress Log
# AI Strategic Framing Study — Bocconi Language Technology

Team: 2 people
Start date: ___________
Submission deadline: ___________

---

## Current Status
NOT STARTED

---

## Corpus Tracker — target ~6,090 docs

Update counts after every scraping session.

### Individuals — target ~2,000

| Actor           | Commercial  | Policy     | Public     | Total    | Status      |
|-----------------|-------------|------------|------------|----------|-------------|
| Sam Altman      | 0 / 130     | 0 / 120    | 0 / 130    | 0 / 380  | not started |
| Dario Amodei    | 0 / 120     | 0 / 120    | 0 / 120    | 0 / 360  | not started |
| Jensen Huang    | 0 / 150     | 0 / 60     | 0 / 120    | 0 / 330  | not started |
| Elon Musk       | 0 / 100     | 0 / 50     | 0 / 150    | 0 / 300  | not started |
| Mark Zuckerberg | 0 / 120     | 0 / 60     | 0 / 150    | 0 / 330  | not started |
| Demis Hassabis  | 0 / 100     | 0 / 80     | 0 / 120    | 0 / 300  | not started |
| **Subtotal**    |             |            |            | 0 / 2000 |             |

### Companies — target ~2,000

| Actor           | Commercial  | Policy     | Public     | Total    | Status      |
|-----------------|-------------|------------|------------|----------|-------------|
| OpenAI          | 0 / 170     | 0 / 120    | 0 / 80     | 0 / 370  | not started |
| Anthropic       | 0 / 150     | 0 / 120    | 0 / 80     | 0 / 350  | not started |
| Google DeepMind | 0 / 150     | 0 / 100    | 0 / 80     | 0 / 330  | not started |
| Meta AI         | 0 / 150     | 0 / 90     | 0 / 80     | 0 / 320  | not started |
| Microsoft       | 0 / 140     | 0 / 100    | 0 / 80     | 0 / 320  | not started |
| Nvidia          | 0 / 150     | 0 / 80     | 0 / 80     | 0 / 310  | not started |
| **Subtotal**    |             |            |            | 0 / 2000 |             |

### Policymakers — target ~1,790 (no commercial context)

| Actor            | Policy     | Public     | Total    | Status      |
|------------------|------------|------------|----------|-------------|
| EU Commission    | 0 / 380    | 0 / 100    | 0 / 480  | not started |
| US Congress      | 0 / 380    | 0 / 70     | 0 / 450  | not started |
| UK DSIT          | 0 / 350    | 0 / 80     | 0 / 430  | not started |
| White House OSTP | 0 / 350    | 0 / 80     | 0 / 430  | not started |
| **Subtotal**     |            |            | 0 / 1790 |             |

### TOTAL: 0 / 6,090

---

## Balance Check

Run `python src/processing/build_corpus.py --balance-report` after each major scraping phase.

| Rule                              | Target      | Actual | Pass? |
|-----------------------------------|-------------|--------|-------|
| Total documents                   | >= 6,000    | —      | —     |
| Largest single actor share        | <= 10%      | —      | —     |
| Smallest context share            | >= 15%      | —      | —     |
| Individuals share                 | ~35%        | —      | —     |
| Companies share                   | ~35%        | —      | —     |
| Policymakers share                | ~30%        | —      | —     |

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
