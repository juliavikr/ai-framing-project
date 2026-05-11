# AI Strategic Framing Study — Project Notes
# Bocconi University · Language Technology · 2026

---

## 1. Research Overview

**What is framing?** Framing refers to the selective emphasis of certain aspects of a
topic over others. When an actor frames AI as an engine of economic growth, they
highlight opportunity and downplay risk; when they frame it as a governance challenge,
they highlight oversight and downplay capability. The same underlying technology is
presented differently depending on what the communicator wants the audience to perceive
and prioritize. This project follows Entman (1993): frames are patterns of selection and
salience that promote particular interpretations.

**Why does context matter?** The central claim is that the same actor deliberately
shifts their framing depending on audience. A CEO speaking at a product launch (commercial
context) has every incentive to emphasize innovation and suppress risk. The same CEO
testifying before Congress (policy context) faces a regulatory audience and may
strategically foreground governance or, conversely, push back with an innovation
narrative to resist regulation. If framing is genuinely strategic, we should observe
systematic differences across contexts that cannot be explained by random variation.

**Research question:** To what extent do actors adapt their framing of AI across
communication contexts (commercial, policy, public), controlling for time, platform,
and actor type?

**Hypotheses:**
- H1: Context significantly predicts framing (β_context ≠ 0)
- H2: Commercial contexts increase innovation/economic framing; policy contexts increase
  risk/regulation framing
- H3: Individual actors show greater cross-context framing variance than institutions
  (individuals have more personal agency to adapt; companies have brand consistency pressures)

**Method in brief:** Scraped ~6,000 documents from 16 actors (individuals, companies,
policymakers). Sentence-level annotation via Claude Haiku (63,546 sentences, 5 frames).
Document-level framing scores as DVs in OLS regression (Models 1–3, three DVs each).

---

## 2. Data Collection

### 2.1 Corpus design and actor selection

**Actor selection rationale:** Actors were selected to represent the full spectrum of
AI discourse: leading AI companies and their CEOs (who shape commercial and public
narrative), and major regulatory bodies (who shape policy narrative). The individual/
company pairing is deliberate — each individual CEO is paired with their own company
(e.g., Altman/OpenAI, Amodei/Anthropic) so that H3 can be tested by comparing how
much an individual adapts versus the institutional voice of their own organization.
The four policymakers cover the three most active regulatory jurisdictions (US, EU, UK).

**16 actors across three types:**

| Type | Actors |
|------|--------|
| Individuals (6) | Sam Altman, Dario Amodei, Jensen Huang, Satya Nadella, Mark Zuckerberg, Demis Hassabis |
| Companies (6) | OpenAI, Anthropic, Google DeepMind, Meta AI, Microsoft, Nvidia |
| Policymakers (4) | EU Commission, US Congress, UK DSIT, White House OSTP |

**Elon Musk exclusion:** Only 21 documents collected from accessible sources (Tesla
EDGAR earnings, Rev.com transcripts). xAI blocked by Cloudflare; no accessible policy
corpus. Replaced by Satya Nadella — full 3-context coverage, clean individual↔company
pair with Microsoft. Raw files archived at `data/raw/_excluded/elon_musk/`.

**Three communication contexts** (defined strictly to avoid ambiguity):
- Commercial: company blogs, product launches, earnings calls, press releases, research publications
- Policy: congressional testimony, regulatory submissions, government strategy documents
- Public: media interviews, podcast appearances, public keynotes, op-eds

These three contexts represent three distinct audiences with different expectations:
investors/customers (commercial), legislators/regulators (policy), and the general
public (public). If actors are strategic communicators, we expect their framing to
vary systematically across these audiences.

**Actor positioning** — a categorical control variable for the actor's known public
strategic identity, assigned at intake based on publicly stated priorities:
- Capability: Altman, Nadella, Zuckerberg + their companies (AI as product/competitive edge)
- Safety: Amodei, Hassabis, Anthropic, Google DeepMind (AI risk and responsible development)
- Infrastructure: Huang, Nvidia (AI as compute/hardware layer)
- Regulator: EU Commission, US Congress, UK DSIT, White House OSTP (oversight mandate)

Positioning is included in Model 3 to test whether an actor's institutional identity
predicts their framing content independently of context — i.e., does a safety-positioned
actor consistently use more risk language regardless of whether they are writing a blog
post or testifying before Congress?

### 2.2 Collection methods and sources

**Web scraping (`scrape_individuals.py`, `scrape_companies.py`, `scrape_policy.py`):**
Paginated link collection, text extraction, date parsing from meta tags / JSON-LD,
URL-based deduplication, 1-second polite delay. Key workarounds:

- **OpenAI and White House OSTP** — both blocked or deleted from live web. Recovered
  via Wayback Machine CDX API (academic reproducibility; no authentication required).
- **Company research papers** — arXiv author-name queries added ~1,306 research papers
  for 6 companies. Classified as commercial context because research papers are official
  company output published under the company's name to demonstrate capability and attract
  talent/investment — the same function as a product blog post. Side effect: inflates
  company corpus share to 52.5% — acknowledged limitation.
- **Sam Altman blog**: 121 posts (source exhausted)
- **Dario Amodei**: 331 commercial via Anthropic sitemap (JS listing bypassed by
  fetching sitemap.xml directly)
- **YouTube transcripts**: all 14 targeted CEO videos had captions disabled — 0 docs
  from YouTube. Web transcripts collected instead (Lex Fridman, Dwarkesh Patel pages).

**Manual PDF ingestion (`ingest_pdf.py` — pdfplumber, MIN_WORDS=200):**
21 PDFs from official sources covering individual testimony, company policy submissions,
EU/US/UK regulatory documents, and public essays. Added 21 docs to the corpus.

**Data pipeline:**
- `clean_and_dedupe.py`: deduplication key = (actor, date, first 200 chars of text)
- `build_corpus.py`: schema validation, word count, post_chatgpt flag (1 if date ≥
  2022-11-30, the ChatGPT public launch date — used as a structural break to control
  for the possibility that AI framing changed across the entire corpus after ChatGPT
  made AI mainstream), UUID4 doc_id
- Loaded to Snowflake: `AI_FRAMING.PUBLIC.CORPUS` (5,925 rows, 8.8s)

### 2.3 Final corpus

**5,946 documents** (after PDF ingestion)

**By actor type:**

| Actor type   | Docs  | Share | Target | Status |
|--------------|-------|-------|--------|--------|
| Companies    | 3,111 | 52.3% | ~35%   | ✗ arXiv inflates |
| Policymakers | 1,704 | 28.7% | ~30%   | ✓ |
| Individuals  | 1,122 | 18.9% | ~35%   | ✗ structural gap |

**By context:**

| Context    | Docs  | Share | Target | Status |
|------------|-------|-------|--------|--------|
| Commercial | 3,661 | 61.6% | —      | — |
| Policy     | 2,048 | 34.4% | —      | — |
| Public     | 237   | 4.0%  | ≥15%   | ✗ structural ceiling |

**Per-actor document counts (actual / target):**

| Actor | Commercial | Policy | Public | Total |
|-------|-----------|--------|--------|-------|
| Sam Altman | 121 / 130 | 1 / 120 | 3 / 130 | **125** |
| Dario Amodei | 331 / 120 | 2 / 120 | 3 / 120 | **336** |
| Jensen Huang | 164 / 150 | 0 / 60 | 10 / 120 | **173** |
| Satya Nadella | 108 / 120 | 80 / 80 | 47 / 100 | **235** |
| Mark Zuckerberg | 125 / 120 | 1 / 60 | 3 / 150 | **129** |
| Demis Hassabis | 105 / 100 | 3 / 80 | 16 / 120 | **124** |
| OpenAI | 545 / 170 | 135 / 120 | 0 / 80 | **545** |
| Anthropic | 520 / 150 | 1 / 120 | 35 / 80 | **528** |
| Google DeepMind | 500 / 150 | 0 / 100 | 51 / 80 | **551** |
| Meta AI | 533 / 150 | 0 / 90 | 0 / 80 | **533** |
| Microsoft | 520 / 140 | 39 / 100 | 39 / 80 | **591** |
| Nvidia | 354 / 150 | 0 / 80 | 6 / 80 | **360** |
| EU Commission | 395 / 380 | 10 / 100 | — | **405** |
| US Congress | 246 / 380 | 23 / 70 | — | **269** |
| UK DSIT | 450 / 350 | 19 / 80 | — | **469** |
| White House OSTP | 561 / 350 | 0 / 80 | — | **561** |
| **TOTAL** | | | | **5,946** |

Individual policy/public gaps (Altman, Amodei, Huang, Zuckerberg) are structural:
congressional testimony blocked at congress.gov/senate.gov; podcast transcripts
YouTube-only with captions disabled; interview sites JS-rendered or paywalled.

**Balance check (as of 2026-05-08):**

| Rule | Target | Actual | Pass? |
|------|--------|--------|-------|
| Total documents | ≥ 6,000 | 5,946 (99.1%) | ✗ (close) |
| Largest single actor share | ≤ 10% | Microsoft 10.0% | ✓ (at cap) |
| Smallest context share | ≥ 15% | Public 4.0% | ✗ structural ceiling |
| Individuals share | ~35% | 18.9% | ✗ structural gap |
| Companies share | ~35% | 52.3% | ✗ arXiv |
| Policymakers share | ~30% | 28.8% | ✓ |

**Known imbalances (all documented as limitations):**
- arXiv papers inflate company commercial share — classified correctly per spec
- Public at 4.0% (target ≥15%) — structural ceiling: YouTube captions disabled
  for all target videos; podcasts JS-rendered; transcripts paywalled
- Individuals at 18.9% (target ~35%) — structural gap in individual policy/public access
- Microsoft at exactly 10.0% cap ✓; no actor exceeds cap

---

## 3. Annotation

### 3.1 Annotation scheme

**Why these 5 frames?** The frames were chosen to cover the dominant dimensions of AI
public discourse identified in prior computational framing studies and AI policy
literature: the opportunity narrative (Innovation, Economic Benefit), the risk narrative
(Risk/Harm, Existential/AGI), and the governance response (Regulation/Governance). This
5-frame scheme was developed iteratively — an 8-frame pilot collapsed several overlapping
categories, and a 3-frame version was too coarse to capture the regulation/risk distinction
that is central to H2. The 5-frame scheme achieved κ=0.86, validating that annotators
can reliably distinguish these categories.

**Why multi-label (not single best label)?** A single sentence can make multiple
simultaneous claims — e.g., "AI will create jobs [Economic Benefit] but requires
oversight [Regulation/Governance]." Forcing a single label would discard real signal.
Binary labels per frame preserve the co-occurrence structure. The None label captures
sentences that carry no discernible frame claim.

**Why require EXPLICIT statements?** Framing analysis requires observable textual
evidence. If annotators infer a frame from subtext or implication, two annotators will
infer differently — producing low Kappa. The "explicit only" rule anchors labels to
surface-level linguistic evidence, making the task tractable and reproducible.

Five binary labels per sentence (one or more labels, or None):

| Label | Definition |
|-------|-----------|
| Innovation/Progress | AI as transformative; EXPLICIT societal benefit or scientific advance claim. Descriptive statements about how AI works do NOT qualify. |
| Economic Benefit | EXPLICIT claim about jobs, revenue, productivity, or national competitiveness. Product announcements do NOT qualify. |
| Risk/Harm | CONCRETE near-term harms: bias, job loss, misuse, surveillance. Vague concern does NOT qualify. |
| Regulation/Governance | EXPLICIT institutional mechanism: law, policy framework, oversight body, compliance requirement, standards body. |
| Existential/AGI | Long-term civilizational risk, AGI, superintelligence, x-risk. Near-term risks go in Risk/Harm. |
| None | Procedural, descriptive, transitional. When a frame must be INFERRED rather than stated, use None. |

Full definitions in `docs/annotation_guidelines.md`.

### 3.2 Gold set and inter-annotator agreement

**What is Cohen's Kappa (κ)?** Kappa measures inter-annotator agreement corrected for
chance. κ=0 means agreement no better than random; κ=1 means perfect agreement.
Landis & Koch (1977) thresholds: κ<0.40 = poor, 0.40–0.60 = moderate, 0.61–0.80 =
substantial, >0.80 = almost perfect. The field standard for LLM annotation pipelines
is κ≥0.70 (substantial) before trusting the LLM to scale the task — below this,
human disagreement is too large to treat any single labeler (human or LLM) as ground truth.

**Gold set design:** 600-sentence stratified sample (300 per annotator, non-overlapping
for labeling, 100-sentence overlap for Kappa). Stratification across contexts (100 per
context) ensures Kappa is computed on a balanced sample rather than one dominated by the
commercial context (61% of corpus). Including ≥5 actors and a mix of pre/post-ChatGPT
sentences ensures the overlap set is representative of the full corpus's diversity.

**Round 1 — κ = 0.36, FAIL**
28 disagreements; 24/28 were None vs. frame. Root cause: None/frame boundary
underspecified. Guideline fix: added "The None Boundary — Critical Rules" (3 rules,
10 calibration examples from actual disagreements).

**Round 2 — κ = 0.37, FAIL**
28 disagreements again despite guideline revision. Root cause diagnosis: **the
disagreements were caused by garbage sentences in the corpus, not by annotation
ambiguity.** Identical sentences kept generating disagreements — React/Next.js JSON
fragments, FEMA boilerplate, Hungarian-language EU sentence, 3-word header fragments,
economic stats with no AI content.

**Corpus cleaning (`src/processing/clean_corpus.py`):**
Applied 5 filters at sentence level to the full 208,320-sentence pool:
1. Non-English (langdetect, confidence > 0.9): 712 removed
2. Too short (< 8 words): 20,723 removed
3. JSON/HTML fragments (regex on `{"`, `className`, `div`, `©`, `px-`, etc.): 9,184 removed
4. No AI keyword relevance (30 keywords including AI, model, neural, ChatGPT, etc.): 114,049 removed
5. Off-topic patterns (FEMA patterns, trade stats, ALL-CAPS fragments < 6 words): 106 removed

Result: **208,320 → 63,546 sentences** (30.5% retained). Saved to
`data/annotation/clean_sentences.csv`.

**Round 3 — κ = 0.86, PASS ✓** (2026-05-09)
New 100-sentence overlap set redrawn from the clean pool (34 commercial / 33 policy /
33 public, 15 actors, 70/30 post/pre-ChatGPT split):

| Label | κ | Agreement |
|-------|---|-----------|
| Innovation/Progress | 0.86 | 95% |
| Economic Benefit | 0.93 | 98% |
| Risk/Harm | 0.80 | 96% |
| Regulation/Governance | 0.83 | 95% |
| Existential/AGI | 0.88 | 99% |
| None | 0.85 | 93% |
| **OVERALL** | **0.86** | **96%** |

14 residual disagreements — all genuine edge cases (model cards as Regulation/Governance
vs. None; implicit risk vs. None). The jump from κ=0.37 to κ=0.86 in one step confirms
the first two rounds were suppressed entirely by corpus noise, not annotation disagreement.

### 3.3 Full LLM annotation

**Model:** `claude-haiku-4-5-20251001` via Anthropic Messages API  
**Configuration:** Batch 15 sentences/call · max_tokens 750 · inter-call delay 0.3s  
**Scope:** 63,546 clean sentences across 4,744 documents  
**Prompt design:** System prompt with all 5 frame definitions + None boundary rules;
output format: compact JSON array `[{"id": "...", "labels": ["..."]}]`. Compact JSON
instruction was critical — default pretty-printing doubled output token cost.

**Result (2026-05-10):** 63,546 sentences labeled; 22 failed batches (0.04%) defaulted to None.

| Label | Sentence-level frequency |
|-------|--------------------------|
| Innovation/Progress | 18.7% |
| Regulation/Governance | 11.5% |
| Risk/Harm | 8.7% |
| Economic Benefit | 6.0% |
| Existential/AGI | 1.1% |
| None | 58.1% |

Outputs: `data/annotation/labeled_sentences.csv` (sentence-level) ·
`data/annotation/labeled_documents.csv` (document-level framing scores)

### 3.4 Annotation quality — validation against gold set

`src/annotation/validate_llm_labels.py` compared Haiku's labels to the 100-sentence
human gold set (Person B v3 annotations).

| Label | Precision | Recall | F1 | Accuracy |
|-------|-----------|--------|----|----------|
| Innovation/Progress | 0.667 | 0.545 | 0.600 | 0.840 |
| Economic Benefit | 1.000 | 0.375 | 0.545 | 0.900 |
| Risk/Harm | 0.750 | 0.500 | 0.600 | 0.920 |
| Regulation/Governance | 1.000 | 0.381 | 0.552 | 0.870 |
| Existential/AGI | 0.667 | 0.400 | 0.500 | 0.960 |
| **MACRO AVG** | **0.847** | **0.534** | **0.633** | **0.915** |

**What do precision, recall, and F1 mean here?**
- **Precision** = of all sentences Haiku labeled as frame X, what fraction were actually
  frame X in human labels? High precision means few false positives (when Haiku fires,
  it is usually right).
- **Recall** = of all sentences humans labeled as frame X, what fraction did Haiku also
  label as X? High recall means few false negatives (Haiku catches most of the true instances).
- **F1** = harmonic mean of precision and recall; penalizes models that are strong on
  one dimension but weak on the other. The 0.80 target means we want both precision
  and recall to be reliably high.

**Diagnosis:** High precision (when Haiku assigns a frame, it is almost always correct)
but low recall (it defaults to None too often — ~47% of true positive labels missed).
This inflates the None rate to 58.1% vs ~33% in human annotations. Framing scores
are systematically lower than true values but **unbiased in direction** — positive
findings are conservative, not inflated.

**Why conservative is safer than inflated for academic claims:** If Haiku over-fires
(high recall, low precision) it would generate false positives — inventing framing
that isn't there — and inflate any observed context differences. That would make the
study's findings stronger than they really are: a type I error risk. Haiku under-fires
(high precision, low recall) — it misses real framing but rarely fabricates it. The
observed effect sizes are therefore underestimates; the true effects are likely larger.
Under-claiming is methodologically safer for an academic paper than over-claiming.

The F1=0.633 is below the 0.80 target and is documented as a methodology limitation.

Output: `outputs/tables/llm_validation.csv`

### 3.5 Cross-model robustness validation

**Motivation:** Is the F1=0.633 a Haiku-specific limitation, or a property of this
annotation task? If all LLMs struggle similarly, Haiku's limitations reflect genuine
task difficulty and our directional claims remain valid.

**Method:** Identical system prompt and batch format applied to the same 100-sentence
gold set using three alternative models from different providers, each independently
evaluated against human labels. Script: `src/annotation/validate_alternative_llm.py`.

```
Human gold (100 sentences, Person A v3)
        ↑             ↑              ↑              ↑
    Haiku         GPT-4o-mini   Llama 3.3 70B  Gemini 2.5 Flash
 (main corpus)    (OpenAI)        (Groq)          (Google)
```

| Label | Haiku F1 | GPT-4o-mini F1 | Llama 3.3-70B F1 | Gemini 2.5 Flash F1 |
|-------|----------|----------------|------------------|---------------------|
| Innovation/Progress | 0.600 | 0.516 | 0.439 | 0.286 |
| Economic Benefit | 0.545 | 0.471 | 0.400 | 0.154 |
| Risk/Harm | 0.600 | 0.667 | 0.545 | 0.000 |
| Regulation/Governance | 0.552 | 0.333 | 0.333 | 0.000 |
| Existential/AGI | 0.500 | 0.000 | 0.000 | 0.000 |
| **MACRO AVG** | **0.633** | **0.472** | **0.415** | **0.214** |
| Macro Precision | 0.847 | 0.471 | 0.386 | 0.335 |
| Macro Recall | 0.534 | 0.501 | 0.497 | 0.204 |

*Gemini 2.5 Flash note: some batches returned malformed JSON; results are partially
valid and treated as indicative only.*

**Key finding:** All models exhibit the same conservative bias — they default to None
too readily (low recall). This is a structural property of instruction-tuned LLMs on
conservative annotation tasks, not a Haiku idiosyncrasy. GPT-4o-mini and Llama have
higher recall but lower precision — they fire more freely and generate more false
positives, which would inflate framing scores and overstate cross-context differences.
Haiku's high-precision / conservative profile is preferable for academic claims.

**Haiku is the best-performing model** (macro F1 0.633 vs 0.415–0.472 for alternatives),
confirming it as the right choice for corpus-scale annotation.

**Per-frame pattern** (consistent across all models):
- Risk/Harm: easiest frame, most reliable DV (F1 0.54–0.67)
- Economic Benefit: weak across all models → confirms DV exclusion
- Existential/AGI: 3 of 4 models achieve F1=0.000 → confirms DV exclusion

Outputs: `outputs/tables/llm_validation_gpt-4o-mini.csv` ·
`outputs/tables/llm_validation_llama-3.3-70b-versatile.csv` ·
`outputs/tables/llm_validation_gemini-2.5-flash.csv`

### 3.6 Differential bias analysis (LLM consistency checks)

**The core question here:** We know Haiku misses ~47% of positive labels overall. The
key assumption for valid regression is that this miss rate is approximately uniform —
i.e., Haiku is equally likely to miss a Risk/Harm sentence whether it comes from OpenAI
or from the EU Commission, and whether it appears in a commercial or a policy document.
If that assumption holds, regression coefficients capture real framing differences
(though scaled down by the suppression factor). If the miss rate varies systematically
by actor or context, then observed differences in framing scores could partly reflect
where Haiku is more vs. less sensitive — not where actors actually frame differently.

Uniform suppression: direction preserved, magnitude underestimated — acceptable.
Differential suppression: observed differences partly spurious — not acceptable.

Four targeted checks were run to test this assumption.

**Check 1 — Recall by context**

| Frame | Commercial recall | Policy recall | Public recall |
|-------|-------------------|---------------|---------------|
| Innovation/Progress | 0.28 | 0.56 | 0.38 |
| Risk/Harm | 0.22 | 0.29 | 0.27 |
| Economic Benefit | — | 0.00 | — |
| Regulation/Governance | 0.40 | 0.38 | — |

Innovation recall is 28pp lower in commercial than policy. The LLM under-detects
innovation in commercial text more than in policy text — meaning the measured
commercial > policy gap on innovation_score is an **understatement** of the true
effect. The H2 innovation finding is conservative.

Economic Benefit recall = 0.00 in policy — the frame is invisible to the LLM in
the one context where cross-context variation is being tested. Any regression
coefficient on economic_score is measuring annotation failure, not real framing.

**Check 2 — Recall by positioning**

| Positioning | Innovation recall | Regulation recall |
|-------------|-------------------|-------------------|
| capability | 0.37 | 0.46 |
| safety | 0.30 | 0.42 |
| regulator | — | 0.92 |

Regulators have very high regulation recall (0.92) — the M1 regulation coefficient
is well-supported. Safety actors' lower innovation recall means their scores are
further suppressed — cross-actor comparisons of raw scores are unreliable.

**Check 3 — None rate by actor (full corpus)**

| Actor | None rate | Actor | None rate |
|-------|-----------|-------|-----------|
| US Congress | 28.7% | Meta AI | 64.1% |
| White House OSTP | 29.4% | Jensen Huang | 64.4% |
| EU Commission | 33.2% | Google DeepMind | 62.4% |
| UK DSIT | 44.6% | Nvidia | 66.3% |
| Sam Altman | 52.3% | Demis Hassabis | 66.8% |
| Satya Nadella | 53.1% | Dario Amodei | 67.5% |
| OpenAI | 54.8% | Anthropic | 68.2% |
| Microsoft | 57.2% | | |
| Mark Zuckerberg | 59.3% | | |

Range: 28.7% → 68.2% = **39.5pp spread**. Regulator actors (28–45% None) vs.
safety-positioning actors (62–68% None). This means raw framing scores cannot be
compared across actors — a document from US Congress with score 0.10 reflects much
less suppression than the same score from Anthropic.

**What remains valid:** Within-actor cross-context contrasts (the LLM's suppression
rate for a given actor applies equally to all that actor's documents regardless of
context label → M2 interaction terms are unaffected). Context effects when actor
is controlled. Directional findings where the bias is known to be conservative.

**What is unreliable:** Raw actor-level mean comparisons ("Anthropic frames more risk
than OpenAI") — systematically confounded by the 39.5pp differential.

**Check 4 — Sensitivity: M1 with recall-corrected scores**

Recall-corrected scores (raw_score / per-frame recall by context, clipped at 1.0)
substituted for raw scores in M1. All three context effects survive:

| Frame | Raw β_policy | Corrected β_policy | Survives? |
|-------|-------------|-------------------|-----------|
| innovation | −0.023 * | −0.042 * (p=0.016) | Yes |
| risk | +0.055 *** | +0.110 *** | Yes |
| regulation | +0.136 *** | +0.358 *** | Yes |

H1 is robust to the measurement bias.

**M3 multicollinearity:** The cluster {actor_type=policymaker, context=policy,
positioning=regulator, platform=regulatory_doc, platform=testimony} is near-perfectly
collinear — nearly all policymakers appear only in policy contexts via testimony and
regulatory_doc platforms. Statsmodels returns billion-scale coefficients for those
terms. **Only report positioning and platform terms from M3** (safety, infrastructure,
press_release, research_paper, speech). Do not cite actor_type or context[T.policy]
from M3 as standalone findings.

**M2 public context degeneracy:** Only Microsoft and Satya Nadella have public-context
data in M2. The combined cell is sparse, producing numerically degenerate estimates
(β ≈ −3.57e-17, spurious p=0.006). **Only commercial/policy contrasts from M2 are
interpretable.**

### 3.7 Innovation sub-classification

**Purpose:** Sub-classify Innovation/Progress sentences into 5 thematic categories
to characterize what type of innovation claim each actor makes (bonus column; does not
affect regression DVs).

**Sub-categories:** health_biotech · climate_energy · scientific · productivity · other_progress

**Method:** Claude Haiku with the same system prompt structure; batch 20 sentences/call;
streaming write with --resume and --finalize flags. Script: `src/annotation/subclassify_innovation.py`.

**Result (2026-05-11):** 12,426 Innovation/Progress sentences classified across 16 actors.

| Actor | n | Health/Bio% | Climate% | Scientific% | Productivity% | Other% |
|-------|---|------------|---------|------------|--------------|--------|
| Nvidia | 415 | 5.5 | 4.6 | 26.7 | **58.1** | 5.1 |
| Jensen Huang | 897 | 9.5 | 3.9 | 21.4 | **53.5** | 11.7 |
| Google DeepMind | 836 | 14.2 | 9.0 | **51.8** | 12.7 | 12.3 |
| Demis Hassabis | 447 | 13.2 | 6.3 | **50.1** | 14.3 | 16.1 |
| OpenAI | 966 | 9.6 | 0.2 | 35.2 | 43.1 | 11.9 |
| Dario Amodei | 1615 | 9.5 | 1.1 | 24.7 | 44.5 | 20.2 |
| Anthropic | 1271 | 5.8 | 0.9 | 24.5 | **50.6** | 18.2 |
| Microsoft | 1430 | 11.0 | 12.3 | 14.5 | 36.8 | 25.3 |
| Satya Nadella | 697 | 5.2 | 15.8 | 8.5 | 41.6 | 29.0 |
| EU Commission | 346 | 12.4 | 3.5 | 23.4 | 22.5 | 38.2 |
| UK DSIT | 1121 | 14.0 | 8.6 | 16.5 | 32.0 | 28.9 |
| White House OSTP | 307 | 8.5 | 3.6 | 40.4 | 14.0 | 33.6 |
| US Congress | 144 | 10.4 | 3.5 | 13.2 | 33.3 | 39.6 |
| Sam Altman | 102 | 4.9 | 1.0 | 28.4 | 23.5 | 42.2 |
| Meta AI | 630 | 8.9 | 3.3 | 25.1 | 39.0 | 23.7 |
| Mark Zuckerberg | 667 | 5.5 | 2.5 | 25.3 | 35.1 | 31.5 |

**Patterns:** Nvidia and Huang are productivity-dominant (AI as operational capacity);
Google DeepMind and Hassabis are scientific-dominant (AI as research advance); Amodei
and Anthropic cluster in scientific + other_progress. The sub-classification aligns
with each actor's broader institutional positioning.

Outputs: `data/annotation/innovation_subclassified.csv` ·
`outputs/tables/innovation_subclassification.csv` ·
`data/annotation/labeled_documents.csv` (innovation_subcategory_dominant column added)

---

## 4. Analysis

### 4.1 Feature engineering

**`src/features/build_features.py`** aggregates sentence-level labels to document level.

For each document d and frame F:
```
framing_score_F_d = (sentences labeled F in d) / (total sentences in d)
```

This is a 0–1 proportion: a 20-sentence document with 5 Innovation labels gets
innovation_score = 0.25.

**Why proportions rather than raw counts?** Documents vary enormously in length (a
blog post is 500 words; a congressional testimony is 10,000 words). A long document
will naturally contain more labeled sentences simply because it has more sentences —
not because the actor frames more intensely. Normalizing by document length makes
framing scores comparable across documents of different lengths. A proportion measures
framing density, which is what we care about.

**Why aggregate to document level rather than use sentence-level labels directly?**
58% of sentences are None. Working at sentence level would mean trying to model a
very sparse, noisy binary variable — most of the variance is just random within-document
variation. Document-level proportions smooth over this noise and give a stable signal
per observation. They also match the unit of analysis in the corpus (one document = one
actor, one context, one date).

**Filter:** Documents with fewer than 5 sentences excluded (3,411 removed from 5,946).
The n≥5 threshold is the minimum for a proportion to carry meaningful signal — a
2-sentence document where 1 sentence has a frame gives a score of 0.50, which is
numerically the same as a 100-sentence document with 50 labeled sentences, but reflects
much more uncertainty. Five sentences was chosen as a conservative floor that eliminates
single-paragraph boilerplate while retaining short but substantive documents.
Retains 2,535 documents for regression.

**Descriptive means by context** (before regression controls):

| Context | Innovation | Economic | Risk | Regulation | Existential |
|---------|-----------|---------|------|-----------|------------|
| Commercial | 0.229 | 0.053 | 0.062 | 0.056 | 0.010 |
| Policy | 0.210 | 0.087 | 0.117 | 0.194 | 0.009 |
| Public | 0.256 | 0.085 | 0.018 | 0.034 | 0.009 |

These descriptive means already visually confirm the direction of H1 and H2: policy is
higher on risk and regulation; commercial and public carry more innovation framing.

### 4.2 Dependent variable selection — why 3 of 5 frames

The annotation scheme produces 5 frames. Only 3 are used as regression DVs:
**innovation_score, risk_score, regulation_score.**

**Economic Benefit — excluded on measurement grounds**

LLM recall = 0.375 overall; recall = 0.00 in the policy context. The frame is
effectively invisible to the annotator in the exact context where cross-context
variation is being tested. Any regression coefficient on economic_score containing
context would be measuring annotation dropout, not real framing. Also low sentence
frequency (6.0%) further limits statistical power.

**Existential/AGI — excluded on frequency grounds**

1.1% sentence frequency produces near-zero document-level variance. OLS on this DV
would be severely underpowered and coefficients uninterpretable. The frame is also
concentrated in 2–3 actors (Amodei essays, Altman long-form pieces) — an actor-
specific signal rather than a corpus-wide pattern suitable for comparative regression.

**The three retained DVs:**

| DV | Sentence freq. | LLM recall range | Theoretical alignment |
|----|---------------|-----------------|----------------------|
| innovation_score | 18.7% | 0.28–0.56 by context | H2: commercial > policy |
| risk_score | 8.7% | 0.22–0.29 by context | H2: policy > commercial |
| regulation_score | 11.5% | 0.38–0.40 by context | H2: policy > commercial (strongest) |

All three have sufficient variance at document level and non-zero LLM recall in every
key context. They map directly onto the H1/H2 theoretical contrast.

### 4.3 Regression approach

**Why OLS (Ordinary Least Squares)?** OLS estimates the linear relationship between
predictors and the DV by minimizing the sum of squared residuals. For a 0–1 proportion
DV, the natural alternative is beta regression (designed for bounded continuous outcomes)
or logistic regression (for binary outcomes). We use OLS because: (1) framing scores
are averages of many binary sentence labels — by the central limit theorem, document-level
proportions are approximately normally distributed, especially for Innovation (18.7%
base rate) and Regulation (11.5%); (2) OLS coefficients are directly interpretable as
percentage-point changes; (3) OLS is standard in computational social science framing
studies, making our results comparable to prior work. The linear approximation is valid
given that most framing scores are well away from 0 or 1 (the boundary region where
OLS breaks down).

**Why three models rather than one?** Each model answers a different question:
- M1 (context + time only): Is there a context effect at all? Simple, clean, interpretable.
- M2 (actor + context + interaction): Do specific actors shift their framing? Requires
  restricting to well-covered actor×context pairs but captures strategic adaptation directly.
- M3 (full controls): After accounting for everything structural, what still predicts
  framing? Highest explanatory power but requires careful interpretation due to multicollinearity.

The three-model progression also provides robustness: if the context effects found in M1
disappear in M3, they were confounded by structural factors. The fact that they survive
(and in some cases strengthen) across models increases confidence in the findings.

**All three models are run separately for each of the three DVs** (innovation_score,
risk_score, regulation_score) — 9 regressions in total.

### 4.4 Interpreting coefficients and model fit

In OLS on a 0–1 proportion DV, **β = expected change in framing proportion per unit
change in the predictor**, holding all others constant.

Concrete examples from results:
- β_policy = +0.136 for regulation_score → policy documents have 13.6 percentage points
  more regulation framing than commercial documents, controlling for time.
- β_post_chatgpt = +0.048 for innovation_score → post-ChatGPT documents have 4.8pp
  more innovation framing than pre-ChatGPT documents, controlling for context.
- β_(Nadella × policy) = +0.271 for innovation_score → Nadella's policy documents have
  27.1pp more innovation framing than his commercial baseline + the average policy effect
  would predict. This excess is the interaction: strategic adaptation above and beyond
  the average context shift.

**Reference categories:** context = commercial · positioning = capability · platform = blog ·
actor_type = individual

**R² interpretation:** Fraction of total DV variance explained by the model.
Social science text analysis norms: R²=0.05–0.15 for a single contextual predictor;
R²>0.15 is strong. Regulation reaches R²=0.221 in M3 — the most structurally predictable
frame. Innovation reaches only R²=0.014 in M1, reflecting genuine actor-level heterogeneity
that M2 better captures (R²=0.082).

### 4.5 Model 1 — Does context predict framing? (H1)

**Specification:**
```
Frame_score_d = β₀ + β₁·C(context_d) + β₂·post_chatgpt_d + ε_d
```

**Purpose:** Minimal, interpretable test of H1. Only two predictors — context and a
pre/post-ChatGPT binary. Actor and platform variation is absorbed into the residual.
Simple enough to communicate the core H1 test without multicollinearity concerns.

**N = 2,535 documents**

**Results:**

| DV | R² | β_policy | β_public | β_post_chatgpt |
|----|-----|---------|---------|---------------|
| innovation_score | 0.014 | −0.023 * | +0.034 ns | +0.048 *** |
| risk_score | 0.041 | +0.055 *** | −0.043 *** | +0.016 * |
| regulation_score | 0.121 | +0.136 *** | −0.043 ** | +0.023 ** |

*** p<0.001 · ** p<0.01 · * p<0.05 · ns not significant

**Interpretation:**
- Context is significant for all three DVs → **H1 confirmed.**
- Regulation is the cleanest context effect: policy carries 13.6pp more regulation
  framing than commercial, explaining 12.1% of variance on its own.
- Risk follows the same direction: policy +5.5pp, public −4.3pp — risk framing peaks
  when addressing policymakers, drops in media/public settings.
- Innovation shows a negative policy coefficient (−2.3pp): commercial is the innovation
  context. The commercial baseline is high; policy deflects downward. This is the H2
  inversion — the absence of innovation in policy confirms commercial as the innovation
  register.
- Post-ChatGPT is positive and significant for all three frames: the discursive field
  intensified across all dimensions after November 2022.
- Low R² (innovation 0.014) means context alone leaves most framing variance unexplained;
  actor-level heterogeneity requires Model 2.

### 4.6 Model 2 — Strategic adaptation (H2/H3)

**Specification:**
```
Frame_score_d = β₀ + β₁·C(actor_d) + β₂·C(context_d) + β₃·C(actor_d):C(context_d) + ε_d
```

**Purpose:** Test whether specific actors adapt their framing beyond the average context
shift. The interaction term β₃ is the headline test: a positive, significant interaction
means that actor frames differently in that context than their baseline + the average
context effect would predict — i.e., strategic adaptation.

**N = 636 documents.** Restricted to actor×context pairs with ≥50 docs AND actors present
in ≥2 contexts. Below 50 docs per cell, OLS interaction estimates have inflated SE and
near-degenerate degrees of freedom. Qualifying actors:
- Microsoft: commercial n=84, policy n=152
- OpenAI: commercial n=194, policy n=81
- Satya Nadella: commercial n=59, policy n=66

Public context is excluded: only Microsoft and Nadella have public docs; the combined
cell produces degenerate estimates (β ≈ −3.57e-17, spurious p=0.006). Only
commercial/policy contrasts are reported.

**Significant interactions:**

| DV | R² | Actor × Context | β | p |
|----|-----|-----------------|---|---|
| innovation_score | 0.082 | Satya Nadella × policy | **+0.271** | <0.001 |
| innovation_score | 0.082 | OpenAI × policy | +0.101 | 0.006 |
| risk_score | 0.049 | OpenAI × policy | −0.056 | 0.025 |
| regulation_score | 0.078 | OpenAI × policy | −0.097 | <0.001 |

**Interpretation:**
- **Nadella × policy (+0.271***):** The largest and most theoretically significant
  coefficient in the study. Nadella's policy documents contain 27.1pp more innovation
  framing than his commercial baseline + the average policy shift would predict. When
  addressing policymakers, Nadella foregrounds AI as a driver of innovation rather
  than as a regulatory challenge — classic strategic framing: shaping the policy
  narrative toward economic opportunity.
- **OpenAI × policy on innovation (+0.101**):** OpenAI similarly increases innovation
  framing when addressing policymakers, though at lower magnitude.
- **OpenAI × policy on regulation (−0.097***):** Despite being in a policy context,
  OpenAI's policy documents have significantly less regulation language than other
  actors' policy documents — OpenAI appears to actively resist regulatory framing in
  its policy communications.
- **OpenAI × policy on risk (−0.056*):** Consistent: OpenAI's policy docs are
  systematically less risk-focused than the policy context would predict.

**Limitation:** Only 3 actors qualify, all from the commercial sector (1 individual,
2 companies). Results cannot be generalized to policymakers or the full 16-actor
corpus. Disclose explicitly in the paper methodology section.

### 4.7 Model 3 — Full structural controls

**Specification:**
```
Frame_score_d = β₀ + β₁·C(actor_type_d) + β₂·C(context_d) + β₃·C(positioning_d)
              + β₄·C(platform_d) + β₅·post_chatgpt_d + ε_d
```

**Purpose:** After partialling out actor type, context, positioning, platform, and
time, identify which structural characteristics independently predict framing. Highest
explanatory power of all three models.

**N = 2,535 documents**

**Multicollinearity caution:** The cluster {actor_type=policymaker, context=policy,
positioning=regulator, platform=regulatory_doc, platform=testimony} is near-perfectly
collinear — nearly all policymakers appear exclusively in policy contexts via testimony
and regulatory_doc platforms. Report only positioning and platform terms from M3.
Do not cite actor_type or context[T.policy] from M3 as primary findings.

**Key results — innovation_score (R²=0.064):**

| Predictor | β | p | Interpretation |
|-----------|---|---|----------------|
| C(platform)[speech] | +0.145 | 0.009 | Speeches carry 14.5pp more innovation framing than blogs |
| C(platform)[research_paper] | −0.084 | <0.001 | Research papers: 8.4pp less innovation framing |
| C(positioning)[safety] | −0.042 | <0.001 | Safety actors: 4.2pp less innovation framing than capability |
| post_chatgpt | +0.039 | <0.001 | Post-ChatGPT: innovation framing up 3.9pp |

**Key results — risk_score (R²=0.079):**

| Predictor | β | p | Interpretation |
|-----------|---|---|----------------|
| C(context)[policy] | +0.055 | <0.001 | Policy: +5.5pp risk above commercial |
| C(context)[public] | −0.043 | <0.001 | Public: 4.3pp less risk than commercial |
| C(positioning)[safety] | +0.038 | <0.001 | Safety actors: 3.8pp more risk framing |
| C(positioning)[infrastructure] | −0.049 | <0.001 | Infrastructure (Nvidia/Huang): 4.9pp less risk |
| post_chatgpt | +0.016 | 0.019 | Post-ChatGPT: risk framing up 1.6pp |

**Key results — regulation_score (R²=0.221 — highest across all models):**

| Predictor | β | p | Interpretation |
|-----------|---|---|----------------|
| C(positioning)[safety] | +0.050 | <0.001 | Safety actors: 5.0pp more regulation framing |
| C(platform)[press_release] | +0.043 | <0.001 | Press releases: 4.3pp more regulation framing |
| post_chatgpt | +0.035 | <0.001 | Post-ChatGPT: regulation framing up 3.5pp |
| C(platform)[research_paper] | −0.031 | 0.003 | Research papers avoid regulation framing |

**M3 interpretation:**
- Regulation framing is the most structurally predictable frame (R²=0.221). Safety
  positioning and the press_release platform independently drive regulation framing
  beyond what context alone explains.
- Safety positioning is a real content predictor: Anthropic, Amodei, Hassabis, and
  Google DeepMind consistently carry more risk and regulation framing and less
  innovation framing — their public positioning matches their linguistic output.
- Infrastructure positioning (Nvidia, Huang) substantially suppresses risk framing:
  actors who frame AI as physical infrastructure discuss societal risk less.
- Platform drives format: speeches are the most innovation-framed format; research
  papers resist both innovation and regulation language (technical rather than
  strategic); press releases are regulation-elevated.
- Post-ChatGPT intensification survives full controls for all three frames —
  November 2022 marked a genuine discursive shift.

### 4.8 Variance analysis — H3

**Purpose:** Test whether individual actors adapt more across contexts than companies.
H3 predicts individual σ > company σ.

**Method:** For each qualifying actor, first compute the mean framing score for each
of that actor's contexts (e.g., Nadella's mean innovation_score across all his commercial
documents, and separately across all his policy documents). Then take the standard
deviation of those context-level means. This SD captures how much the actor's framing
shifts across the communication contexts where they appear.

Standard deviation (rather than range = max − min) is used because it generalizes
cleanly to actors with 3 contexts without over-weighting a single extreme context, and
is additive across DVs for comparison.

**Qualification criterion:** ≥50 docs in ≥2 distinct contexts. Only 5 of 16 actors
qualify — the 50-doc threshold excludes nearly all individuals (structural gap in
policy/public coverage: YouTube-blocked, podcasts paywalled, conference transcripts
unavailable). This is a data availability constraint, not an analytical choice.

**Results:**

| Actor | Type | Contexts | Risk σ | Innovation σ | Regulation σ |
|-------|------|----------|--------|--------------|--------------|
| Satya Nadella | individual | comm/pol/pub | 0.050 | **0.129** | **0.064** |
| Microsoft | company | comm/pol/pub | 0.049 | 0.031 | 0.049 |
| UK DSIT | policymaker | pol/pub | 0.036 | 0.088 | 0.012 |
| OpenAI | company | comm/pol | 0.008 | 0.037 | 0.011 |
| Google DeepMind | company | comm/pub | 0.032 | 0.011 | 0.016 |

**H3 verdict:** Directionally supported — not formally testable.

Satya Nadella (sole qualifying individual) shows the highest innovation variance
(σ=0.129) and regulation variance (σ=0.064) of any qualifying actor — 4× higher than
his paired company Microsoft on innovation (σ=0.031). A t-test requires ≥2 individuals;
only 1 qualifies. Present in the paper as the strongest available individual-level
evidence, consistent with H3, with the corpus limitation disclosed explicitly.

**Connection to M2:** The Nadella × policy interaction in M2 (+0.271*** on innovation)
is the regression analogue of σ=0.129 in the variance analysis. Both reflect the same
underlying pattern from different angles: M2 tests significance and direction; variance
analysis quantifies magnitude.

---

## 5. Hypothesis Verdicts

**H1 — Does context predict framing?** ✓ CONFIRMED

Context is significant in M1 for all three DVs (all p<0.001). Policy increases
regulation (+0.136***) and risk (+0.055***); commercial is the reference and produces
the highest innovation framing. The finding is not driven by a single outlier context —
all three DVs show consistent, directional context effects. Confirmed robust by
recall-corrected sensitivity analysis.

**H2 — Commercial → innovation/economic; policy → risk/regulation?** ✓ PARTIALLY CONFIRMED

- Policy → regulation: strongly confirmed (β=+0.136***)
- Policy → risk: confirmed (β=+0.055***)
- Commercial → innovation: confirmed by inversion (policy β=−0.023* below commercial baseline)
- Commercial → economic benefit: dropped — LLM recall=0.00 in policy makes this untestable

The H2 innovation finding is conservative: innovation recall is substantially lower in
commercial (0.28) than policy (0.56), meaning the measured commercial > policy gap
understates the true effect. True difference is likely larger.

**H3 — Individuals adapt more than institutions?** ✓ DIRECTIONALLY SUPPORTED, not testable

Satya Nadella (sole qualifying individual) shows the highest cross-context variance of
any qualifying actor on innovation (σ=0.129) and regulation (σ=0.064), substantially
above paired company Microsoft (σ=0.031, 0.049). A t-test cannot be run — only 1
individual qualifies due to corpus coverage limitations. Present as illustrative finding.

---

## 6. Key Methodological Limitations

1. **39.5pp None rate spread across actors.** Regulator actors have 28–45% None rates;
   safety-positioning actors have 62–68%. Raw cross-actor framing score comparisons are
   confounded by differential LLM sensitivity to writing style. Do not report "Anthropic
   frames more X than OpenAI" as a primary finding. Within-actor context contrasts (M2
   interactions) are unaffected.

2. **LLM macro F1 = 0.633 (recall = 0.534).** Haiku misses ~47% of true positive labels.
   Framing scores are underestimates of true prevalence. Positive findings are
   conservative, not inflated — the direction of bias is known and documented.

3. **Economic Benefit excluded.** LLM recall = 0.00 in policy context. Cannot test
   H2 for this frame with the current annotations.

4. **Model 2 restricted to 3 actors (N=636).** Only Microsoft, OpenAI, and Satya
   Nadella have sufficient coverage in 2+ contexts. M2 results cannot be generalized
   to the full corpus.

5. **H3 not formally testable.** Only 1 individual actor (Nadella) qualifies for
   variance analysis. Insufficient degrees of freedom for a t-test.

6. **Public context at 4.0% (target ≥15%).** Structural ceiling: YouTube captions
   disabled, podcasts paywalled, conference transcripts unavailable. Document in paper
   data section as a research limitation.

7. **arXiv inflates company commercial share to 52.3%.** Papers are classified correctly
   per spec (company research output), but this creates an imbalanced type distribution.
   Document in methodology.

8. **M3 multicollinearity.** Policymaker / regulator / policy / testimony cluster is
   near-perfectly collinear. Only report positioning and platform terms from M3.

---

## 7. Key Decisions Log

| Decision | Alternatives considered | Reason chosen |
|----------|------------------------|---------------|
| Replace Musk with Nadella | Keep Musk with 21 docs; drop actor entirely | Nadella has full 3-context corpus, clean pair with Microsoft |
| Wayback CDX for OpenAI/OSTP | Headless scraping; accept gap | Academic reproducibility; no authentication required |
| arXiv for company research | Skip research papers | Fills commercial context gap for AI labs; papers are public company output |
| 5 annotation frames | 8 frames (original draft); 3 frames (simplified) | 5 balances coverage with Kappa feasibility |
| Clean corpus before Round 3 | Revise guidelines a third time | Root cause was data quality, not label ambiguity — guidelines had been updated with no effect |
| Snowflake for storage | Local CSV only; PostgreSQL | Shared access between 2 teammates; free trial; heavy queries in warehouse |
| Haiku for LLM labeling | Claude Sonnet; GPT-4.1-mini | Cheapest option with sufficient label quality; ~$10 for full corpus |
| Compact JSON in system prompt | Smaller batch size | Haiku pretty-prints by default (~1,000 tokens/batch); one instruction line halved output cost |
| Pair-level M2 filtering | Actor-level filtering | Actor-level drops every actor with a thin public context → N=0; pair-level lets actors contribute where data exists |
| 3 DVs not 5 | Run all 5 | Economic Benefit recall=0.00 in policy; Existential/AGI frequency=1.1% — both produce unreliable regression estimates |
| Drop Economic Benefit from H2 | Report with caveats | LLM recall=0.00 in policy — any coefficient measures annotation failure, not framing |
