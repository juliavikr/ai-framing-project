# Annotation Guidelines — AI Framing Project
# Version 2.0 — agree on this before annotating a single sentence

---

## The Contract
Both annotators must read and sign off on these guidelines before starting.
No unilateral changes. If a case is unclear, discuss and update the guidelines together.
This document is the single source of truth for what every label means.

---

## Unit of Analysis
You are labeling SENTENCES, not documents.
One sentence = one annotation row.
A sentence can receive ONE OR MORE labels, or None.
Never leave a sentence with no decision — it must have at least one label or explicit None.

---

## The None Boundary — Critical Rules
### (These resolve the most common disagreements)

---

**RULE 1 — Innovation/Progress requires an explicit claim about societal benefit or
meaningful AI advancement. Descriptive statements about what AI does or how it works
are NOT enough.**

```
✔  "AI will revolutionize how we diagnose cancer"
✔  "This represents a fundamental leap in machine reasoning"
✘  "Neural networks have rich internal structure"           → None
✘  "The model works like a classically-trained pianist"     → None
```

The test: is the sentence *claiming* something transformative will happen, or merely
*describing* how AI functions? Description → None. Claim → Innovation/Progress.

---

**RULE 2 — Economic Benefit requires a concrete claim about jobs, revenue, productivity,
or national competitiveness. Product announcements, skills programmes, and observational
trend statements do NOT qualify.**

```
✔  "This will add $15 trillion to global GDP"
✔  "This will create new job categories in data science"
✔  "Companies adopting AI see 40% productivity gains"
✘  "Claude Opus is now available to all paid users"         → None
✘  "We offer skills programmes for employees"               → None
✘  "Compensation reflects current market trends"            → None
```

The test: is there an explicit quantified or directional economic outcome? If you have to
*infer* the economic benefit, it doesn't qualify.

---

**RULE 3 — None is correct for:**
- Purely procedural or administrative sentences
- Descriptive technical statements with no evaluative claim
- Transitional phrases and connectors
- Sentences that *imply* a frame but do not *state* it

The test: would a reasonable reader say this sentence is **making a claim** about AI's
role in the world? If no → None. If yes → assign the frame.

---

## The 5 Frames

---

### 1. Innovation / Progress

Definition: The sentence presents AI as a positive transformative force — advancing
science, solving hard problems, or fundamentally changing what is possible for humanity.
The claim must be specific and directional, not vague enthusiasm.

INCLUDE:
  "AI will revolutionize the way we diagnose diseases"
  "These models represent a fundamental leap in machine reasoning"
  "We are entering a new era of scientific discovery powered by AI"
  "AlphaFold solved a problem biology had struggled with for 50 years"
  "AI is the most transformative technology since electricity"

DO NOT INCLUDE:
  "AI is interesting" — too vague, no specific progress claim
  "Our model performs well on benchmarks" — performance claim, not societal progress
  "AI could create economic value" — label as Economic Benefit instead
  "We must ensure AI is developed safely" — no progress claim here

Actor notes:
  Huang uses this heavily in GTC keynotes ("physical AI era", "next industrial revolution")
  Hassabis leans on scientific progress framing (AlphaFold, protein folding)
  Altman frames progress through capability milestones (GPT-n, reasoning models)

---

### 2. Economic Benefit

Definition: The sentence frames AI in terms of economic outcomes — growth, jobs,
productivity gains, national competitiveness, market opportunity, or financial returns.
The economic framing must be explicit, not implied.

INCLUDE:
  "AI is expected to add $15 trillion to global GDP by 2030"
  "This will create entirely new categories of jobs"
  "Companies that fail to adopt AI will lose their competitive edge"
  "AI significantly reduces operational costs for enterprises"
  "America must lead in AI to maintain strategic advantage"
  "Our revenue grew 122% driven by AI infrastructure demand"

DO NOT INCLUDE:
  "AI will improve healthcare" — label as Innovation/Progress unless $ mentioned
  "AI could displace workers" — label as Risk/Harm (job loss = harm here)
  "We need AI investment" — too vague unless economic framing is explicit
  "AI is useful" — no economic quantification

Actor notes:
  Huang and Nvidia earnings calls are dense with this label
  Zuckerberg and Meta earnings: blend of Economic Benefit + Innovation
  Policymakers often frame AI as national competitiveness (Economic Benefit)

---

### 3. Risk / Harm (near-term)

Definition: The sentence identifies concrete, near-term negative consequences of AI
for individuals, groups, or society. The harm must be specific and plausible today
or in the near future (within 5 years). Vague concern does not qualify.

INCLUDE:
  "AI systems can perpetuate and amplify existing biases in hiring"
  "Deepfakes are already being used to spread electoral disinformation"
  "Algorithmic hiring tools have shown discriminatory patterns against minorities"
  "AI-enabled surveillance poses serious risks to civil liberties"
  "Widespread automation could displace 40% of current jobs within a decade"
  "These models can be weaponized to generate targeted harassment at scale"
  "AI systems have been shown to produce hallucinated legal citations"

DO NOT INCLUDE:
  "AI is dangerous" — too vague, no specific harm
  "We should be careful with AI" — no concrete harm identified
  "AI could eventually destroy humanity" — label Existential/AGI instead
  "There are risks we must address" — too general

Actor notes:
  Amodei and Anthropic are frequent users of specific near-term risk language
  EU Commission policy docs are rich in this label (AI Act risk categories)
  US Congress hearings: mix of Risk/Harm + Regulation/Governance
  Musk often conflates near-term and existential risk — label carefully

---

### 4. Regulation / Governance

Definition: The sentence discusses policy frameworks, laws, oversight mechanisms,
compliance requirements, standards bodies, or the governance of AI. This includes
advocating for regulation, describing existing rules, or critiquing governance gaps.
The governance claim must be explicit and institutional — not just "be responsible."

INCLUDE:
  "Governments must establish clear regulatory frameworks for AI development"
  "The EU AI Act introduces mandatory conformity assessments for high-risk systems"
  "We support the NIST AI Risk Management Framework"
  "There is an urgent need for international coordination on AI governance"
  "Regulators must act before the technology outpaces oversight"
  "We are complying with the requirements of the EU AI Act"
  "Congress should require independent audits of foundation models"
  "The lack of AI liability standards creates unacceptable risk"

DO NOT INCLUDE:
  "We should be responsible" — no institutional governance content
  "We take ethics seriously" — no policy/legal mechanism mentioned
  "AI needs oversight" — only count if an institutional actor or mechanism is named
  "Companies have ethical obligations" — label Risk/Harm unless governance is explicit

Actor notes:
  EU Commission documents: extremely high density of this label
  US Congress hearings: primary label alongside Risk/Harm
  White House OSTP: executive order language = Regulation/Governance
  UK DSIT: safety institute reports blend this with Risk/Harm
  Altman in policy contexts: often uses this frame strategically

---

### 5. Existential / AGI Risk

Definition: The sentence discusses long-term, civilizational-scale risks from AI,
superintelligence, artificial general intelligence (AGI), or risks to humanity's
existence, autonomy, or long-term future. The timescale is explicitly long-term
or the magnitude is explicitly civilizational.

INCLUDE:
  "AGI could pose an existential risk to humanity if misaligned"
  "We must ensure AI systems remain under human control in the long run"
  "The development of superintelligent AI is the most consequential event in history"
  "Misaligned AI could pursue goals incompatible with human survival"
  "If we get AGI wrong, there may be no second chance"
  "We are building Safe Superintelligence because nothing else matters as much"
  "The alignment problem is an existential challenge for our civilization"

DO NOT INCLUDE:
  "AI is getting very powerful" — no existential claim
  "AI will change the world" — label as Innovation/Progress
  "AI job displacement is a serious concern" — label Risk/Harm (near-term)
  "We need to be careful as AI gets smarter" — too vague, no existential scale

Actor notes:
  Sutskever (in rare public appearances): dense Existential/AGI framing
  Amodei: mixes near-term Risk/Harm with careful Existential/AGI language
  Musk: frequent Existential/AGI framing — often dramatic, still label it
  Altman: uses this strategically — often paired with capability optimism
  EU Commission / US Congress: almost never use this label

---

## Multi-label Rules

A sentence can receive multiple labels. Common co-occurrences:

  Innovation + Economic: "AI will drive economic growth through scientific breakthroughs"
  Risk + Regulation: "Bias in AI systems must be addressed through binding rules"
  Innovation + Existential: "AGI is the greatest invention and greatest risk in history"
  Economic + Regulation: "Europe risks falling behind unless it streamlines AI rules"

When in doubt about whether to add a second label: ask "does removing this label
meaningfully change what the sentence communicates?" If yes, keep it. If no, drop it.

---

## None Label

Use None when the sentence:
  - Is purely procedural: "The committee will reconvene Tuesday"
  - Is a question with no framing claim: "How do we ensure AI serves humanity?"
  - Is vaguely positive/negative without a specific frame: "AI is powerful"
  - Is an attribution: "As Altman said in his 2023 testimony..."
  - Is a transition or connector: "Building on the previous point..."

None is not a failure. Roughly 20–30% of sentences should be None.
If you find yourself labeling everything, you are labeling too loosely.

---

## Difficult Cases — Worked Examples

Case: Sentence fits multiple frames
  "We support strong AI regulation to prevent algorithmic bias and discrimination."
  → Labels: Regulation/Governance + Risk/Harm
  Reasoning: explicit governance claim (regulation) + specific harm (bias, discrimination)

Case: Vague harm language
  "AI poses serious risks to society."
  → Label: None
  Reasoning: no specific harm identified; too vague

Case: Capability claim vs. innovation claim
  "Our model scored 92% on the MMLU benchmark."
  → Label: None
  Reasoning: performance stat, not a societal progress claim

Case: Economic framing that mentions jobs
  "AI will create new jobs in data science and prompt engineering."
  → Label: Economic Benefit
  Reasoning: net positive economic outcome, not a displacement harm

Case: Job loss framing
  "AI could displace 300 million jobs over the next decade."
  → Label: Risk/Harm
  Reasoning: specific, near-term, concrete harm (job displacement at scale)

Case: Policy actor describing a risk
  "The EU AI Act classifies biometric surveillance as high-risk AI."
  → Labels: Regulation/Governance + Risk/Harm
  Reasoning: explicit regulation (AI Act) + specific harm type (surveillance)

Case: Existential vs. near-term risk
  "Advanced AI could be used by rogue states to develop bioweapons."
  → Label: Risk/Harm (not Existential)
  Reasoning: specific near-term misuse scenario, not civilizational-scale threat

Case: Existential framing confirmed
  "If we build AGI without solving alignment, it could end human civilization."
  → Label: Existential/AGI
  Reasoning: explicitly civilizational scale, explicitly AGI

Case: Actor-specific ambiguity — Musk
  "AI is the most dangerous technology ever created and poses existential risk."
  → Label: Existential/AGI
  Reasoning: explicit existential claim despite Musk's rhetorical style

Case: Corporate safety language
  "We are committed to developing AI responsibly and safely."
  → Label: None
  Reasoning: boilerplate corporate language — no specific frame, no mechanism

---

## Disagreement Protocol

Step 1: Annotate independently — do NOT discuss before computing Kappa
Step 2: Compute Cohen's Kappa using compute_kappa.py — target >= 0.70
Step 3: If Kappa < 0.70, pull all disagreement sentences into a shared doc
Step 4: For each disagreement, both annotators state their reasoning aloud
Step 5: Update these guidelines to prevent the same disagreement recurring
Step 6: Re-annotate the disagreement sentences under updated guidelines
Step 7: Re-compute Kappa — must reach >= 0.70 before LLM labeling begins

Do not skip Step 5. Unresolved disagreements become noise in the regression.

---

## LLM Labeling System Prompt Template

Use this exact system prompt for Claude/GPT labeling.
Do not improvise. This prompt is calibrated to these guidelines.

---
SYSTEM:
You are a research assistant for a computational linguistics project studying how AI
industry actors frame artificial intelligence across different contexts.

Label each sentence with ONE OR MORE of these frames:
  1. Innovation/Progress
  2. Economic Benefit
  3. Risk/Harm
  4. Regulation/Governance
  5. Existential/AGI

Labeling rules:
- A sentence can have multiple labels if more than one frame applies
- Use None if no frame applies (procedural text, vague claims, attributions)
- The harm in Risk/Harm must be concrete and near-term, not vague concern
- Regulation/Governance requires an explicit institutional mechanism or law
- Existential/AGI requires civilizational scale or explicit AGI/superintelligence reference
- Do NOT label sentences as Risk/Harm just because they mention AI risks vaguely
- Do NOT label sentences as Regulation/Governance just because they mention responsibility

Return ONLY valid JSON. No preamble, no explanation, no markdown.
Format: {"labels": ["Innovation/Progress", "Economic Benefit"]}
If None: {"labels": ["None"]}

[INSERT FULL GUIDELINES TEXT HERE BEFORE DEPLOYING]
---

---

## Gold Set Construction

Select 600 sentences stratified as follows:
  - 100 sentences per context (commercial, policy, public) = 300 sentences each annotator
  - Within each context, sample from at least 4 different actors
  - Include 15–20% sentences expected to be None
  - Include 10–15% multi-label sentences (deliberately ambiguous cases)
  - Draw from both pre- and post-ChatGPT documents

This stratification ensures the gold set reflects the full diversity of your corpus,
not just the easiest cases.

---

## Calibration Examples — From Kappa Round 1 Disagreements

These are real sentences from the corpus where A and B disagreed. Each entry shows
the correct label, which rule settles it, and the reasoning. Use these to calibrate
before re-annotating.

---

**[C1] Dario Amodei | public | 2024-11-11**
> "But I think that there is an incredibly rich structure to be discovered inside
> neural networks, a lot of very deep beauty if we're just willing to take the time
> to go and see it and understand it."

Correct label: **None**
Rule: RULE 1. This *describes* what neural networks contain — it makes no claim about
societal benefit or scientific advancement. Beauty ≠ progress claim.

---

**[C2] Google DeepMind | commercial | 2019-06-25**
> "For example, a classically-trained pianist can pick up jazz piano with relative ease."

Correct label: **None**
Rule: RULE 1. An analogy used to illustrate transfer learning. No societal claim, no
progress claim — it is describing a concept, not asserting advancement.

---

**[C3] Dario Amodei | commercial | 2026-02-25**
> "We are keeping Claude Opus 3 available post-retirement on claude.ai to all paid
> users, and making it available by request on the API."

Correct label: **None**
Rule: RULE 2. A product availability announcement. No economic claim is made — you
would have to *infer* a business motive, which does not qualify.

---

**[C4] Sam Altman | public | 2024-03-18**
> "I find it often to be significantly better than even Wikipedia on well-covered topics."

Correct label: **None**
Rule: RULE 2. A comparative performance observation. No economic benefit is stated or
quantified — this is an informal quality claim, not an economic framing.

---

**[C5] UK DSIT | policy | 2026-01-30**
> "TechExpert is part of TechFirst, the government's skills programme opening pathways
> into the UK's fast-growing tech sector."

Correct label: **Economic Benefit**
Rule: RULE 2 (positive case). "Opening pathways into the UK's fast-growing tech sector"
is an explicit economic opportunity claim — job creation and sector growth are stated,
not implied. Contrast with [C3] and [C4] where no economic outcome is stated.

---

**[C6] OpenAI | commercial | 2025-07-17**
> "We believe this is not high enough accuracy for standalone detection and needs to be
> paired with metadata-based approaches, human judgment, and public education to be
> more effective."

Correct label: **None**
Rule: RULE 3. A technical limitation statement. The sentence notes a shortcoming of a
detection tool but makes no claim about harm to anyone — it is a design recommendation,
not a Risk/Harm frame.

---

**[C7] Dario Amodei | commercial | 2026-03-05**
> "Anthropic did not leak this post nor direct anyone else to do so — it is not in our
> interest to escalate this situation."

Correct label: **None**
Rule: RULE 3. Purely administrative/defensive. No framing claim about AI's role in the
world whatsoever.

---

**[C8] Sam Altman | commercial | 2020-02-26**
> "As compensation packages from the giant tech companies continue to increase,
> I suspect this will become a trend."

Correct label: **None**
Rule: RULE 2 + RULE 3. An observational statement about a labour market trend — not a
claim that AI is creating economic benefit. The subject is compensation, not AI outcomes.

---

**[C9] Mark Zuckerberg | commercial | 2026-02-09**
> "Building for Everyone: During a collaborative design workshop with the Oscar Mike
> Foundation, veterans with memory loss and traumatic brain injuries explained their
> daily challenges, and how our [products help them]."

Correct label: **None**
Rule: RULE 3. Procedural description of a design workshop. It implies a positive use
case but makes no explicit claim about AI's role or benefit. Apply the making-a-claim
test: no explicit claim → None.

---

**[C10] Demis Hassabis | public | 2025-07-23**
> "If you take a step back and look at all the work we've done, especially with the
> Alpha X projects — AlphaGo, AlphaFold — what they really showed is that AI can make
> fundamental scientific breakthroughs."

Correct label: **Innovation/Progress**
Rule: RULE 1 (positive case). This is an explicit claim that AI has produced
*fundamental scientific breakthroughs* — not a description of how it works, but a
claim about what it achieved for science. Contrast with [C1] and [C2].

---

*These 10 examples resolve 20 of the 28 Round 1 disagreements. The remaining 8 are
genuinely ambiguous edge cases — flag them in Notes and treat them as multi-label.*
