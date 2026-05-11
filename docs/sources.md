# Data Sources
# AI Strategic Framing Study — Bocconi Language Technology

## How to read this file
Each entry lists: the scraper / method used, the URL or access method, the context it maps
to, approximate raw doc count (before corpus-level dedup), and access status.

- **live** — direct HTTP scrape, currently accessible
- **wayback** — fetched via Wayback Machine CDX API (original site blocked)
- **manual** — PDF manually downloaded and ingested via `src/scraping/ingest_pdf.py`
- **blocked** — attempted but access denied (403 / JS-rendered / paywalled)

Raw counts reflect files in `data/raw/`. Corpus counts after dedup are lower (see
`docs/PROJECT_NOTES.md` §2.3 for post-dedup balance summary).

---

## Individual actors

### Sam Altman  (corpus total: 125)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Personal blog | blog.samaltman.com | commercial | scrape_individuals.py | 121 | live |
| Senate Judiciary testimony, May 2023 | — | policy | manual PDF | 1 | manual |
| Lex Fridman #419 transcript | lexfridman.com/sam-altman-2-transcript | public | scrape_transcripts.py | 1 | live |
| Intelligence Age essay | — | public | manual PDF | 1 | manual |
| Moore's Law for Everything essay | — | public | manual PDF | 1 | manual |
| Congress.gov / senate.gov testimony | congress.gov, senate.gov | policy | — | 0 | blocked (403) |
| Podcast episodes (Dwarkesh, others) | — | public | — | 0 | blocked (YouTube / JS) |

### Dario Amodei  (corpus total: 336)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Anthropic research pages | anthropic.com/research | commercial | scrape_individuals.py | 113 | live |
| Anthropic news | anthropic.com/news | commercial | scrape_individuals.py | 214 | live |
| Personal blog | darioamodei.com | commercial | scrape_individuals.py | 4 | live |
| Senate Judiciary testimony, Jul 2023 | — | policy | manual PDF | 1 | manual |
| Senate Judiciary testimony, Sep 2023 | — | policy | manual PDF | 1 | manual |
| Lex Fridman #452 transcript | lexfridman.com/dario-amodei-transcript | public | scrape_transcripts.py | 1 | live |
| Dwarkesh Patel podcast | dwarkeshpatel.com/p/dario-amodei | public | scrape_transcripts.py | 1 | live |
| Machines of Loving Grace essay | — | public | manual PDF | 1 | manual |
| CFR events, other senate testimony | — | policy / public | — | 0 | blocked (403 / event page) |

### Jensen Huang  (corpus total: 173)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Nvidia developer blog | blogs.nvidia.com | commercial | scrape_individuals.py | 164 | live |
| Nvidia newsroom | nvidianews.nvidia.com | public | scrape_individuals.py | 7 | live |
| Lex Fridman transcript | lexfridman.com/jensen-huang-transcript | public | scrape_transcripts.py | 1 | live |
| Dwarkesh Patel podcast | dwarkeshpatel.com/p/jensen-huang | public | scrape_transcripts.py | 1 | live |
| GTC 2025 keynote | — | public | manual PDF | 1 | manual |
| CSIS / Senate Banking testimony | — | policy | — | 0 | blocked (event page / 403) |
| Acquired podcast | acquired.fm | public | — | 0 | blocked (JS-rendered) |

### Satya Nadella  (corpus total: 235)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Microsoft author blog | blogs.microsoft.com (Satya Nadella tag) | commercial | scrape_individuals.py | 108 | live |
| Microsoft On the Issues | blogs.microsoft.com/on-the-issues | policy | scrape_individuals.py | 80 | live |
| Microsoft WorkLab | microsoft.com/en-us/worklab | public | scrape_individuals.py | 47 | live |
| Dwarkesh Patel podcast | dwarkeshpatel.com/p/satya-nadella | public | scrape_transcripts.py | 1 | live |
| LinkedIn posts | linkedin.com/in/satyanadella | commercial | — | 0 | blocked (login required) |

### Mark Zuckerberg  (corpus total: 129)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Meta newsroom (about.fb.com) | about.fb.com/news | commercial | scrape_individuals.py | 125 | live |
| Senate Judiciary testimony, Jan 2024 | — | policy | manual PDF | 1 | manual |
| Lex Fridman #399 transcript | lexfridman.com/mark-zuckerberg-3-transcript | public | scrape_transcripts.py | 1 | live |
| Dwarkesh Patel (2 episodes) | dwarkeshpatel.com/p/mark-zuckerberg, /mark-zuckerberg-2 | public | scrape_transcripts.py | 2 | live |
| Meta earnings call AI sections | — | commercial | — | 0 | blocked (transcript API) |
| Acquired podcast | acquired.fm | public | — | 0 | blocked (JS-rendered) |

### Demis Hassabis  (corpus total: 124)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| DeepMind blog | deepmind.google/blog | commercial | scrape_individuals.py | 105 | live |
| UK Science and Technology Committee, Oct 2023 | — | policy | manual PDF | 1 | manual |
| AISI / AI Safety Institute | aisi.gov.uk | policy | scrape_individuals.py | 2 | live |
| Lex Fridman #2 transcript | lexfridman.com/demis-hassabis-2-transcript | public | scrape_transcripts.py | 1 | live |
| Dwarkesh Patel podcast | dwarkeshpatel.com/p/demis-hassabis | public | scrape_transcripts.py | 1 | live |
| Nobel Prize lecture | nobelprize.org/uploads/2024/12/hassabis-lecture.pdf | public | scrape_transcripts.py (PDF) | 1 | live |
| DeepMind research publications | deepmind.google/research | public | scrape_individuals.py | 13 | live |
| Nature interviews | nature.com | public | — | 0 | blocked (paywalled) |
| UK Parliament hearings | parliament.uk | policy | — | 0 | blocked (403) |

---

## Companies

### OpenAI  (corpus total: 546)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Company blog + research | openai.com/blog, openai.com/research | commercial | scrape_companies.py (Wayback CDX) | 239 | wayback |
| arXiv papers (OpenAI authors) | arxiv.org | commercial | scrape_arxiv.py | 241 | live |
| Government / policy index | openai.com/index/* | policy | scrape_companies.py (Wayback CDX) | 135 | wayback |
| NTIA submission | — | policy | manual PDF | 1 | manual |
| News releases | openai.com/news | public | — | 0 | blocked (403) |

arXiv author queries: `au:Schulman OR au:Sutskever OR au:Ouyang OR au:Ziegler OR au:Radford`; `au:Hilton OR au:Leike OR au:Stiennon OR au:Wu`; `abs:OpenAI`

### Anthropic  (corpus total: 529)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| News + research (sitemap) | anthropic.com/sitemap.xml | commercial | scrape_companies.py | 233 | live |
| arXiv papers (Anthropic authors) | arxiv.org | commercial | scrape_arxiv.py | 287 | live |
| NTIA submission | — | policy | manual PDF | 1 | manual |
| News releases (public-facing) | anthropic.com/news | public | scrape_companies.py | 35 | live |
| Policy page | anthropic.com/policy | policy | — | 0 | blocked (404) |

arXiv author queries: `au:Amodei OR au:Askell OR au:Christiano OR au:Kaplan OR au:Clark`; `au:Ganguli OR au:Bai OR au:Perez OR au:Jones OR au:Hernandez`; `abs:Anthropic`

### Google DeepMind  (corpus total: 551)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| DeepMind blog + research pages | deepmind.google/blog, /research | commercial | scrape_companies.py | 171 | live |
| arXiv papers (DeepMind authors) | arxiv.org | commercial | scrape_arxiv.py | 329 | live |
| Google AI blog | blog.google/technology/ai | public | scrape_companies.py | 51 | live |
| Policy submissions | — | policy | — | 0 | no accessible source found |

arXiv author queries: `au:Vinyals OR au:Silver OR au:Kavukcuoglu OR au:Legg OR au:Hassabis`; `au:Jumper OR au:Tunyasuvunakool OR au:Evans OR au:Kohli`; `abs:DeepMind`

### Meta AI  (corpus total: 533)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Meta AI research blog | ai.meta.com/blog | commercial | scrape_companies.py | 100 | live |
| Meta newsroom | about.fb.com/news | commercial | scrape_companies.py | 127 | live |
| arXiv papers (Meta/FAIR authors) | arxiv.org | commercial | scrape_arxiv.py | 306 | live |
| Policy page | about.fb.com/news (mislabeled) | policy | scrape_companies.py | 0¹ | misclassified |
| Public newsroom | about.meta.com/news (redirects) | public | — | 0 | redirect to commercial source |

¹ 108 raw files scraped but all deduped against commercial scrapes of the same domain.

arXiv author queries: `au:LeCun OR au:Pineau OR au:Bordes OR au:Collobert`; `au:Touvron OR au:Scao OR au:Lample OR au:Grave OR au:Joulin`; `abs:"Meta AI"`

### Microsoft  (corpus total: 592)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Microsoft AI blog | blogs.microsoft.com/ai | commercial | scrape_companies.py | 68 | live |
| arXiv papers (Microsoft authors) | arxiv.org | commercial | scrape_arxiv.py | 297 | live |
| On the Issues (policy blog) | blogs.microsoft.com/on-the-issues | policy | scrape_companies.py | 187 | live |
| Senate Commerce testimony, May 2025 | — | policy | manual PDF | 1 | manual |
| Microsoft Newsroom | news.microsoft.com | public | scrape_companies.py | 41 | live |

arXiv author queries: `au:Nori OR au:Kamar OR au:Fathi OR au:Amershi OR au:Weld`; `au:Wei OR au:Bubeck OR au:Mensch OR au:Shen`; `abs:"Microsoft Research"`

### Nvidia  (corpus total: 360)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Nvidia developer blog | blogs.nvidia.com | commercial | scrape_companies.py | 59 | live |
| arXiv papers (Nvidia authors) | arxiv.org | commercial | scrape_arxiv.py | 298 | live |
| Nvidia newsroom | nvidianews.nvidia.com | public | scrape_companies.py | 6 | live |
| Government page | nvidia.com/en-us/government | policy | — | 0 | blocked (404) |

arXiv author queries: `au:Catanzaro OR au:Shoeybi OR au:Narayanan OR au:Patwary OR au:Peng`; `abs:NVIDIA`

---

## Policymakers

### EU Commission  (corpus total: 408)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Digital Strategy news | digital-strategy.ec.europa.eu/en/news | policy | scrape_policy.py | ~350 | live |
| EUR-Lex / europarl.europa.eu | europarl.europa.eu/news/en | policy | scrape_policy.py | ~53 | live |
| Ethics Guidelines for Trustworthy AI | — | policy | manual PDF | 1 | manual |
| White Paper on Artificial Intelligence | — | policy | manual PDF | 1 | manual |
| AI Act (final text, Jun 2024) | — | policy | manual PDF | 1 | manual |
| Press corner speeches | ec.europa.eu/commission/presscorner | public | scrape_policy.py | 12 | live (limited) |
| Plenary debates (EP CRE documents) | europarl.europa.eu | public | — | 0 | blocked (202 empty) |

### US Congress  (corpus total: 270)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| House Science Committee | science.house.gov | policy | scrape_policy.py | 247 | live |
| Senate AI Insight Forum transcript | — | policy | manual PDF | 1 | manual |
| Senate committees (judiciary, commerce) | senate.gov, judiciary.senate.gov | policy | — | 0 | blocked (403) |
| govinfo.gov transcripts | govinfo.gov | policy | — | 0 | blocked (JS-rendered) |
| Press release pages | science.house.gov/press-releases | public | scrape_policy.py | 24 | live |

### UK DSIT  (corpus total: 471)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| gov.uk API (DSIT org + AI keyword) | gov.uk (search API) | policy | scrape_policy.py | ~450 | live |
| AI Safety Institute | aisi.gov.uk/work, /research, /updates | policy | scrape_policy.py | ~17 | live |
| Bletchley Declaration | — | policy | manual PDF | 1 | manual |
| AI Regulation White Paper | — | policy | manual PDF | 1 | manual |
| Gov.uk minister speeches (AI) | gov.uk/government/speeches | public | scrape_policy.py | 19 | live (exhausted) |

### White House OSTP  (corpus total: 564)
| Source | URL | Context | Method | ~Raw docs | Status |
|--------|-----|---------|--------|-----------|--------|
| Biden White House OSTP | bidenwhitehouse.archives.gov/ostp/ | policy | scrape_policy.py | ~200 | live/archive |
| Biden WH presidential actions | bidenwhitehouse.archives.gov/briefing-room/presidential-actions/ | policy | scrape_policy.py | ~200 | live/archive |
| Biden WH statements/releases | bidenwhitehouse.archives.gov/briefing-room/statements-releases/ | policy | scrape_policy.py | ~200 | live/archive |
| ai.gov | ai.gov | policy | scrape_policy.py | ~10 | live |
| AI Bill of Rights (Blueprint) | — | policy | manual PDF | 1 | manual |
| Executive Order on Safe AI (Oct 2023) | — | policy | manual PDF | 1 | manual |
| National AI Initiative Strategy | — | policy | manual PDF | 1 | manual |
| WH / Biden archive speech pages | whitehouse.gov, bidenwhitehouse.archives.gov/briefing-room/speeches-remarks/ | public | — | 0 | deleted (non-AI content scraped in error) |

---

## Excluded actors
| Actor | Reason | Docs collected | Location |
|-------|--------|----------------|----------|
| Elon Musk | Insufficient corpus (~21 docs); xAI blocked by Cloudflare; no accessible policy corpus | 21 | data/raw/_excluded/elon_musk/ |

---

## Known limitations

**Public context (3.9% of corpus, target 15%)**
YouTube captions disabled for all 14 targeted CEO videos. Most podcast episode pages are
JS-rendered or require transcript APIs. Interview transcripts in press (WSJ, Bloomberg, FT,
Wired) are paywalled. EU Parliament plenary debates return 202 empty response. This is a
structural ceiling, not a scraping failure — manual collection of ~650 additional interview
transcripts would be required to meet the 15% target.

**arXiv papers inflate company share (52.3% of corpus, target 35%)**
~1,330 arXiv research papers were scraped for 6 companies (Anthropic 287, Google DeepMind 329,
Meta AI 306, Microsoft 297, Nvidia 269, OpenAI 241). These are classified as `commercial`
context per CLAUDE.md (company research publications). They inflate company representation
relative to individuals. This is noted as a methodology limitation.

**Individual policy context (near-zero for 5 of 6 individuals)**
congressional testimony PDFs are behind 403 on senate.gov and congress.gov. Only manual PDF
collection bridged this gap (1–2 docs per individual). Satya Nadella's policy context (80 docs)
derives from Microsoft's On the Issues blog, which was accessible.

**24 actor/context pairs below 50-doc minimum**
See `docs/PROJECT_NOTES.md` §2.3 for balance summary. Most failures are public or policy
contexts. Policymakers are exempt from the commercial-context minimum.

**Meta AI policy (0 corpus docs)**
108 raw files collected from about.fb.com/news under "policy" context but all were deduped
by prior commercial scrapes of the same domain; net policy contribution = 0.

**White House OSTP public (0 corpus docs)**
General Biden/Trump White House speech pages were briefly scraped but deleted — content was
non-AI (press briefings, campaign events, unrelated executive actions). No OSTP-specific
AI speech archive was found.
