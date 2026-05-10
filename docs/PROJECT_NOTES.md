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
- [ ] 24 actor/context pairs below 50-doc minimum — regression will filter to
      pairs with sufficient n; report which pairs are excluded
- [x] Kappa threshold — κ = 0.86 PASSED (2026-05-09)
- [x] LLM labeling pipeline — COMPLETE (63,546 sentences, 2026-05-10)
- [x] `validate_llm_labels.py` — macro F1 = 0.633 (precision 0.847, recall 0.534)
- [~] Innovation sub-classification — BLOCKED (needs ~$1 Anthropic credits; script fixed with streaming write + resume)
- [ ] `build_features.py` — pending sub-classification completion
- [ ] Regression models (Models 1–3 for risk_score, innovation_score, regulation_score) — pending features
- [ ] variance_analysis.py — test H3 (individuals vary more than institutions across contexts)
- [ ] Paper write-up — Week 4 goal

**End product goal:**
The final deliverable is an academic paper testing strategic framing adaptation in AI discourse.
Three OLS models answer H1 (does context predict framing?), H2 (commercial → innovation/economic;
policy → risk/regulation?), and H3 (do individuals adapt more than institutions?).
Inputs: labeled_documents.csv framing scores. Outputs: regression tables in outputs/tables/,
framing variance figures in outputs/figures/, submitted Week 4.
