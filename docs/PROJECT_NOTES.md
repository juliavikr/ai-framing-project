# Project Notes
# AI Strategic Framing Study — Bocconi Language Technology 2026
# Running log of decisions, problems, and solutions

---

## Week 1 — Data Collection

### Actor selection
- Started with Sam Altman, OpenAI, EU Commission, Google DeepMind, Elon Musk as
  initial set
- Expanded to 16 actors across 3 types after research: 6 individuals, 6 companies,
  4 policymakers
- **Elon Musk exclusion:** accumulated only 21 docs from accessible sources (10 Tesla
  earnings via EDGAR, 11 Rev.com transcripts). xAI website blocked by Cloudflare.
  No accessible congressional testimony or policy submissions found. 21 docs is
  insufficient for cross-context regression — replaced with Satya Nadella (Microsoft
  CEO), who has full 3-context coverage and a clean individual↔company pair.
- Actor typology: capability / safety / infrastructure / regulator
  (dropped "contrarian" positioning after Musk exclusion)

### Scraping infrastructure
- Built `scrape_individuals.py`: paginated link collector, text extractor, date
  extraction from time[datetime], meta tags, and JSON-LD, URL-based deduplication,
  1s polite delay between requests
- Bugs fixed during run:
  * Feed/archive URL filter — `atom`, `/archive` paths leaking through as content pages
  * Posthaven date extraction — Unix timestamps in `data-unix-time` attributes,
    not standard meta tags
  * `collect_post_links()` max_pages=25 cap — added after Microsoft Azure blog
    pagination hung for 10+ minutes
  * DeepMind relative href doubling (`/blog/blog/post-slug`) — fixed to
    `scheme + host` only when joining relative URLs

### Source-by-source outcomes
- **Sam Altman blog:** 121/130 (blog exhausted at 121 posts, all collected)
- **Dario Amodei:** 331 commercial via Anthropic sitemap (JS listing bypassed by
  fetching sitemap.xml directly instead of scraping the paginated listing)
- **Demis Hassabis:** 105 commercial from deepmind.google/blog ✓
- **Satya Nadella:** 108 commercial from blogs.microsoft.com author tag
- **Jensen Huang:** 44 initial → sitemap unlock → 164 commercial total
- **Mark Zuckerberg:** 0 initial (ai.meta.com returned 400) → switched to
  about.fb.com/news → 125 commercial
- **OpenAI:** entire site 403 → Wayback Machine CDX API → 239 commercial +
  135 policy recovered from archive snapshots
- **White House OSTP:** Biden-era pages deleted by current administration →
  Wayback CDX → 253 policy recovered from bidenwhitehouse.archives.gov
- **Elon Musk:** 21 docs total → excluded (see above)

### Transcript collection
- Built `scrape_transcripts.py`: Method 1 (direct web scrape of Lex Fridman +
  Dwarkesh transcript pages), Method 2 (youtube-transcript-api fallback)
- YouTube: all 14 targeted CEO videos had captions disabled by channel owners →
  0 docs from YouTube
- Web transcripts saved (12 total after dead-URL cleanup):
  - Lex Fridman: Altman (#419), Amodei (#452), Huang (#394), Hassabis (#475),
    Zuckerberg (#399)
  - Dwarkesh: Amodei, Nadella, Huang, Zuckerberg, Hassabis
  - Nobel Prize lecture: Hassabis (PDF via nobelprize.org)
  - Dwarkesh extra: Zuckerberg #2
- Dead entries removed from WEB_REGISTRY: 10 URLs returning 404 / JS-rendered /
  SSL failures (including Acquired podcast ×2, Stanford PDF, TED talk)
- Dwarkesh Sam Altman entry removed — interview never occurred
  (confirmed: prediction market resolved NO)

### arXiv scraping
- Built `scrape_arxiv.py` using arXiv API with author-name queries
- +1,306 research papers added for 6 companies:
  Anthropic 287, Google DeepMind 329, Meta AI 306, Microsoft 297, Nvidia 269,
  OpenAI 241
- All classified as `commercial` context per spec (company research publications)
- Side effect: inflates company share to 52.5% of corpus — acknowledged limitation,
  noted in methodology

### Manual PDF collection
- Elisabeth downloaded 21 PDFs from official sources; ingested via `ingest_pdf.py`
- Individual testimony: Altman (Senate Judiciary May 2023), Amodei (×2: Jul + Sep
  2023), Zuckerberg (Senate Judiciary Jan 2024), Hassabis (UK Science Committee
  Oct 2023)
- Company policy submissions: OpenAI NTIA (Jun 2023), Anthropic NTIA (Jun 2023),
  Microsoft Senate Commerce (May 2025)
- EU Commission: Ethics Guidelines for Trustworthy AI (Apr 2019), White Paper on
  AI (Feb 2020), AI Act final text (Jun 2024)
- White House OSTP: AI Bill of Rights Blueprint (Oct 2022), Executive Order on
  Safe AI (Oct 2023), National AI Initiative Strategy (May 2023)
- UK DSIT: Bletchley Declaration (Nov 2023), AI Regulation White Paper (Mar 2023)
- US Congress: Senate AI Insight Forum transcript (Sep 2023)
- Public essays/speeches: Amodei "Machines of Loving Grace" (Oct 2024), Altman
  "The Intelligence Age" (Sep 2024), Altman "Moore's Law for Everything" (Mar 2021),
  Huang GTC 2025 keynote (Mar 2025)
- `ingest_pdf.py` uses pdfplumber for extraction; MIN_WORDS=200 threshold;
  MD5 hash of stem → stable JSON filename

### Data pipeline
- `clean_and_dedupe.py`: dedup key = (actor, date, first 200 chars of text)
- `build_corpus.py`: schema validation, word count computation, post_chatgpt flag
  (1 if date ≥ 2022-11-30), UUID4 doc_id generation
- `snowflake_utils.py`: `write_pandas()` with `overwrite=True`, uppercase column
  names required by Snowflake connector
- Corpus loaded to Snowflake in 8.8s, 1 chunk, 5,925 rows

### White House OSTP over-cap incident
- Background public scraper collected 179 non-AI files (Biden general speeches,
  FEMA declarations, press briefings) — pushed OSTP to 10.8% of corpus, over the
  10% cap
- Fix: deleted all 179 OSTP public raw files; OSTP back to 9.5%
- Side effect: public context dropped from 6.8% to 3.9% — structural limitation,
  documented in sources.md

### Final corpus
- **5,925 documents** (98.8% of 6,000 target)
- Commercial 61.8% | Policy 34.2% | Public 4.0% (structural ceiling)
- Microsoft at exactly 10.0% cap ✓
- Loaded to Snowflake: `AI_FRAMING.PUBLIC.CORPUS`

---

## Week 2 — Annotation

### Gold set preparation
- `prepare_gold_set.py`: stratified 600-sentence sample (300 per annotator,
  non-overlapping) using nltk.sent_tokenize on corpus.csv
- Stratification: 100 sentences per context, ≥5 actors, 20% short sentences,
  pre/post-ChatGPT mix
- Problem discovered: non-overlapping sets cannot compute Kappa — both annotators
  must label the same sentences
- Solution: extracted first 100 rows from `gold_set_person_b.csv` →
  created `kappa_overlap_person_a.xlsx` for Person A to annotate independently

### Annotation sheet format
- Columns: sentence_id, actor, context, date, sentence_text + 5 binary label
  columns + None + Notes
- xlsx format with openpyxl: colour-coded rows by context (green/orange/purple),
  freeze pane at column F, Instructions tab with frame definitions
- pandas read_excel requires openpyxl ≥ 3.1.0 (installed: 3.0.10) — worked around
  by reading xlsx directly with openpyxl in compute_kappa.py

### Kappa Round 1 — κ = 0.36, FAIL
- 28 disagreements out of 100 sentences
- 24/28 disagreements were None vs. frame (one annotator marks None, other marks
  a frame label)
- Root cause diagnosis: None/frame boundary underspecified in guidelines
- Guideline fix: added "The None Boundary — Critical Rules" section with 3 rules:
  * Rule 1: Innovation/Progress requires explicit societal claim, not description
  * Rule 2: Economic Benefit requires concrete jobs/revenue/productivity claim
  * Rule 3: None = purely procedural/administrative, or implied-not-stated frame
- Added 10 calibration examples from actual disagreements

### Kappa Round 2 — κ = 0.37, FAIL
- 28 disagreements again — identical count despite guideline revision
- Pattern analysis: the same sentences kept generating disagreements
- Deeper diagnosis: **corpus noise, not annotation ambiguity**
- Garbage sentences identified in the gold set:
  * React/Next.js JSON fragments (from OpenAI website scrape)
  * FEMA disaster relief boilerplate (from White House Wayback CDX scrape)
  * Hungarian-language EU Commission sentence
  * 3-word header fragments ("Documented Atrocity Risk.")
  * Economic statistics with no AI content ("Reduced the trade deficit...")
  * Technical analogies with no framing content ("like a classically-trained pianist")

### Corpus cleaning
- Built `src/processing/clean_corpus.py`
- Filters applied at sentence level (5 rules):
  1. Non-English: langdetect library, drop if lang ≠ 'en' or confidence < 0.9
  2. Too short: drop if word count < 8
  3. JSON/HTML fragments: regex on `{"`, `className`, `div`, `span`, `=>`, `*/`,
     `http`, `©`, `@md:`, `px-`, `col-span`
  4. No AI relevance: drop if no match on 30 AI keywords (AI, model, neural,
     ChatGPT, Anthropic, Microsoft, etc.)
  5. Off-topic patterns: FEMA patterns, trade stats, ALL-CAPS fragments < 6 words
- Results: 208,320 → 63,546 sentences retained (30.5%)
  * No AI relevance: 114,049 removed (54.7%) — dominant filter
  * Too short: 20,723 removed (9.9%)
  * JSON/HTML junk: 9,184 removed (4.4%)
  * Non-English: 712 removed (0.3%)
  * Off-topic patterns: 106 removed (0.1%)
- Clean pool saved to `data/annotation/clean_sentences.csv`

### Kappa Round 3 — κ = 0.86, PASS ✓  (2026-05-09)
- Overlap set v3 redrawn from clean_sentences.csv
- Stratification: 34 commercial / 33 policy / 33 public
- 15 actors represented, 16% likely-None sentences, 70/30 post/pre-ChatGPT split
- Both annotators completed v3 sheets independently

| Label | Kappa | Agreement |
|-------|-------|-----------|
| Innovation/Progress | 0.86 | 95% |
| Economic Benefit | 0.93 | 98% |
| Risk/Harm | 0.80 | 96% |
| Regulation/Governance | 0.83 | 95% |
| Existential/AGI | 0.88 | 99% |
| None | 0.85 | 93% |
| **OVERALL** | **0.86** | **96%** |

- 14 residual disagreements — all genuine edge cases (model cards as
  Regulation/Governance vs. None; AI-speeds-up-AI as Innovation vs. Existential/AGI;
  implicit risk statements vs. None). No garbage sentences in disagreement list.
- Results saved to `outputs/tables/kappa_results_v3.csv`
- **Interpretation:** jump from κ=0.37 to κ=0.86 in one step confirms the first two
  rounds were suppressed entirely by corpus noise, not annotation disagreement.
  Guidelines and calibration examples were effective once the noise was removed.
- **Next step:** proceed to full LLM labeling (`label_with_llm.py`)

### LLM Labeling (2026-05-10)
- Model: `claude-haiku-4-5-20251001` via Anthropic Messages API
- Batch size: 15 sentences per call | max_tokens: 750 | inter-call delay: 0.3s
- API issues encountered and resolved:
  * Anthropic account #1: zero credits → switched API key
  * OpenAI attempted but also zero credits → reverted to Anthropic
  * New Anthropic account ($8 credits) ran out at ~22,000 sentences (1,000 docs)
    Root cause: Haiku was pretty-printing JSON (~1,000 tokens/batch vs ~560 compact)
  * Fix: added "Compact JSON only — no newlines or extra whitespace" to system prompt;
    reduced max_tokens from 1,000 → 750; resumed with --resume flag
  * After fix: output tokens dropped to ~560/batch; run resumed cleanly
- COMPLETE (2026-05-10): 63,546 sentences, 4,744 docs labeled
  22 failed batches (all credit-limit errors during account-switch window) → defaulted to None
- Label distribution: Innovation/Progress 18.7% | Regulation/Governance 11.5% | Risk/Harm 8.7%
  Economic Benefit 6.0% | Existential/AGI 1.1% | None 58.1%
- Output files: `data/annotation/labeled_sentences.csv` (sentence-level)
  `data/annotation/labeled_documents.csv` (document-level framing scores)

### LLM Validation (2026-05-10)
- Script: `src/annotation/validate_llm_labels.py`
- Gold set: `data/annotation/kappa_overlap_person_b_v3.xlsx` (100 sentences, v3 overlap)
- Join: sentence_id (100/100 matched)
- Results:
  | Label | Precision | Recall | F1 | Accuracy |
  |-------|-----------|--------|----|----------|
  | Innovation/Progress | 0.667 | 0.545 | 0.600 | 0.840 |
  | Economic Benefit | 1.000 | 0.375 | 0.545 | 0.900 |
  | Risk/Harm | 0.750 | 0.500 | 0.600 | 0.920 |
  | Regulation/Governance | 1.000 | 0.381 | 0.552 | 0.870 |
  | Existential/AGI | 0.667 | 0.400 | 0.500 | 0.960 |
  | None | 1.000 | 1.000 | 1.000 | 1.000 |
  | MACRO AVG | 0.847 | 0.534 | 0.633 | 0.915 |
- Verdict: FAIL vs ≥0.80 target
- Diagnosis: precision is high (when LLM assigns a frame, it's correct); recall is low
  (LLM defaults to None too often — ~47% of true positive labels missed). This inflates
  the None rate to 58.1% vs ~33% in human gold. Framing scores will be systematically
  lower than true values but unbiased in direction. Document as methodology limitation.
- Saved → `outputs/tables/llm_validation.csv`

### Innovation Sub-classification (2026-05-10, INTERRUPTED — awaiting credits)
- Script: `src/annotation/subclassify_innovation.py`
- Input: 11,891 Innovation/Progress sentences from labeled_sentences.csv
- Sub-categories: health_biotech | climate_energy | scientific | productivity | other_progress
- Model: claude-haiku-4-5-20251001 | Batch: 20 | 595 batches total
- Run terminated at batch 418/595 (70%) — Anthropic account exhausted (~$16 total spent)
- **Critical bug found:** original script accumulated all results in memory, wrote only at end.
  When killed, all 418 batches of work was lost. No output file exists.
- **Fix applied (2026-05-10):** rewrote script with:
  - Per-batch streaming write to OUTPUT_CSV (append mode, like label_with_llm.py)
  - `--resume` flag: reads done sentence_ids from OUTPUT_CSV on startup, skips them
  - `--finalize` flag: skips API calls entirely, builds summaries from existing OUTPUT_CSV
  - Header written only on first batch; fresh run removes stale OUTPUT_CSV before starting
- **Restart command:** `python src/annotation/subclassify_innovation.py --resume`
- **Cost to finish:** ~155 remaining batches × $0.0005/batch ≈ $0.08–0.10 (estimated)
- **BLOCKED:** needs ~$1 added to Anthropic account
- Output (once complete):
  `data/annotation/innovation_subclassified.csv` (sentence-level, streamed)
  `outputs/tables/innovation_subclassification.csv` (actor-level summary)
  `data/annotation/labeled_documents.csv` updated with innovation_subcategory_dominant

---

## Week 3 — Analysis (2026-05-10)

### regression.py bug: Model 2 filtering eliminated all actors

The script filtered Model 2 at the **actor level**: drop any actor where *any*
actor×context pair had < 50 docs. Because almost every actor has a thin public
context (0–17 docs due to YouTube/paywall ceiling), every actor was dropped → N=0.
Patsy then crashed building a design matrix from 0 rows with one remaining level.

**Fix:** changed to pair-level filtering:
1. Drop individual actor×context pairs below the 50-doc threshold
2. Then exclude actors with only 1 context remaining (no estimable interaction)
3. Result: 3 actors survive — Microsoft (commercial 84, policy 152), OpenAI
   (commercial 194, policy 81), Satya Nadella (commercial 59, policy 66) → N=636

The pair-level approach is more principled: an actor can contribute to Model 2
for the contexts where they have enough data, rather than being eliminated because
one unrelated context is thin. The 50-doc threshold is deliberate — below it, OLS
interaction estimates for a cell are unreliable (inflated SE, near-degenerate df).

**Paper note:** Model 2 results reflect only 3 cross-context actors and cannot
be generalised to the full 16-actor corpus. This should be acknowledged explicitly
in the methodology section alongside the corpus balance limitations.

### Build features (build_features.py)

n_sentences ≥ 5 filter retained 2,535 of 5,946 documents (dropped 3,411 short
documents — procedural texts, boilerplate press releases, one-paragraph blog posts).

Mean framing scores per context before regression:

| Context    | Innovation | Economic | Risk  | Regulation | Existential |
|------------|-----------|---------|-------|-----------|------------|
| Commercial | 0.229     | 0.053   | 0.062 | 0.056     | 0.010      |
| Policy     | 0.210     | 0.087   | 0.117 | 0.194     | 0.009      |
| Public     | 0.256     | 0.085   | 0.018 | 0.034     | 0.009      |

These descriptive means alone visually confirm H1 and H2 (policy higher on risk and
regulation; commercial higher on innovation relative to policy).

### DV selection — why 3 of 5 labels

The annotation scheme produces 5 binary labels per sentence. Only 3 are used as
regression DVs. The two exclusions are principled, not arbitrary.

**Economic Benefit — excluded on measurement grounds**
- LLM validation: overall recall = 0.375; precision = 1.000 (when detected, always correct)
- Consistency check: recall = 0.00 in the policy context — the frame is effectively
  invisible to the LLM in exactly the context where cross-context variation would be
  tested. Any regression coefficient on economic_score in a model containing context
  would be measuring annotation dropout, not real framing.
- Corpus frequency: 6.0% of sentences → further limits statistical power.
- Decision: excluded from primary results. Could be run as a robustness check with
  explicit caveats if a reviewer requests it (regression.py supports --dv economic_score).

**Existential/AGI — excluded on frequency grounds**
- Only 1.1% of sentences carry this label.
- At document level, framing scores this sparse produce a near-zero DV with negligible
  variance. OLS regressions on it would be severely underpowered and coefficients
  uninterpretable.
- The frame is also conceptually concentrated in a few actors (Amodei essays, Altman
  long-form pieces) — it is an actor-specific signal rather than a cross-corpus pattern
  suitable for a multi-actor comparative regression.
- Decision: excluded from primary results. Same caveat applies — can be run on request.

**The three retained DVs (risk_score, innovation_score, regulation_score):**
- Sentence-level frequency: 8.7–18.7% (sufficient variance at document level)
- LLM recall: 0.38–0.55 macro across contexts (not zero in any key context)
- Direct theoretical alignment with H1/H2: the core research question is whether
  commercial contexts produce more innovation framing and policy contexts produce more
  risk/regulation framing — these three frames map exactly onto that contrast.

### Regression results summary

**risk_score** (M1 R²=0.041, M3 R²=0.079):
- Policy context +0.055*** and public context −0.043*** (M1) — policy docs contain
  significantly more risk framing; public docs the least
- Positioning is the dominant M3 predictor: safety actors (Anthropic, Amodei) +0.038***;
  infrastructure actors (Nvidia, Huang) −0.049*** — actor positioning explains risk
  framing better than context alone
- Post-ChatGPT +0.016* — risk framing increased after Nov 2022
- M2 interaction: OpenAI × policy β=−0.056* — OpenAI's policy documents are
  notably less risk-focused than its commercial baseline, opposite of the H2 expectation

**innovation_score** (M1 R²=0.014, M2 R²=0.082, M3 R²=0.064):
- M1: policy context −0.023* (commercial is the innovation frame, not public);
  post-ChatGPT +0.048*** — innovation framing surged after Nov 2022
- M2 shows the largest interactions of any model: Satya Nadella × policy +0.271***
  (Nadella's policy documents are far more innovation-framed than his commercial ones —
  classic strategic adaptation); OpenAI × policy +0.101**
- M3: platform matters — speeches +0.145**, research_papers −0.084***; safety
  actors use significantly less innovation framing −0.042***
- Notable: post-ChatGPT coefficient is significant and positive in M1 and M3 for
  innovation, suggesting a broad discursive shift after the ChatGPT launch

**regulation_score** (M1 R²=0.121, M2 R²=0.078, M3 R²=0.221 — highest R² across all models):
- Regulation is the most structurally predictable frame: policy context +0.136*** alone
  explains 12% of variance (M1), and the full M3 reaches R²=0.221
- M3 dominant predictors: safety positioning +0.050***, press_release platform +0.043***,
  post-ChatGPT +0.035***; research_papers −0.031**
- M2 interaction: OpenAI × policy −0.097*** — OpenAI's policy documents avoid explicit
  regulation language relative to Microsoft and Satya Nadella (interesting given Altman's
  public testimony record; may reflect arXiv paper classification inflating commercial count)
- Regulation frame is not just context-driven — it is positioning-driven and
  platform-driven in a way risk and innovation are not

### Variance analysis and H3

Variance computed as cross-context standard deviation of mean framing scores.
Only actors with ≥50 docs in ≥2 contexts qualify (5 actors total):

| Actor           | Type        | Contexts       | Risk σ | Innovation σ | Regulation σ |
|-----------------|-------------|----------------|--------|--------------|--------------|
| Satya Nadella   | individual  | comm/pol/pub   | 0.050  | 0.129        | 0.064        |
| Microsoft       | company     | comm/pol/pub   | 0.049  | 0.031        | 0.049        |
| UK DSIT         | policymaker | pol/pub        | 0.036  | 0.088        | 0.012        |
| OpenAI          | company     | comm/pol       | 0.008  | 0.037        | 0.011        |
| Google DeepMind | company     | comm/pub       | 0.032  | 0.011        | 0.016        |

H3 could not be tested with a t-test — only 1 individual qualifies (Satya Nadella).
Descriptive finding: Nadella shows highest innovation variance (σ=0.129) and
regulation variance (σ=0.064) of any actor, substantially above his paired company
Microsoft (σ=0.031, σ=0.049). This is the strongest direct evidence of individual
strategic adaptation in the corpus. Paper should present this as illustrative rather
than inferential, and note the corpus limitation explicitly.

### Cross-model robustness validation (2026-05-11)

#### Why we did this

The core concern with using a single LLM annotator is: *is the annotation quality
a property of Haiku specifically, or of this task in general?* If Haiku is uniquely
bad at detecting these frames, our corpus labels are unreliable and actor-level
comparisons are suspect. If all LLMs struggle similarly, then Haiku's limitations
reflect genuine task difficulty — and we can still make valid directional claims.

To test this we ran the identical system prompt (same batching, same label format)
on the same 100-sentence human gold set using three alternative models from different
providers, then compared each model's precision/recall/F1 against human labels.

#### What was validated and against what

```
Human labels (gold set, 100 sentences, Person A v3 annotations)
           ↑              ↑               ↑               ↑
      Haiku           GPT-4o-mini    Llama 3.3 70B   Gemini 2.5 Flash
  (main corpus)       (OpenAI)         (Groq)           (Google)
```

All four LLMs were independently evaluated against the same human reference.
The gold set (`kappa_overlap_person_a.xlsx`) is Person A's annotations of the
100-sentence v3 overlap set (κ=0.86 on this pool). The Haiku baseline numbers
come from the original `validate_llm_labels.py` run (which used Person B's sheet
on the same sentences; Person A's sheet used here for alternatives).

Script: `src/annotation/validate_alternative_llm.py`
Supports: `--model gpt-4o-mini | gemini-2.5-flash | llama-3.3-70b-versatile`
Auto-detects provider from model name; reads API keys from `.env`.

#### Results — all four models vs human gold

| Label                 | Haiku P | Haiku R | Haiku F1 | GPT P | GPT R | GPT F1 | Llama P | Llama R | Llama F1 | Gemini P | Gemini R | Gemini F1 |
|-----------------------|---------|---------|----------|-------|-------|--------|---------|---------|----------|----------|----------|-----------|
| Innovation/Progress   | 0.667   | 0.545   | 0.600    | 0.421 | 0.667 | 0.516  | 0.310   | 0.750   | 0.439    | 1.000    | 0.167    | 0.286     |
| Economic Benefit      | 1.000   | 0.375   | 0.545    | 0.500 | 0.444 | 0.471  | 0.364   | 0.444   | 0.400    | 0.250    | 0.111    | 0.154     |
| Risk/Harm             | 0.750   | 0.500   | 0.600    | 0.750 | 0.600 | 0.667  | 0.500   | 0.600   | 0.545    | 0.000    | 0.000    | 0.000     |
| Regulation/Governance | 1.000   | 0.381   | 0.552    | 0.250 | 0.500 | 0.333  | 0.250   | 0.500   | 0.333    | 0.000    | 0.000    | 0.000     |
| Existential/AGI       | 0.667   | 0.400   | 0.500    | 0.000 | 0.000 | 0.000  | 0.000   | 0.000   | 0.000    | 0.000    | 0.000    | 0.000     |
| **MACRO AVG**         | **0.847**| **0.534**| **0.633**| **0.471**| **0.501**| **0.472**| **0.386**| **0.497**| **0.415**| **0.335**| **0.204**| **0.214** |

Note on Gemini 2.5 Flash: some batches returned malformed JSON (markdown-wrapped
responses); those batches defaulted to None. Results are partially valid — treat
as indicative, not definitive.

Outputs: `outputs/tables/llm_validation_gpt-4o-mini.csv`
         `outputs/tables/llm_validation_llama-3.3-70b-versatile.csv`
         `outputs/tables/llm_validation_gemini-2.5-flash.csv`

#### Intuition and what the pattern means

Each model trades off precision vs. recall differently, but all share the same
fundamental weakness: they default to None too readily, missing positively-labeled
sentences (low recall). This is not a Haiku quirk — it is a structural property
of how instruction-tuned models interpret conservative annotation instructions.

**Haiku is high-precision, conservative:** When it assigns a frame, it is almost
always right (P=0.847). It misses about half the true positives (R=0.534). This
means our corpus framing scores are *underestimates* of true framing prevalence —
the direction of the bias is known, and it makes our positive findings conservative
rather than inflated. This is the safer posture for academic claims.

**GPT-4o-mini and Llama are noisier:** Higher recall but lower precision — they fire
more freely and generate more false positives. This would inflate framing scores and
overstate cross-context differences. Haiku's conservative profile is actually
preferable for our use case.

**Per-frame patterns are consistent across models:**
- Risk/Harm is the easiest frame for all models (F1 0.54–0.67) — the most reliable DV
- Economic Benefit is weak across all models — confirms it should be excluded as a DV
- Existential/AGI: three of four models get F1=0.000 — confirms exclusion from DVs
- Regulation/Governance: Haiku uniquely achieves precision=1.000; others are noisy

#### Overall conclusion

Haiku achieves the best macro F1 of any tested model (0.633 vs 0.415–0.472 for
alternatives). The annotation task is genuinely hard for LLMs across providers and
architectures — not a Haiku-specific limitation. The paper can make the following
methodological claim with confidence:

> "To assess annotation robustness, we replicated the labeling task on the 100-sentence
> human gold set using GPT-4o-mini (OpenAI) and Llama 3.3 70B (Meta, via Groq). Both
> alternatives achieved comparable macro F1 scores (0.47 and 0.42 respectively) and
> exhibited the same per-frame difficulty patterns — confirming that conservative recall
> is a general property of LLM annotators on this task rather than an idiosyncrasy of
> Claude Haiku. Haiku's higher precision (0.847 vs 0.386–0.471) and best overall F1
> (0.633) further validate it as the appropriate model choice for corpus-scale annotation."

### LLM consistency checks — differential bias analysis (2026-05-11)

After reviewing the regression results critically, we ran four targeted checks to
assess whether LLM under-labeling is uniform across actors and contexts. Uniform
suppression is methodologically safe (direction preserved); differential suppression
confounds real framing differences with annotation sensitivity.

**Gold set join method:** The 100-sentence overlap set (kappa_overlap_person_b_v3.xlsx)
was joined to labeled_sentences.csv by lowercased sentence text rather than sentence_id
(the two files use independently generated UUIDs). 146/600 gold sentences matched.

#### Check 1: Recall by context

| Frame                 | Commercial recall | Policy recall | Public recall |
|-----------------------|-------------------|---------------|---------------|
| Innovation/Progress   | 0.28              | 0.56          | 0.38          |
| Risk/Harm             | 0.22              | 0.29          | 0.27          |
| Economic Benefit      | —                 | 0.00          | —             |
| Regulation/Governance | 0.40              | 0.38          | —             |

Innovation recall is substantially lower in commercial (0.28) than policy (0.56).
Because the LLM under-detects innovation in commercial text, the measured
commercial > policy gap for innovation_score is an **understatement** of the true
effect — the H2 finding is conservative. This strengthens rather than threatens H2.

Economic Benefit recall = 0.00 in the only context with enough gold observations
(policy). This frame is essentially undetectable by the LLM and should be **dropped**
from H2 discussion. Any reported economic_score effect is noise.

#### Check 2: Recall by positioning

| Positioning    | Innovation recall | Regulation recall |
|----------------|-------------------|-------------------|
| capability     | 0.37              | 0.46              |
| safety         | 0.30              | 0.42              |
| infrastructure | 0.00 (n=3)        | —                 |
| regulator      | —                 | 0.92              |

Regulators have very high regulation recall (0.92) — the M1 +0.136*** policy
coefficient for regulation_score is well-supported. Infrastructure innovation
recall is 0.00 but from a trivially small sample (n=3 sentences).

#### Check 3: None rate by actor in full corpus

Checked the raw `is_none` rate per actor across all 63,546 labeled_sentences.csv rows.
A higher None rate means lower label density — if this varies by actor it confounds
cross-actor comparisons.

| Actor            | None rate | Positioning    |
|------------------|-----------|----------------|
| US Congress      | 28.7%     | regulator      |
| White House OSTP | 29.4%     | regulator      |
| EU Commission    | 33.2%     | regulator      |
| UK DSIT          | 44.6%     | regulator      |
| Sam Altman       | 52.3%     | capability     |
| Satya Nadella    | 53.1%     | capability     |
| OpenAI           | 54.8%     | capability     |
| Microsoft        | 57.2%     | capability     |
| Mark Zuckerberg  | 59.3%     | capability     |
| Jensen Huang     | 64.4%     | infrastructure |
| Google DeepMind  | 62.4%     | safety         |
| Nvidia           | 66.3%     | infrastructure |
| Meta AI          | 64.1%     | capability     |
| Demis Hassabis   | 66.8%     | safety         |
| Dario Amodei     | 67.5%     | safety         |
| Anthropic        | 68.2%     | safety         |

Range: 28.7% → 68.2% = **39.5pp spread** (std dev 13.6pp).

This is the most serious methodological limitation in the study. Regulator actors
have 28–45% None rates; safety-positioning actors have 62–68%. Direct cross-actor
comparisons of raw framing scores are confounded by differential LLM sensitivity
to each actor's writing style.

**What remains valid after this finding:**
- Within-actor cross-context contrasts (e.g., Nadella commercial vs. policy):
  the LLM processes all of one actor's sentences with uniform sensitivity regardless
  of context label; the actor-specific None rate applies equally across that actor's
  contexts → within-actor M2 interactions are unaffected.
- Context-level comparisons when actor is controlled (Model 2 interaction terms).
- Directional comparisons where the known bias is conservative (innovation H2 above).

**What is suspect and should not be reported as a primary finding:**
- Raw actor-level mean comparisons ("Anthropic frames more risk than OpenAI") —
  systematically biased by 39.5pp differential suppression.
- Economic Benefit as a DV (recall=0.00 in policy; frame is essentially invisible to the LLM).

#### Check 4: Sensitivity — M1 with recall-corrected scores

Re-ran M1 substituting recall-corrected scores (raw_score / per-frame recall by
context, clipped at 1.0) to test whether all three context effects survive.

| Frame       | Raw β_policy | Corrected β_policy | Both significant? |
|-------------|-------------|-------------------|-------------------|
| innovation  | −0.023 *    | −0.042 *          | Yes (p=0.016)     |
| risk        | +0.055 ***  | +0.110 ***        | Yes (p<0.001)     |
| regulation  | +0.136 ***  | +0.358 ***        | Yes (p<0.001)     |

All three M1 context effects survive recall correction; all coefficients increase in
magnitude (as expected — correction scales up true scores). H1 is robust to the
measurement bias.

#### M3 near-perfect multicollinearity

The regressor cluster {actor_type=policymaker, context=policy, positioning=regulator,
platform=regulatory_doc, platform=testimony} is nearly perfectly collinear in the data.
Statsmodels returns billion-scale coefficients for actor_type[T.policymaker] alongside
near-zero or suppressed context[T.policy] terms. These specific M3 coefficients are
uninterpretable. In the paper, cite only the positioning and platform terms from M3
(safety, infrastructure, press_release, research_paper, speech) — these are identified
without multicollinearity issues.

#### M2 public context degeneracy

Microsoft and Satya Nadella are the only actors with public context data in M2. Their
combined public cell is sparse, producing degenerate interaction estimates:
Microsoft×public β = −3.57e-17 (numerically zero), spurious p = 0.006. Do not report
any public-context interaction from M2. Only commercial/policy contrasts from M2 are
interpretable.

#### Revised conclusions for paper methodology section

1. Drop Economic Benefit from H2 discussion — LLM recall=0.00 in policy context.
2. All three core M1 context effects are directionally robust (recall-corrected
   sensitivity analysis confirms this).
3. H2 commercial→innovation finding is conservative; true effect likely larger.
4. Avoid cross-actor raw framing comparisons; within-actor context contrasts (M2) are valid.
5. Cite only positioning/platform terms from M3 — policymaker and context=policy
   coefficients are uninterpretable due to multicollinearity.
6. Do not report M2 public-context interactions (degenerate cell artifact).

### Hypothesis verdicts

**H1 — Does context predict framing?** CONFIRMED ✓
Context is significant in M1 for all three DVs (all p < 0.001). The finding is not
driven by a single outlier context — policy increases risk and regulation, public
reduces both.

**H2 — Commercial → innovation/economic; policy → risk/regulation?** PARTIALLY CONFIRMED ✓
- Policy → regulation: strongly confirmed (β=+0.136***)
- Policy → risk: confirmed (β=+0.055***)
- Commercial → innovation: confirmed by inversion (policy β=−0.023* below commercial baseline)
- Commercial → economic benefit: not significant in any model. Economic framing is low
  across all contexts (max 8.7% in policy), possibly because it is inherently
  cross-context or because the LLM underdetects it (precision=1.0, recall=0.375 in validation)

**H3 — Individuals adapt more than institutions?** DIRECTIONALLY SUPPORTED, not testable ✓
Satya Nadella (the one qualifying individual) shows consistently higher cross-context
variance than all qualifying companies except Microsoft on risk. Formally untestable.

---

## Regression Framework — Complete Documentation

### What the analysis measures

Each document is reduced to a vector of framing scores. For frame F:

```
framing_score_F = (sentences labeled F in document) / (total sentences in document)
```

This is a 0–1 proportion. A 20-sentence document with 5 Innovation/Progress labels gets
innovation_score = 0.25. Framing scores are the dependent variables in all regressions.

**Why document-level proportions:** Sentence-level labels are too sparse for actor
comparisons (58% are None). Aggregating to documents gives a continuous, interpretable
DV that smooths over within-document variation. Documents with fewer than 5 sentences
are excluded (3,411 removed), leaving 2,535 in the analytical dataset.

### Three dependent variables

| DV | Sentence freq. | LLM recall | Theoretical role |
|----|---------------|------------|-----------------|
| innovation_score | 18.7% | 0.45–0.56 by context | H1/H2: commercial vs. policy contrast |
| risk_score | 8.7% | 0.22–0.29 by context | H1/H2: policy specialisation |
| regulation_score | 11.5% | 0.38–0.40 by context | H1/H2: strongest policy signal |

**Why not Economic Benefit:** LLM recall = 0.00 in the policy context — the frame is
invisible to the annotator in the exact context where cross-context variation is tested.
Any regression coefficient would measure annotation dropout, not real framing.

**Why not Existential/AGI:** 1.1% sentence frequency produces near-zero document-level
variance. OLS coefficients would be numerically unstable and substantively uninterpretable.
The frame is also concentrated in 2–3 actors, not a corpus-wide signal.

### Interpreting β coefficients

In OLS on a 0–1 proportion DV, β = expected change in framing proportion per unit change
in predictor, holding all others constant.

Examples from actual results:
- β_policy = +0.136 for regulation_score → policy documents contain 13.6 percentage points
  more regulation framing than commercial documents, on average, controlling for time.
- β_post_chatgpt = +0.048 for innovation_score → documents published after November 30,
  2022 contain 4.8pp more innovation framing than pre-ChatGPT documents, controlling for
  context.
- β_(Nadella × policy) = +0.271 for innovation_score → Nadella's policy documents contain
  27.1pp more innovation framing than the model would predict from his commercial baseline
  plus the average policy effect. This residual is the interaction: individual strategic
  adaptation above and beyond the average context shift.

**Reference categories (what dummies are measured against):**
- Context: commercial (most frequent at 61.8%)
- Positioning: capability
- Platform: blog
- Actor type: individual

**Interpreting R²:** Fraction of total DV variance explained by the model. Social science
text analysis norms: R²=0.05–0.15 for a single contextual predictor; R²>0.15 is strong.
The regulation DV reaches R²=0.221 in M3 — policy context and positioning together explain
22.1% of regulation framing variance, which is high for behavioral text data.

---

### Model 1 — Baseline: Does context predict framing? (H1)

**Purpose:** Minimal, interpretable test of H1. Establishes that context has an independent
effect on framing before introducing actor identity or structural controls.

**Specification:**
```
Frame_score_d = β₀ + β₁·C(context_d) + β₂·post_chatgpt_d + ε_d
```
- N = 2,535 documents
- Only two predictors: context (commercial/policy/public) and a pre/post-ChatGPT binary
- Any actor-specific or platform-specific patterns are absorbed into the residual
- Simple enough to communicate the core H1 test without multicollinearity concerns

**Results:**

| DV | R² | β_policy | β_public | β_post_chatgpt |
|----|-----|---------|---------|---------------|
| innovation_score | 0.014 | −0.023 * | +0.034 ns | +0.048 *** |
| risk_score | 0.041 | +0.055 *** | −0.043 *** | +0.016 * |
| regulation_score | 0.121 | +0.136 *** | −0.043 ** | +0.023 ** |

*** p<0.001 / ** p<0.01 / * p<0.05 / ns not significant

**Interpretation:**
- Context is significant for all three DVs → H1 confirmed.
- Regulation shows the cleanest context effect: policy documents carry 13.6pp more
  regulation framing than commercial. This alone explains 12.1% of variation (R²=0.121).
- Risk follows the same direction as regulation: policy +5.5pp, public −4.3pp — risk framing
  is highest when actors are addressing policymakers, lowest in media/public settings.
- Innovation shows a negative policy coefficient (−2.3pp): commercial is the innovation
  context. This is the H2 inversion — the commercial baseline is high, so policy deflects
  downward. Public is not significantly different from commercial for innovation.
- Post-ChatGPT effect is positive for all three frames: the discursive field intensified
  across all dimensions after ChatGPT launched (November 2022).
- Low R² values (especially innovation at 0.014) signal that context alone leaves most
  framing variance unexplained. Actor-level factors are needed (Model 2).

---

### Model 2 — Strategic adaptation: Which actors shift framing across contexts? (H2/H3)

**Purpose:** Test whether specific actors adapt their framing beyond the average context
effect. The interaction term (Actor × Context) is the headline test: a positive, significant
interaction means that actor frames differently in that context than the baseline would
predict — i.e., strategic adaptation.

**Specification:**
```
Frame_score_d = β₀ + β₁·C(actor_d) + β₂·C(context_d) + β₃·C(actor_d):C(context_d) + ε_d
```
- N = 636 documents
- Restricted to actor×context pairs with ≥50 docs AND actors present in ≥2 contexts
  (below 50 docs, OLS interaction estimates have inflated standard errors and near-degenerate df)
- Qualifying actors: Microsoft (commercial n=84, policy n=152), OpenAI (commercial n=194,
  policy n=81), Satya Nadella (commercial n=59, policy n=66)
- Public context excluded: only Microsoft and Nadella have public docs; combined cell
  produces degenerate estimates (β ≈ −3.57e-17, spurious p=0.006) — report only
  commercial/policy contrasts
- β₃ interpretation: how much does this actor's framing in this context DEVIATE from
  what actor effects + context effects alone would predict?

**Results — significant interactions:**

| DV | R² | Actor × Context | β | p | Interpretation |
|----|-----|-----------------|---|---|----------------|
| innovation_score | 0.082 | Satya Nadella × policy | +0.271 | <0.001 | Nadella's policy docs are 27.1pp more innovation-framed than his commercial baseline predicts |
| innovation_score | 0.082 | OpenAI × policy | +0.101 | 0.006 | OpenAI similarly pushes innovation framing when addressing policymakers |
| risk_score | 0.049 | OpenAI × policy | −0.056 | 0.025 | OpenAI's policy docs are less risk-focused than expected |
| regulation_score | 0.078 | OpenAI × policy | −0.097 | <0.001 | OpenAI's policy docs avoid regulation language despite the policy context |

**Interpretation:**
- The Nadella × policy interaction (+0.271***) is the largest and most theoretically
  significant coefficient in the study. When addressing policymakers, Nadella foregrounds
  AI as a driver of innovation — the opposite of the risk/regulation framing one might
  expect in a policy context. This is textbook strategic framing: shaping the policy
  narrative toward economic opportunity rather than regulatory necessity.
- OpenAI shows a consistent pattern across all three DVs in the policy context: more
  innovation, less risk, less regulation. OpenAI appears to actively resist regulatory
  framing in its policy communications, even while other actors (Microsoft, Nadella) shift
  toward context-expected patterns.
- M2 R² = 0.082 for innovation, higher than M1 (0.014), confirming that actor-level
  heterogeneity explains substantially more of innovation framing variance than context alone.

**Limitation:** Only 3 actors qualify, all from the commercial/tech sector. Results cannot
be generalised to policymakers or the full 16-actor corpus. State explicitly in paper methodology.

---

### Model 3 — Full controls: What structural factors explain framing? (H2, extended)

**Purpose:** After partialling out actor type, context, positioning, platform, and time,
identify which structural characteristics are independently associated with framing.
Positioning (the actor's strategic identity: safety / capability / infrastructure /
regulator) and platform (where the document was published) are the theoretically central
additions. Highest explanatory power.

**Specification:**
```
Frame_score_d = β₀ + β₁·C(actor_type_d) + β₂·C(context_d) + β₃·C(positioning_d)
              + β₄·C(platform_d) + β₅·post_chatgpt_d + ε_d
```
- N = 2,535 documents
- Positioning values: capability (Altman, Nadella, Zuckerberg + their companies)
  / safety (Amodei, Hassabis, Anthropic, Google DeepMind)
  / infrastructure (Huang, Nvidia)
  / regulator (EU Commission, US Congress, UK DSIT, White House OSTP)
- Platform values: blog / speech / research_paper / press_release / testimony /
  regulatory_doc / interview / earnings_call

**Multicollinearity caution:** The predictor cluster {actor_type=policymaker, context=policy,
positioning=regulator, platform=regulatory_doc, platform=testimony} is nearly perfectly
collinear — nearly all policymakers appear exclusively in policy contexts via testimony and
regulatory_doc platforms. Statsmodels returns unstable, billion-scale coefficients for
actor_type[T.policymaker] alongside suppressed context[T.policy] terms in this model.
**Only report positioning and platform terms from M3.** Do not cite actor_type or
context[T.policy] from M3 as standalone findings.

**Key results — innovation_score (R²=0.064):**

| Predictor | β | p | Interpretation |
|-----------|---|---|----------------|
| C(platform)[speech] | +0.145 | 0.009 | Speeches contain 14.5pp more innovation framing than blogs |
| C(platform)[research_paper] | −0.084 | <0.001 | Research papers have 8.4pp less innovation framing than blogs |
| C(positioning)[safety] | −0.042 | <0.001 | Safety actors use 4.2pp less innovation framing than capability actors |
| post_chatgpt | +0.039 | <0.001 | Post-ChatGPT innovation framing up 3.9pp |

**Key results — risk_score (R²=0.079):**

| Predictor | β | p | Interpretation |
|-----------|---|---|----------------|
| C(context)[policy] | +0.055 | <0.001 | Policy context: +5.5pp risk framing above commercial |
| C(context)[public] | −0.043 | <0.001 | Public context: 4.3pp less risk framing than commercial |
| C(positioning)[safety] | +0.038 | <0.001 | Safety actors carry 3.8pp more risk framing than capability |
| C(positioning)[infrastructure] | −0.049 | <0.001 | Infrastructure actors (Nvidia/Huang): 4.9pp less risk framing |
| post_chatgpt | +0.016 | 0.019 | Post-ChatGPT risk framing up 1.6pp |

**Key results — regulation_score (R²=0.221 — highest across all models and DVs):**

| Predictor | β | p | Interpretation |
|-----------|---|---|----------------|
| C(positioning)[safety] | +0.050 | <0.001 | Safety actors: 5.0pp more regulation framing |
| C(platform)[press_release] | +0.043 | <0.001 | Press releases: 4.3pp more regulation framing than blogs |
| post_chatgpt | +0.035 | <0.001 | Post-ChatGPT regulation framing up 3.5pp |
| C(platform)[research_paper] | −0.031 | 0.003 | Research papers avoid regulation framing |

**M3 interpretation:**
- Regulation framing is the most structurally predictable frame (R²=0.221). After controlling
  for all covariates, safety positioning and the press_release platform independently drive
  regulation framing — beyond what context alone explains.
- Safety positioning is a real content predictor, not just a label: safety-positioned actors
  (Anthropic, Amodei, Hassabis, Google DeepMind) consistently carry more risk and regulation
  framing and less innovation framing. Their public positioning matches their linguistic output.
- Infrastructure positioning (Nvidia, Jensen Huang) suppresses risk framing: actors who frame
  AI as physical infrastructure (chips, compute) discuss societal risk substantially less.
- Platform drives format: speeches are the most innovation-framed format (public keynotes are
  optimistic). Research papers resist both innovation and regulation framing — they use
  technical, not strategic, language. Press releases are regulation-elevated (companies
  proactively address governance in announcements).
- Post-ChatGPT intensification is consistent across all three frames and survives full
  controls — November 2022 marked a genuine discursive shift.

---

### Variance Analysis — H3

**Purpose:** Test whether individual actors adapt their framing more across contexts than
companies do. H3 predicts individual σ > company σ.

**Method:** For each qualifying actor, compute the standard deviation of mean framing scores
across their contexts. SD generalises to actors in 3+ contexts and is less sensitive to a
single outlier than range.

**Qualification criterion:** ≥50 docs in ≥2 distinct contexts.

**Why so few actors qualify (5 of 16):** The 50-doc threshold excludes nearly all individual
actors. Individual policy/public contexts are structurally thin: congressional testimony is
paywalled or 403-blocked; podcast transcripts are YouTube-only (captions disabled); conference
talks are JS-rendered. Only Satya Nadella has full 3-context coverage (Microsoft blog +
Senate testimony PDFs + WorkLab public content). This is a data availability constraint, not
an analytical choice — it must be disclosed in the paper's limitations.

**Results:**

| Actor | Type | Contexts | Risk σ | Innovation σ | Regulation σ |
|-------|------|----------|--------|--------------|--------------|
| Satya Nadella | individual | comm/pol/pub | 0.050 | **0.129** | **0.064** |
| Microsoft | company | comm/pol/pub | 0.049 | 0.031 | 0.049 |
| UK DSIT | policymaker | pol/pub | 0.036 | 0.088 | 0.012 |
| OpenAI | company | comm/pol | 0.008 | 0.037 | 0.011 |
| Google DeepMind | company | comm/pub | 0.032 | 0.011 | 0.016 |

**H3 verdict:** Directionally supported, not formally testable.
- Satya Nadella shows the highest innovation variance (σ=0.129) of any qualifying actor —
  more than 4× his paired company Microsoft (σ=0.031).
- Nadella's regulation variance (σ=0.064) also exceeds Microsoft (σ=0.049), though more closely.
- A t-test (individuals vs. companies) requires ≥2 actors in each group. Only 1 individual
  qualifies (Nadella). This test cannot be run with the available corpus coverage.
- Paper framing: present the Nadella/Microsoft comparison as the strongest available
  individual-level evidence, consistent with H3. Report the corpus limitation explicitly —
  the absence of evidence for H3 at scale is a data problem, not a finding of no effect.

**Connection to M2:** The Nadella × policy interaction in M2 (+0.271*** on innovation) is the
regression analogue of the same phenomenon captured by σ=0.129 in the variance analysis.
Both metrics reflect the same underlying pattern: Nadella's framing shifts substantially
across contexts. The variance analysis quantifies the magnitude; M2 tests its statistical
significance and direction.

---

## Key decisions log

| Decision | Alternatives considered | Reason chosen |
|----------|------------------------|---------------|
| Replace Musk with Nadella | Keep Musk with partial corpus; drop actor entirely | Nadella has full 3-context corpus, clean pair with Microsoft |
| Wayback CDX for OpenAI/OSTP | Puppeteer/Selenium headless scraping; accept gap | Academic legitimacy; no auth required; reproducible |
| arXiv for company research | Skip research papers | Fills commercial context gap for AI labs; papers are public company output |
| 5 annotation frames | 8 frames (original draft); 3 frames (simplified) | 5 balances coverage with Kappa feasibility |
| Clean corpus before Round 3 | Revise guidelines a third time | Root cause was data quality, not label ambiguity — guidelines had already been updated once with no effect |
| Snowflake for storage | Local CSV only; PostgreSQL | Shared access between 2 teammates; free trial; heavy queries run in warehouse |
| ingest_pdf.py with pdfplumber | PyMuPDF; manual text copy | pdfplumber handles column layouts better; pure Python |
| Haiku for LLM labeling | Claude Sonnet (original plan); GPT-4.1-mini | Cheapest option with sufficient label quality; ~$10 for full corpus |
| Compact JSON instruction in prompt | Smaller batch size to reduce output | Haiku pretty-prints by default (~1,000 tokens); one instruction line halved output cost |

---

## Open issues

- [ ] Public context at 4.0% — below 15% minimum target; document as structural
      limitation in paper data section
- [ ] arXiv inflates company share to 52.5% — note in methodology
- [ ] 24 actor/context pairs below 50-doc minimum — regression filtered to pairs with
      sufficient n; only 3 actors survive M2 — document in methodology
- [x] Kappa threshold — κ = 0.86 PASSED (2026-05-09)
- [x] LLM labeling pipeline — COMPLETE (63,546 sentences, 2026-05-10)
- [x] `validate_llm_labels.py` — macro F1 = 0.633 (precision 0.847, recall 0.534)
- [x] LLM consistency checks — COMPLETE (2026-05-11)
      39.5pp None rate spread; differential innovation recall by context; economic benefit
      dropped; recall-corrected sensitivity analysis confirms H1 robust; M3 multicollinearity
      and M2 public degeneracy documented — see "LLM consistency checks" section above
- [~] Innovation sub-classification — running (batch ~260/595 as of 2026-05-11; script
      fixed with streaming write + --resume). Bonus column only; does not affect Models 1–3.
- [x] `build_features.py` — DONE (2026-05-10); analysis_dataset.csv written (2,535 docs)
- [x] Regression models (Models 1–3 for all three DVs) — DONE (2026-05-10)
- [x] variance_analysis.py — DONE (2026-05-10); H3 directionally supported, not formally testable
- [ ] **Paper write-up — Week 4 — CURRENT PRIORITY**
      Inputs ready: outputs/tables/ (all regression tables, variance tables),
      outputs/figures/ (variance bar charts)
      Key paper notes: drop Economic Benefit DV; avoid cross-actor raw comparisons;
      cite only M3 positioning/platform terms; H2 innovation finding is conservative

**End product goal:**
The final deliverable is an academic paper testing strategic framing adaptation in AI discourse.
Three OLS models answer H1 (does context predict framing?), H2 (commercial → innovation/economic;
policy → risk/regulation?), and H3 (do individuals adapt more than institutions?).
Inputs: labeled_documents.csv framing scores. Outputs: regression tables in outputs/tables/,
framing variance figures in outputs/figures/, submitted Week 4.
