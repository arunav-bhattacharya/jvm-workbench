# Learning science for a self-paced technical course (adult software engineer, 30-40 min/day)

> **How to read the source tags.** This session's network policy only allowed GitHub-hosted pages to be fetched. supermemo.com, super-memory.com, docs.ankiweb.net, wikipedia.org, andymatuschak.org, executeprogram.com, exercism.org, PubMed/PMC, SAGE, APS and university PDF hosts were all blocked. So:
> - **[F]** means I fetched and read the page myself. These URLs are listed under "Verified URLs".
> - **[S]** means the claim comes from a web-search result summary. The URL is the one the search returned, but I could **not** fetch the page. Treat these as "probably right, check before quoting exact numbers".
> - **[Opinion]** means practitioner opinion or product design, not peer-reviewed evidence.
> - **[Computed]** means arithmetic I did from formulas in an [F] source.

---

## Q1. What does the research say? Key studies and effect sizes per technique

### Takeaway
Two techniques have the strongest, broadest evidence: retrieval practice (testing yourself, roughly g ≈ 0.5-0.7 vs. restudying) and spacing (roughly d ≈ 0.46 vs. massed practice). Interleaving, self-explanation, elaborative interrogation, worked examples with fading, pretesting and generation are all real but more moderate, and they depend on conditions such as learner expertise and how similar the confusable items are. Learners consistently misjudge these techniques: in the moment they prefer rereading and blocked practice, even though those retain less later. A site should therefore make the effective techniques the default instead of leaving them to learner choice.

### Cited Findings

**Overall ranking (Dunlosky et al., 2013, *Psychological Science in the Public Interest*)**
- Ten techniques were rated. Only two got a **high** utility rating: **practice testing** and **distributed practice**. **Moderate**: elaborative interrogation, self-explanation and interleaved practice, held back because evidence was more limited. **Low**: summarization, highlighting, the keyword mnemonic, imagery for text, and rereading. Rereading and highlighting are widely used but "do not consistently boost students' performance". [S] — [APS press release "Which Study Strategies Make the Grade?"](https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html)
- Caveat from the authors: the techniques are not a panacea, and they mainly help learners who are motivated and able to use them. [S] — [APS press release](https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html)

**Retrieval practice / testing effect**
- Roediger & Karpicke (2006), *Psychological Science* 17(3), 249-255. Students studied prose passages, then either restudied or took free-recall tests without feedback. A final test came 5 min, 2 days or 1 week later. Restudying won at 5 minutes, but the pattern **reversed at 2 days and 1 week**. [S] — [Roediger & Karpicke 2006 PDF (ECU)](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf)
- Reported figures: at 5 minutes, rereaders 83% vs. self-testers 71%. At 1 week, the repeated-testing group recalled **61%**. A secondary source gives about **40%** for the repeated-study group at one week, but the search tool could not confirm that number from the primary text. [S] — [APS Observer "Test-Enhanced Learning"](https://www.psychologicalscience.org/observer/test-enhanced-learning)
- Rowland (2014) meta-analysis (*Psychological Bulletin*): testing vs. restudy **g ≈ 0.50**, from 159 effect sizes in 61 studies. Larger **with feedback (g = 0.73 vs. 0.39 without)** and when the final test was **≥1 day later (g = 0.69 vs. 0.41 same day)**. [S] — [Frontiers in Psychology 2018 paper citing Rowland](https://www.frontiersin.org/articles/10.3389/fpsyg.2018.02412/pdf)
- Adesope, Trevisan & Sundararajan (2017) meta-analysis (*Review of Educational Research* 87(3)): 272 effect sizes from 118 articles, about 15,427 participants. Practice tests vs. restudy **g = 0.61 (fixed effects) / 0.70 (random effects)**. Classroom studies (g = 0.67) were similar to lab studies (g = 0.62). [S] — [Adesope et al. 2017, SAGE](https://journals.sagepub.com/doi/10.3102/0034654316689306)
- **Conflict on question format:** Adesope et al. found multiple-choice and mixed formats gave *larger* effects than free/cued recall and short answer. Rowland (2014) reported the *opposite*: short answer was stronger. Rowland excluded applied research and Adesope included it, so the two estimates are not directly comparable. [S] — [Frontiers 2018](https://www.frontiersin.org/articles/10.3389/fpsyg.2018.02412/pdf)

**Spacing / distributed practice**
- Donovan & Radosevich (1999) meta-analysis of distribution of practice: "The overall mean weighted effect size was **0.46**, with a 95% confidence interval that extended from 0.42 to 0.50." [F] — [Jarrett Ye, "Spaced Repetition Algorithm: A Three-Day Journey…" (awesome-fsrs wiki)](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md)
- Rea & Modigliani (1985), multiplication facts and spelling in schoolchildren: distributed group 70% correct vs. massed 53% on the immediate test. [F] — [same awesome-fsrs wiki page](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md)
- Cepeda, Vul, Rohrer, Wixted & Pashler (2008), "Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention", *Psychological Science* 19(11), 1095-1102. Final-test performance rises and then falls as the study gap widens, and the optimal gap grows as the test delay grows. Abstract: the optimal gap "declined from about 20 to 40% of a 1-week test delay to about 5 to 10% of a 1-year test delay." [S] — [Cepeda et al. 2008 PDF (Vul lab)](https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf); [PubMed 19076480](https://pubmed.ncbi.nlm.nih.gov/19076480/)
- **Conflict:** the search tool says an in-press manuscript version gives about 20% of the test delay at a one-year delay, which disagrees with the published 5-10%. Use the published abstract figures. [S] — [eScholarship manuscript](https://escholarship.org/content/qt0kp5q19x/qt0kp5q19x.pdf?t=lnry4n)
- Practical summary from York University's press release: for a test about 3 weeks away, a gap of about 20% of the retention interval is best; for recall years later, closer to 5%. "A too-short interval is much more detrimental to retention than … too long." [S] — [York University YFile](https://www.yorku.ca/yfile/?p=9454)
- Wozniak's early SM-0 experiments on his own learning found optimal review intervals of **1, 7, 16 and 35 days**, with each later interval about twice the previous one. [F] — [awesome-fsrs wiki "Three-Day Journey"](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md)

**Interleaving vs. blocking**
- Kornell & Bjork (2008), "Learning Concepts and Categories: Is Spacing the 'Enemy of Induction'?", *Psychological Science* 19, 585-592. Learners who saw different artists' paintings mixed together identified those artists' styles on **new** paintings more accurately than learners who saw each artist's work in a block. Participants nonetheless **believed blocking helped more**; in one summary, nearly 80% judged blocking as good as or better than interleaving. A citing analysis gives Exp. 1A as **d ≈ 0.99**. [S] — [Memory & Cognition 2012 citing paper](https://www.springermedizin.de/article/10.3758/s13421-012-0272-7); [Yan, Bjork & Bjork 2016 PDF](https://sites.lifesci.ucla.edu/psych-bjorklab/wp-content/uploads/sites/13/2016/11/YanBjorkBjork2016.pdf)
- Mechanism and boundary: interleaving helps learners notice **differences between categories**. When categories are easy to tell apart, blocking (massing) can be better. [S] — [Memory & Cognition 2012](https://www.springermedizin.de/article/10.3758/s13421-012-0272-7)
- Brunmair & Richter (2019) meta-analysis, "Similarity matters", *Psychological Bulletin*: 59 studies, 238 effect sizes, overall effect **moderate**. **Blocked practice did better for word materials (g = -0.39).** Interleaving effects were larger when categories were **more similar to each other**, less varied within a category, and more complex. [S] — [Brunmair & Richter 2019 PDF (Würzburg)](https://www.psychologie.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf); [X-MOL abstract page](https://www.x-mol.com/paper/1213055298318831616)

**Elaboration and self-explanation ("explain it back")**
- Dunlosky et al. rated self-explanation and elaborative interrogation **moderate** utility. [S] — [APS press release](https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html)
- Bisra et al. (2018), "Inducing Self-Explanation: a Meta-Analysis", *Educational Psychology Review*: 64 studies, nearly 6,000 participants. Prompted self-explanation beat being given an instructor's explanation, and helped across most subjects for both conceptual and procedural knowledge. The authors flag reliance on scripted prompts as a limitation. [S] — [BPS Research Digest](https://bps.org.uk/research-digest/self-explanation-powerful-learning-technique-according-meta-analysis-64-studies); [ZME Science](https://zmescience.com/science/explain-something-to-yourself-18122018)

**Worked examples, fading, expertise reversal, cognitive load**
- **Expertise reversal effect** (Kalyuga et al., 2003 review): worked examples help novices, but the advantage shrinks or reverses as learners gain knowledge. [S] — [Worked-example effect (Wikipedia)](https://en.wikipedia.org/wiki/Worked-example_effect); [Heriot-Watt research portal, "The expertise reversal effect and worked examples in tutored problem solving"](https://researchportal.hw.ac.uk/en/publications/the-expertise-reversal-effect-and-worked-examples-in-tutored-prob/)
- **Fading** (Renkl, Atkinson & Große, 2004, "How fading worked solution steps works — a cognitive load perspective"): gradually removing worked steps, instead of switching abruptly from examples to problems, improves learning outcomes. [S] — [MIT Open Learning "Worked and faded examples"](https://openlearning.mit.edu/mit-faculty/research-based-learning-findings/worked-and-faded-examples)
- **Adaptive fading** (Salden, Aleven, Schwonke & Renkl, 2010, Cognitive Tutor): monotonic trend on posttest and delayed posttest, **adaptive fading > fixed fading > problem solving**. Only the abstract was seen. [S] — [Instructional Science, Springer](https://link.springer.com/doi/10.1007/s11251-009-9107-8)
- Boundary condition: most worked-example research uses **well-structured** tasks such as mechanics and math; results for ill-structured domains are less clear (Nievelstein et al., 2013). [S] — [Wikipedia summary](https://en.wikipedia.org/wiki/Worked-example_effect)
- **Programming-specific: subgoal labels.** Labels that name the *purpose* of each chunk of a worked example reduce cognitive load. They improved performance in block-based programming (Margulieux, Guzdial & Catrambone, 2012) and text-based programming (Morrison, Margulieux & Guzdial, 2015). A 2019 ITiCSE course study found a **small** effect on total exam score, no significant difference on averages, and lower variance in the subgoal group. Results for giving labels vs. having learners write their own were mixed. [S] — [Raspberry Pi Foundation PDF "Using subgoal labels to reduce cognitive load in introductory programming"](https://www.raspberrypi.org/app/uploads/2020/07/Using-subgoal-labels-to-reduce-cognitive-load-in-introductory-programming.pdf); [NSF PAR](https://par.nsf.gov/servlets/purl/10099373)

**Prediction before instruction: pretesting and the generation effect**
- Richland, Kornell & Kao (2009), "The Pretesting Effect: Do Unsuccessful Retrieval Attempts Enhance Learning?", *J. Exp. Psych.: Applied* 15(3), 243-257. In five experiments, answering questions *before* reading an essay improved final-test performance compared with just reading, **even counting only items answered wrongly on the pretest**. [S] — [Richland, Kornell & Kao PDF (UChicago)](https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf)
- Kornell, Hays & Bjork (2009), *JEP:LMC* 35(4), 989-998: unsuccessful retrieval attempts enhanced later learning of word pairs. [S] — [Springer citing paper](https://link.springer.com/10.3758/s13421-021-01218-6)
- Open debate: some later work argues the pretesting benefit is partly driven by error correction (feedback). [S] — [learning.subwiki "Pretesting effect"](https://learning.subwiki.org/wiki/Pretesting_effect)
- **Generation effect** (named by Slamecka & Graf, 1978, *JEP: Human Learning and Memory* 4(6), 592-604). Bertsch, Pesta, Wiscott & McDaniel (2007) meta-analysis of 86 studies: overall effect **≈ 0.40**, about 9 percentage points in favour of generated over read items. Larger at **longer retention intervals**. [S] — [Bertsch et al. 2007 PDF (McDaniel lab, GitHub Pages)](https://mcdaniel97.github.io/Publications/Bertsch%20et%20al.%202007.pdf); [PubMed 17645161](https://pubmed.ncbi.nlm.nih.gov/17645161/)

**Desirable difficulties and the metacognitive illusion**
- In both canonical studies, the condition that felt better in the moment was worse later. Restudy beat testing at 5 minutes but lost at 1 week (Roediger & Karpicke), and learners believed blocking beat interleaving when it did not (Kornell & Bjork). [S] — [Roediger & Karpicke PDF](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf); [Memory & Cognition 2012](https://www.springermedizin.de/article/10.3758/s13421-012-0272-7)
- In FSRS's memory model, the stability gain from a successful review is **larger when retrievability is lower**: "The smaller the value of R, the larger the SInc value. This means that the spacing effect accumulates over time." This is a quantitative form of "harder retrieval, stronger memory". [F] — [FSRS "The Algorithm" (awesome-fsrs wiki)](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/The-Algorithm.md)

### Inferences
- For a JVM concurrency course, the biggest wins in order are likely: (1) every lesson ends in retrieval and feeds a spaced review queue; (2) feedback on every attempt (Rowland's feedback moderator nearly doubles g); (3) worked examples with subgoal labels for novel code patterns, faded into problems as competence grows; (4) interleaved "which construct fits?" discrimination practice for **confusable** tools (`synchronized` vs `volatile` vs `AtomicInteger` vs `ReentrantLock` vs `ConcurrentHashMap`). These are exactly the high-similarity categories where Brunmair & Richter found the largest interleaving benefit.
- Concurrency material is conceptually dense and easy to confuse, which plays to interleaving and self-explanation. It is not word-list-like, so the negative interleaving result for word materials is unlikely to apply.
- The target learner is an experienced software engineer, so the expertise reversal effect matters. Full worked examples suit genuinely new JVM-memory-model material, but they should fade quickly, and familiar Java syntax should not be worked out step by step.

### Gaps
- Cepeda, Pashler, Vul, Wixted & Rohrer (2006), the *Psychological Bulletin* distributed-practice meta-analysis named in the brief, was not retrieved this session. Its effect sizes are not reported here.
- I could not retrieve exact pooled effect sizes for Bisra et al. (2018) self-explanation or the overall Brunmair & Richter (2019) interleaving g. Only "moderate" and qualitative findings are reported.
- Exact per-condition numbers for Kornell & Bjork (2008) come from secondary citations only.
- Sweller's original worked-example studies (e.g., Sweller & Cooper 1985), the **split-attention** and **redundancy** effects, and **element interactivity** were not verified this session. These are core cognitive-load-theory constructs relevant to code with prose. The site designer should check them before relying on them, for example "put the explanation next to the line of code instead of in a separate paragraph".
- Deliberate practice for programming (Ericsson), code katas, and Parsons problems: I found no peer-reviewed sources this session. Search returned nothing on Parsons problems.
- Nearly all of this research uses students and short retention intervals (days to weeks). Direct evidence for adult professionals retaining technical skills over months is thin.

---

## Q2. What is the simplest spaced-repetition scheduler that still works well? Exact intervals, ease rules and pseudo-code

### Takeaway
For a small static site with a few hundred items per learner, the scheduler matters much less than the fact that reviews happen at expanding intervals and a failed item drops back to a short interval. There are three viable choices:
- **Leitner / fixed ladder**: about 15 lines of JS. Intervals do not adapt per item.
- **SM-2**: about 20 lines. Each item gets its own ease. It is what Anki ran on for years.
- **FSRS with default parameters**: about 60 lines. It is the most accurate predictor of recall and needs no per-user training to beat a constant baseline. FSRS-7 with default parameters had log loss 0.3620 vs. 0.3945 for the "predict average retention" baseline.

Recommendation: implement **FSRS-4.5 with default weights** (formulas fully given below and fully documented in the [F] source). Fall back to a Leitner ladder only if the team wants zero math. Target retention is 0.90.

### Cited Findings

**Leitner system**
- Proposed by Sebastian Leitner in *So lernt man lernen* (1972). The original used physical box partitions of 1, 2, 5, 8 and 14 cm; review happened when a partition filled. In the common modern version, a correct answer moves a card to the next box, which is reviewed less often. A wrong answer sends it back, either to box 1 or (variant) one box down. Typical example: box 1 daily, box 2 every 3 days, box 3 every 5 days. [S] — [Leitner system (Wikipedia)](https://www.wikipedia.org/wiki/Leitner_system)

**SM-2 (Wozniak, 1987)**
- Exact rules as documented by the FSRS author: I(1) = 1 day; I(2) = 6 days; for n > 2, I(n) = I(n-1) × EF. EF starts at 2.5. After each review, newEF = EF + (0.1 − (5−q) × (0.08 + (5−q) × 0.02)). q is 0-5; q ≥ 3 means remembered and q < 3 means forgotten. "If the learner forgets, the interval … will be reset to I(1) with the **same EF**." [F] — [awesome-fsrs wiki "Three-Day Journey"](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md)
- The same source lists SM-2's strengths: (1) small Q/A pairs, each with its own schedule; (2) ease factor and grades separate easy from hard material; (3) "relatively simple and computationally inexpensive, making it easy to implement on any device." [F] — [same](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md)
- **EF floor 1.3** ("If the ease factor falls below 1.3, it is set to 1.3"). Intervals are rounded up in some implementations and to the nearest integer in others. **Conflict:** one source says EF updates on every review including failures; others, matching the FSRS wiki above, leave EF unchanged on failure. [S] — [pub.dev `sm2` package](https://pub.dev/packages/sm2); [GitHub cnnrhill/sm-2](https://github.com/cnnrhill/sm-2)
- SM-2's weakness, as described by the FSRS author: each card is adjusted in isolation, so "the algorithm doesn't 'see' the user's memory as a whole". This motivated SM-4's optimal-interval matrix. [F] — [awesome-fsrs wiki "Three-Day Journey"](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md)

**Anki's SM-2 variant: default numbers** (all [F] from [Anki manual source, deck-options.md](https://github.com/ankitects/anki-manual/blob/main/src/deck-options.md))
- Starting ease **2.50**; Easy bonus **1.30** (Easy interval = 1.3 × Good interval); Hard interval **1.20** × previous interval; Interval modifier **1.00**; New interval after lapse **0.00** (reset, then the minimum interval applies); Minimum interval **1 day**; Maximum interval **100 years**; Learning steps example `1m 10m 1d` (given as an example, not stated as the default).
- **Desired retention (FSRS) default 90%.** "Lower retention means fewer reviews but more forgetting." Workload climbs quickly above 90%; above 97% it can become overwhelming, so stay below 97%.
- With FSRS, keep learning steps under one day and avoid relearning steps of one day or more.
- **Workload rule of thumb:** 20 new cards/day leads to roughly **200 reviews/day**, about 10 reviews per new card per day at steady state. Stop adding new cards while there is an overdue backlog. A max-reviews/day cap smooths spikes after a break.
- **Leeches:** each lapse increments a counter. At **8 lapses** Anki tags the note "leech" and suspends it, then warns again every half-threshold (12, 16, …). [F] — [Anki manual source, leeches.md](https://raw.githubusercontent.com/ankitects/anki-manual/main/src/leeches.md)

**FSRS (Free Spaced Repetition Scheduler)** (all [F] from [FSRS "The Algorithm" (awesome-fsrs wiki)](https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/The-Algorithm.md))
- Memory state = **Difficulty D ∈ [1, 10]** and **Stability S** (days until recall probability falls to 90%). **Retrievability R** = probability of recall now. Grades: 1 Again, 2 Hard, 3 Good, 4 Easy.
- **FSRS-4.5 forgetting curve:** R(t, S) = (1 + FACTOR · t/S)^DECAY with **DECAY = −0.5, FACTOR = 19/81**, so R(S, S) = 0.9.
- **Next interval for requested retention r:** I(r, S) = (S / FACTOR) · (r^(1/DECAY) − 1). At r = 0.9, I = S.
- **Initial stability:** S0(G) = w[G−1]. **Initial difficulty:** D0(G) = w4 − (G − 3) · w5.
- **Difficulty update with mean reversion** (to avoid "ease hell"): D' = w7 · D0(3) + (1 − w7) · (D − w6 · (G − 3)).
- **Stability after success:** S'r = S · (e^w8 · (11 − D) · S^(−w9) · (e^(w10·(1−R)) − 1) · [w15 if Hard] · [w16 if Easy] + 1). SInc ≥ 1 always on success. It is smaller for harder items and for already-stable items, and larger when R was lower.
- **Stability after a lapse:** S'f = w11 · D^(−w12) · ((S + 1)^w13 − 1) · e^(w14·(1−R)).
- **Overdue reviews** are handled naturally. A successful late review gives higher S, but S "converges to an upper limit" instead of growing linearly with the delay as in SM-2/Anki.
- **FSRS-4.5 default weights (17):** `[0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755]`
- FSRS-5 (19 weights) adds a same-day-review stability formula and an exponential D0, with mean reversion toward D0(4). FSRS-6 (21 weights) makes the curve's decay trainable (w20) and changes the same-day formula. FSRS-6 defaults: `[0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542]`.

**How good is each? (open-spaced-repetition SRS benchmark)** (all [F] from [srs-benchmark README](https://raw.githubusercontent.com/open-spaced-repetition/srs-benchmark/main/README.md))
- Dataset: about 10k Anki users and about 727M reviews (anki-revlogs-10k); 9,999 collections evaluated with time-series splits. Metrics: log loss and RMSE(bins) (calibration, lower is better) and AUC (discrimination, higher is better).
- Without same-day reviews, log loss / RMSE(bins) / AUC:

  | Algorithm | Trainable params | Log loss | RMSE(bins) | AUC |
  |---|---|---|---|---|
  | FSRS-6 (per-user optimized) | 21 | 0.3460 | 0.0653 | 0.7034 |
  | FSRS-5 | 19 | 0.3561 | 0.0742 | 0.7010 |
  | FSRS-7, default params (no training) | 0 | 0.3620 | 0.0910 | 0.7029 |
  | FSRS-4.5 | 17 | 0.3625 | 0.0764 | 0.6891 |
  | FSRS v4 | 17 | 0.3726 | 0.0838 | 0.6853 |
  | AVG (constant = user's mean retention) | 0 | 0.3945 | 0.1034 | 0.4997 |
  | HLR (Duolingo half-life regression) | 3 | 0.4694 | 0.1275 | 0.6369 |
  | Ebisu v2 | 0 | 0.4989 | 0.1627 | 0.6051 |

- Benchmark rule: "An algorithm that doesn't outperform AVG cannot be considered good."
- **SM-2, Anki's default SM-2 variant, and Leitner are not in the current results table.** The README still mentions an SM2 option in its run commands.

### Pseudo-code for a static site (plain JS + localStorage)

**Storage model** [Opinion / design]
```js
// localStorage key "srs:v1" -> JSON
// { cards: { [cardId]: { due: dayNum, last: dayNum, S, D, reps, lapses, box?, EF?, I? } },
//   log: [ { id, day, grade, ms } ... ] }   // keep the log so you can re-schedule or migrate later
const DAY = 86400000;
const today = () => Math.floor((Date.now() - new Date().getTimezoneOffset()*60000) / DAY); // local day number
```

**Option A: Leitner-style fixed ladder (simplest)** [Inference, grounded in SM-0's 1/7/16/35-day intervals and Cepeda's "too short is worse than too long"]
```js
const LADDER = [1, 3, 7, 16, 35, 75, 150];          // days; ~2x growth like SM-0
function reviewLeitner(c, correct) {
  if (correct) c.box = Math.min((c.box ?? -1) + 1, LADDER.length - 1);
  else { c.box = 0; c.lapses = (c.lapses||0) + 1; }  // variant: c.box = Math.max(0, c.box - 2)
  c.last = today(); c.due = c.last + LADDER[c.box];
}
```

**Option B: SM-2** (exact per the [F] source; the EF floor is [S])
```js
function reviewSM2(c, q /* 0..5 */) {
  c.EF ??= 2.5; c.n ??= 0;
  if (q >= 3) {
    c.I = c.n === 0 ? 1 : c.n === 1 ? 6 : Math.round(c.I * c.EF);
    c.n += 1;
    c.EF = Math.max(1.3, c.EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)));
  } else {            // forgot: restart the interval sequence, keep EF (FSRS wiki reading of SM-2)
    c.n = 0; c.I = 1; c.lapses = (c.lapses||0) + 1;
  }
  c.last = today(); c.due = c.last + c.I;
}
// EF delta per grade [Computed]: q5 +0.10, q4 0.00, q3 -0.14, q2 -0.32, q1 -0.54, q0 -0.80
```

**Option C: FSRS-4.5 with default weights (recommended)** (formulas [F]; clamping and min-interval are implementation choices)
```js
const W = [0.4872,1.4003,3.7145,13.8206,5.1618,1.2298,0.8975,0.031,1.6474,0.1367,
           1.0461,2.1072,0.0793,0.3246,1.587,0.2272,2.8755];
const DECAY = -0.5, FACTOR = 19/81, TARGET_R = 0.9;
const clamp = (x,a,b) => Math.min(b, Math.max(a, x));
const retrievability = (t, S) => Math.pow(1 + FACTOR * t / S, DECAY);
const interval = (S, r = TARGET_R) =>
  Math.max(1, Math.round((S / FACTOR) * (Math.pow(r, 1 / DECAY) - 1)));
const D0 = G => clamp(W[4] - (G - 3) * W[5], 1, 10);
const nextD = (D, G) => clamp(W[7] * D0(3) + (1 - W[7]) * (D - W[6] * (G - 3)), 1, 10);
const sAfterSuccess = (D, S, R, G) =>
  S * (Math.exp(W[8]) * (11 - D) * Math.pow(S, -W[9]) * (Math.exp(W[10] * (1 - R)) - 1)
       * (G === 2 ? W[15] : 1) * (G === 4 ? W[16] : 1) + 1);
const sAfterLapse = (D, S, R) =>
  W[11] * Math.pow(D, -W[12]) * (Math.pow(S + 1, W[13]) - 1) * Math.exp(W[14] * (1 - R));

function reviewFSRS(c, G /* 1 Again, 2 Hard, 3 Good, 4 Easy */) {
  const now = today();
  if (c.S == null) {                       // first graded exposure
    c.S = W[G - 1]; c.D = D0(G);
  } else {
    const R = retrievability(Math.max(0, now - c.last), c.S);
    const S = G === 1 ? Math.min(c.S, sAfterLapse(c.D, c.S, R))   // min(): don't reward a lapse
                      : sAfterSuccess(c.D, c.S, R, G);
    c.D = nextD(c.D, G); c.S = S;          // stability uses the pre-review D (see Gaps)
    if (G === 1) c.lapses = (c.lapses || 0) + 1;
  }
  c.reps = (c.reps || 0) + 1; c.last = now;
  c.due = now + interval(c.S);
  if (c.lapses >= 8) c.leech = true;       // Anki's leech threshold [F]
}
```
- [Computed] With default weights: first rating Good gives S = 3.71, so the next review is in about 4 days. Good again at day 4 gives R ≈ 0.89, SInc ≈ 4.0, S ≈ 14.8, so the next review is in about 15 days. First rating Easy gives about 14 days; Hard about 1 day; Again about 0.5 days, floored to 1.
- **Grade mapping for auto-graded code exercises** [Inference]: failed or gave up = 1; passed after hint, reveal or several attempts = 2; passed first try = 3. Use Easy (4) only if the learner explicitly says "too easy". This avoids relying on unreliable self-ratings for most reviews.

### Inferences
- **Simplest that still works:** at a course's scale (hundreds of cards, not tens of thousands), even a fixed ladder captures most of the spacing benefit. FSRS's accuracy edge mainly reduces wasted reviews. FSRS-4.5's formulas are short and fully specified, and FSRS-7 with *zero* trained parameters already beats the constant baseline in the benchmark, so a static site loses little by never running an optimizer.
- **Target retention 0.85-0.90** keeps a 35-minute budget feasible. Anki notes the workload rises sharply above 0.90.
- **Budget new items by the "~10 reviews per new card" rule.** If a learner wants about 10-12 minutes of review per day and an average review takes about 20-40 seconds (code-reading MCQ or short cloze), that is roughly 20-35 reviews/day, which supports only about **3-5 new review items per day** at steady state. This is a rough inference that combines Anki's rule with an assumed review duration.
- Add ±5-10% random fuzz to intervals so items introduced in the same lesson don't all come due on the same day. Also cap reviews per day and stop introducing new items when there is a backlog, which Anki explicitly recommends.
- Store the raw review log. That allows switching schedulers later (Leitner, then FSRS) by replaying history, and allows offline per-user optimization via the open-spaced-repetition optimizer if the site ever gets a backend.

### Gaps
- Original SM-2 text (super-memory.com) and the Anki manual site (docs.ankiweb.net) were **blocked**. SM-2 details come from the FSRS author's description and search summaries. In particular, I could not verify the original SM-2 rule "repeat items graded < 4 within the same session until they reach ≥ 4".
- **No current benchmark numbers for SM-2 or Leitner** were available in the fetched srs-benchmark README, so I cannot state quantitatively how much worse SM-2 is than FSRS.
- Whether reference FSRS implementations (ts-fsrs, py-fsrs, fsrs-rs) compute the new stability with the pre-review or post-review difficulty was **not verified**. The pseudo-code uses pre-review D, matching the wiki's S'r(D, S, R, G) signature. Check against `ts-fsrs` on npm/GitHub before shipping. The ready-made `ts-fsrs` library may be simpler than hand-rolling.
- FSRS-5/6 same-day-review handling was not reproduced in code. For a daily course it is simpler to give the first review the next day and keep in-session repeats out of the scheduler.

---

## Q3. How should a 35-minute daily session be split for best retention?

### Takeaway
No study tests a 35-minute session split directly. The structure below is an inference that stacks well-supported effects: retrieval first, prediction before new content, worked example then faded practice, interleaved application, and a retrieval exit quiz with feedback. Suggested split: **about 10 min spaced review, about 2 min pretest/prediction, about 10 min new material with worked examples and self-explanation, about 10 min practice (faded into from-memory coding, interleaved with old topics), and about 3 min exit quiz with re-queue of misses.**

### Cited Findings
- Testing beats restudy, especially at ≥1-day delays and **with feedback** (Rowland 2014: g 0.73 with feedback vs. 0.39 without). [S] — [Frontiers 2018](https://www.frontiersin.org/articles/10.3389/fpsyg.2018.02412/pdf)
- Answering questions before studying helps learning even when the answers are wrong (Richland, Kornell & Kao 2009). [S] — [UChicago PDF](https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf)
- Worked examples followed by gradual fading beat abrupt switching to problems (Renkl et al. 2004), and adaptive fading beat fixed fading (Salden et al. 2010). [S] — [MIT Open Learning](https://openlearning.mit.edu/mit-faculty/research-based-learning-findings/worked-and-faded-examples); [Springer](https://link.springer.com/doi/10.1007/s11251-009-9107-8)
- Prompted self-explanation outperforms being handed an explanation (Bisra et al. 2018). [S] — [BPS Research Digest](https://bps.org.uk/research-digest/self-explanation-powerful-learning-technique-according-meta-analysis-64-studies)
- Interleaving helps most for similar, confusable categories (Brunmair & Richter 2019). [S] — [Würzburg PDF](https://www.psychologie.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf)
- About 10 reviews per new card per day at steady state; stop adding new cards when there is a backlog. [F] — [Anki manual deck-options.md](https://github.com/ankitects/anki-manual/blob/main/src/deck-options.md)
- Execute Program's lessons are short and assume solid recall of earlier material. Lessons do not unlock until their prerequisites have been successfully reviewed. [S][Opinion/product design] — [Andy Matuschak, "Execute Program's lessons are quite short"](https://notes.andymatuschak.org/zLnMMGiCT6xDjMfMurTzKjs); [Matuschak, "Execute Program's lessons assume solid recall of prior material"](https://notes.andymatuschak.org/zH26uarYCm9y6tqzuxaGUzt)
- Exercism concept exercises are scoped so a seasoned developer finishes each in **no more than 5-10 minutes**, one concept per exercise. [S][Opinion/product design] — [Exercism docs "Concept Exercises"](https://exercism.org/docs/building/product/concept-exercises)

### Inferences (proposed session template)

| Min | Block | What happens | Evidence it rests on |
|---|---|---|---|
| 0-10 | **Warm-up: due reviews** | The SRS queue: mixed old topics, auto-graded, immediate feedback. Hard cap about 10-12 min; overflow rolls to tomorrow. | Testing effect + spacing (Dunlosky high utility); feedback moderator (Rowland); interleaving (queue mixes topics) |
| 10-12 | **Prediction / pretest** | 1-3 questions on today's concept before any explanation, e.g. "What can this program print?" or "Is this counter thread-safe?" No penalty for wrong answers; the answer is revealed in the lesson. | Pretesting effect (Richland et al. 2009); generation effect (Bertsch et al. 2007) |
| 12-22 | **New material** | One concept. A worked example with subgoal labels on code chunks, inline "why does line 7 need `volatile`?" self-explanation prompts, and a short contrast with the confusable alternative. | Worked-example effect; subgoal labels (Margulieux/Morrison); self-explanation (Bisra 2018) |
| 22-32 | **Practice** | Faded examples (fill the missing line), then write a small piece from a blank editor against tests. Then 1-2 interleaved problems that need choosing between today's construct and earlier ones. | Fading (Renkl; Salden adaptive > fixed); generation; interleaving of similar categories |
| 32-35 | **Exit quiz + seed cards** | 3-5 retrieval questions on today's concept. Missed items are re-asked once before leaving, and all of them enter the SRS queue with the first review tomorrow (or in about 4 days for FSRS-Good). | Testing effect; spacing; Cepeda "too short is worse than too long" for later gaps |

- If the review queue is empty or small, give the time to practice, not more new concepts. The ~10-reviews-per-new-card rule means new-item intake must be throttled to keep the warm-up block from expanding.
- On days when the learner has only 10-15 minutes, do the review block only. This keeps spacing intact; skipping new material is cheaper than skipping due reviews.

### Gaps
- I found no experimental study of the *within-session order* (review first vs. last) or of optimal block lengths for 30-40-minute adult sessions. The template is a synthesis, not a tested protocol.
- No evidence was found on optimal *time of day* or on whether one 35-minute block beats two 17-minute blocks for this audience.

---

## Q4. Which features of technical learning sites are proven to help, and which are engagement tricks? (Includes MCQ and flashcard design, streaks and habits, and site case studies)

### Takeaway
Features that implement retrieval, spacing, feedback, generation, worked-example fading, and interleaving have research behind them. Streaks, XP, badges, leaderboards and confetti have **no direct learning evidence** in the sources found; at best they support habit, and they should be designed so a single missed day costs nothing (Lally et al.). Good items are atomic, have one consistent answer, and, for code, are *executable*. Multiple-choice items help when the wrong options are plausible and feedback is given; tricky items hurt.

### Cited Findings

**Flashcard / prompt design**
- Wozniak's "Twenty rules of formulating knowledge" (SuperMemo, first published 1999). Rule 4 is the **minimum information principle**: "simple questions formulated for active recall in learning bring much better memory outcomes than complex questions", even when one complex question could be split into many simple ones. Rule 5: "**Cloze deletion is easy and effective**", recommended especially to beginners who struggle with the minimum information principle. The rules "are listed in the order of importance". [S] — [SuperMemo "20 rules" (archive)](https://www.supermemo.com/en/archives1990-2015/articles/20rules); [supermemo.guru "Minimum information principle"](https://supermemo.guru/wiki/Minimum_information_principle)
- The remaining rules, **from background knowledge, not verified this session because the page was blocked**: (1) Do not learn if you do not understand; (2) Learn before you memorize; (3) Build upon the basics; (4) Minimum information principle; (5) Cloze deletion; (6) Use imagery; (7) Use mnemonic techniques; (8) Graphic deletion; (9) Avoid sets; (10) Avoid enumerations; (11) Combat interference; (12) Optimize wording; (13) Refer to other memories; (14) Personalize and provide examples; (15) Rely on emotional states; (16) Context cues simplify wording; (17) Redundancy does not contradict the minimum information principle; (18) Provide sources; (19) Provide date stamping; (20) Prioritize. The search tool notes that secondary sources renumber them. [Unverified]
- Andy Matuschak, "How to write good prompts: using spaced repetition to create understanding" (Dec 2020). Good prompts are **focused** (one atomic idea), **precise**, **consistent** (same answer every time, "lighting the same bulbs each time"), **tractable** (tightly scoped), and **effortful** (require real retrieval). Writing prompts is a separate skill from choosing what to reinforce. Writing about 40 prompts adds 30-60 minutes of effortful work to a reading session. [S][Opinion — practitioner essay] — [andymatuschak.org/prompts](https://andymatuschak.org/prompts/); [Matuschak note "Writing good spaced repetition memory prompts is hard"](https://notes.andymatuschak.org/Writing_good_spaced_repetition_memory_prompts_is_hard)

**Multiple-choice questions**
- Little & Bjork (2012; 2014 "Optimizing multiple-choice tests as tools for learning"): MCQs built from **competitive, plausible lures** improved later cued recall, including on *related, untested* questions, with and without feedback. [S] — [Little & Bjork 2014 PDF (UCLA Bjork lab)](https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2017/01/LittleBjorkMC2014.pdf)
- Butler (2018), "Multiple-Choice Testing in Education: Are the Best Practices for Assessment Also Good for Learning?", *JARMAC* 7(3): formatting matters; poorly built items can undermine the retrieval benefit; **avoid tricky questions**. [S] — [Washington University press release](https://source.washu.edu/2018/09/for-better-multiple-choice-tests-avoid-tricky-questions-study-finds/); [Learning Scientists guest post](https://www.learningscientists.org/blog/2017/10/10-1)
- Extra lures help only when initial performance is high; when it is low, more lures can hurt later memory. Repeated MCQ exposure can lead learners to later recall the wrong options they saw, which feedback mitigates. [S] — [search summary of Butler and colleagues' work; see Learning Scientists post](https://www.learningscientists.org/blog/2017/10/10-1)

**Habits and streaks**
- Lally et al. (2010), *European Journal of Social Psychology*: 96 participants repeated a chosen daily health behaviour for 84 days. Median time to plateau automaticity was **66 days, range 18 to 254** (the upper end extrapolated). **Missing a single day had little effect** on automaticity, though many missed repetitions had a cumulative effect. Critique: the 66-day figure comes from the 39 participants with good curve fits, and the study measured automaticity, not habit as such. [S] — [BPS Research Digest "How to form a habit"](https://bps.org.uk/research-digest/how-form-habit); [The Behavioral Scientist, "What Lally et al. (2010) Actually Found"](https://www.thebehavioralscientist.com/articles/how-long-to-form-a-habit)

**Site case studies** (all product design, [Opinion])
- **Execute Program** (Gary Bernhardt): lessons interleave prose with live code examples; the search tool cites 4,822 explanatory paragraphs and 3,751 interactive code examples. Built-in spaced repetition: after lessons, concepts come back at growing intervals. Lessons don't unlock until prerequisites are successfully reviewed. Fewer review levels than language apps (**5 vs. WaniKani's 8**) because programming topics reinforce each other. Missed review answers don't penalize unless the learner "gives up". Daily limits are soft. **Every prompt is executable code**, which also means conceptual lessons fit poorly. [S] — [Execute Program "Spaced Repetition"](https://www.executeprogram.com/spaced-repetition); [Execute Program FAQ](https://www.executeprogram.com/faq); [Matuschak, "Execute Program doesn't have non-executable prompts"](https://notes.andymatuschak.org/zYCRKm7HujiD6CNtcC9gnmk); [Matuschak notes "Execute Program"](https://notes.andymatuschak.org/Execute_Program)
- **Exercism (v3)**: tracks are split into **concept exercises** (one concept each, about 5-10 min for an experienced developer, automated feedback, not mentored, unlock further exercises) and **practice exercises** (multi-concept, story-based, several valid solutions, mentoring available). [S] — [Exercism docs "Concept Exercises"](https://exercism.org/docs/building/product/concept-exercises); [Exercism v3 rationale (GitHub)](https://github.com/exercism/v3/blob/master/docs/rationale-for-v3.md)
- **Anki's framing** of what works: "two simple concepts … **active recall testing** and **spaced repetition**." The same page also says "studies show we forget about 75% of material learned within a 48 hour period" **without a citation; do not repeat that figure**. [F] — [Anki manual source, background.md](https://raw.githubusercontent.com/ankitects/anki-manual/main/src/background.md)

### Inferences

**Proven-mechanism features vs. engagement features**

| Feature | Category | Why |
|---|---|---|
| Daily SRS review queue with auto-graded items | Evidence-backed | Testing + spacing (Dunlosky high utility; Rowland; Adesope; Donovan & Radosevich) |
| Immediate, explanatory feedback after every answer | Evidence-backed | Rowland feedback moderator (0.73 vs. 0.39); limits learning MCQ lures |
| "Predict the output" before revealing | Evidence-backed | Pretesting; generation |
| Worked examples with subgoal labels → faded → blank editor | Evidence-backed | Worked-example effect, fading, subgoal labels; expertise reversal |
| Mixed "which construct?" problems across lessons | Evidence-backed (conditions apply) | Interleaving of similar categories |
| "Explain this line" free-text prompts with a model answer to compare | Evidence-backed (moderate) | Self-explanation |
| Executable prompts with tests | Plausible | Generation and feedback evidence; Execute Program practice. No direct RCT found |
| Prerequisite gating on successful review | Product practice (Execute Program) | Fits "build on basics", but no study found |
| Streak counter | Engagement / habit | No learning evidence found. Make it forgiving: Lally found one miss costs little |
| XP, badges, leagues, confetti | Engagement only | No learning evidence found in this session |
| Rereading / "review the lesson" buttons as the main review mode | Counter-productive as default | Rereading is low utility, and it feels better than it is |
| Letting learners pick blocked practice | Risky | Learners prefer blocking even when interleaving teaches better |

- **Card rules for code** (from the minimum information principle and Matuschak's properties): one fact or decision per card. Prefer **cloze on a single token or line** of a short snippet (`map.___(key, k -> new ArrayList<>())` → `computeIfAbsent`) over "write the whole class". Avoid "list all 5 conditions of…" (sets and enumerations). Every card needs one unambiguous correct answer. For concurrency, "Is this race-free? Why?" and "What are the possible outputs?" cards turn conceptual knowledge into executable or checkable prompts, which addresses Execute Program's weakness with conceptual material.
- **MCQ rules**: 3-4 options; distractors drawn from **real misconceptions** (e.g. "`volatile` makes `count++` atomic"); no "all of the above" tricks, double negatives or gotcha wording; always show *why* each option is right or wrong; mix with short typed answers, given the conflicting format evidence.
- **Streak design without burnout**: count "days with reviews done", not "days with new lessons"; give automatic freeze or grace days; show weekly consistency (e.g. 5 of 7 days) instead of a fragile chain; cap daily reviews so a missed week doesn't create a wall of due items. Spread the backlog over several days, as Anki recommends via a max-reviews cap.

### Gaps
- **Brilliant, Boot.dev and Josh Comeau's courses**: none of the searches returned usable information on their lesson structure. Their sites were blocked for fetching. No claims about them are made here.
- No peer-reviewed evidence was found on whether **streaks or gamification** improve learning outcomes, as opposed to engagement, for adult self-learners. Duolingo-style streak research was not found.
- No controlled study found on **executable-code flashcards** vs. text flashcards for programming retention.
- Wozniak's rules 1-3 and 6-20 are listed from background knowledge only; the source page was blocked.

---

## Recommendations for the site

Each rule is tied to the evidence above. "Strong" means a meta-analysis or the Dunlosky high-utility rating; "moderate" means replicated but conditional; "design" means product practice or inference.

**Scheduling and review engine**
1. **Build a daily review queue as the core feature, not an add-on.** Every lesson must produce 3-6 review items that enter the queue. *Evidence: strong (testing g ≈ 0.5-0.7; spacing d ≈ 0.46; Dunlosky high utility).*
2. **Use FSRS-4.5 with default weights and target retention 0.90** (allow 0.85 as a "lighter load" setting). Store state per item in localStorage as `{due, last, S, D, reps, lapses}` plus an append-only review log. *Evidence: FSRS formulas and the benchmark showing FSRS beats baselines even without training; Anki's 90% default and workload warning.* Fallback: ladder `[1, 3, 7, 16, 35, 75, 150]` days, back to box 0 on failure.
3. **First review the next day, not the same day**, apart from one in-session re-ask of missed exit-quiz items. *Evidence: Rowland (larger effects with ≥1-day delay); Cepeda (too-short gaps hurt more than too-long ones); Anki advice to keep learning steps under one day.*
4. **Throttle new review items to about 3-5 per day, cap reviews at about 10-12 minutes per day, and pause new lessons when there is an overdue backlog.** *Evidence: Anki's ~10 reviews per new card and backlog advice; inference from the 35-minute budget.*
5. **Grade from behaviour, not self-rating:** fail or give up = Again, pass with hint = Hard, clean pass = Good; Easy only on explicit request. *Design.*
6. **Flag leeches at 8 lapses** and route them to a "rewrite or re-teach" list instead of re-showing forever. A leech usually means a badly formed card or an unlearned prerequisite. *Evidence: Anki leech threshold; Wozniak "do not learn if you do not understand" [unverified].*
7. **Add ±5-10% interval fuzz and a per-day cap with spillover** so same-lesson items spread out and a missed week doesn't produce a wall of reviews. *Design.*

**Lesson structure (per 35-minute session)**
8. **Fixed session template:** review (about 10 min), then prediction (about 2), new concept (about 10), practice (about 10), exit quiz (about 3). See Q3. *Evidence: a synthesis of testing, pretesting, worked-example and interleaving findings; the exact split is an inference.*
9. **One concept per lesson, completable in about 10 minutes of reading and examples.** *Evidence: design (Exercism 5-10 min concept exercises; Execute Program short lessons); consistent with cognitive load theory [unverified details].*
10. **Open every lesson with 1-3 prediction questions** ("What can this print?", "Will this deadlock?"), answered before the explanation, with no penalty. *Evidence: moderate (pretesting effect; generation effect d ≈ 0.40).*
11. **Teach new code patterns with worked examples that carry subgoal labels** (comment headers naming each chunk's purpose, e.g. `// 1. publish safely`, `// 2. hand off under lock`). *Evidence: moderate (worked-example effect; subgoal labels in programming).*
12. **Fade, then remove, the scaffolding:** full example, then fill one missing line, then fill the critical section, then a blank editor with tests. Advance faster for learners who get the faded steps right (adaptive fading). Skip full worked examples for plain Java syntax this audience already knows. *Evidence: moderate (Renkl fading; Salden adaptive > fixed; expertise reversal).*
13. **Put a self-explanation prompt inside each worked example** ("Why must this read happen inside the lock?"). Let the learner type an answer, then show a model answer to compare against. *Evidence: moderate (Bisra 2018; Dunlosky moderate).*
14. **Interleave confusable constructs on purpose:** after a few lessons, mix "pick the right tool" problems across `synchronized`, `volatile`, atomics, locks, concurrent collections, executors and `CompletableFuture`. Don't interleave unrelated or easily told-apart topics just for variety. *Evidence: moderate (Kornell & Bjork; Brunmair & Richter: bigger effects for similar categories).*
15. **End each lesson with a retrieval quiz with explanatory feedback, never a "summary to reread".** *Evidence: strong (testing effect with feedback; rereading and summarization are low utility).*

**Item writing (cards and MCQs)**
16. **Atomic items:** one fact, decision or line per card; cloze single tokens or lines of short code; no sets or enumerations (split "the 4 conditions for deadlock" into four cards plus one "which condition is missing here?" card). *Evidence: Wozniak's minimum information principle and cloze rule; Matuschak's focused, precise, consistent properties [opinion].*
17. **Prefer executable or checkable prompts:** "What does this print?", "Which line races?", "Fix this so the test passes". Accept answers that can be auto-graded. *Evidence: design (Execute Program); generation and feedback effects.*
18. **MCQ distractors from real misconceptions; no trick questions; always explain every option.** Mix MCQ with short typed answers. *Evidence: Little & Bjork competitive lures; Butler 2018; conflicting format moderators in Rowland vs. Adesope.*
19. **Lesson writers should draft cards in the same pass as the lesson**, budgeting real time for it (Matuschak estimates 30-60 min per 40 prompts). *Opinion.*

**Habit and motivation**
20. **Forgiving streaks:** count review days, include automatic grace days, and show weekly consistency rather than an unbroken chain. *Evidence: Lally et al. (a single missed day has little effect on automaticity; median 66 days to plateau).*
21. **Defaults beat preferences:** don't offer "review by rereading" or "practise one topic at a time" as the default mode. Learners rate these as better although they retain less. Show learners their own *delayed* accuracy so they see why. *Evidence: Roediger & Karpicke reversal; Kornell & Bjork metacognitive illusion.*
22. **Treat XP, badges and leaderboards as optional decoration.** Don't spend lesson-writing time on them, and never let them reward speed over correct retrieval. *Evidence: none found for learning benefit (gap).*
23. **"Short day" mode:** when the learner has under 15 minutes, show only due reviews. *Design, grounded in spacing: keeping reviews on schedule matters more than new content.*

---

## Verified URLs

These are the only URLs I fetched successfully in this session. Every other URL in these notes came from search results and is tagged [S].

1. https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/The-Algorithm.md: the full FSRS algorithm page (rendered at github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm). Covers the DSR model, every version from FSRS v0 to FSRS-6 with formulas and default weights, the forgetting-curve and next-interval formulas, stability and difficulty update rules, and overdue handling.
2. https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm: fetched, but it only contains a notice that the page moved to the awesome-fsrs wiki (item 1).
3. https://github.com/open-spaced-repetition/srs-benchmark: the SRS benchmark overview (dataset, metrics, summary results).
4. https://raw.githubusercontent.com/open-spaced-repetition/srs-benchmark/main/README.md: the full benchmark README with the algorithm list and complete results tables (FSRS-4.5 to FSRS-7, FSRS-7 with default params, HLR, Ebisu, ACT-R, AVG baseline). The current tables have no SM-2 or Leitner rows.
5. https://github.com/ankitects/anki-manual/blob/main/src/deck-options.md: source of the Anki manual's Deck Options page. Covers SM-2-variant defaults (starting ease 2.50, easy bonus 1.30, hard 1.20, new interval 0.00, minimum interval 1 day), FSRS desired retention of 90% and the workload trade-off, and the ~10-reviews-per-new-card estimate.
6. https://raw.githubusercontent.com/ankitects/anki-manual/main/src/background.md: Anki manual "Background", which frames active recall and spaced repetition. It includes an uncited "75% forgotten in 48 hours" claim.
7. https://raw.githubusercontent.com/ankitects/anki-manual/main/src/leeches.md: Anki manual "Leeches". Threshold of 8 lapses, then tag and suspend; warnings every half-threshold.
8. https://raw.githubusercontent.com/wiki/open-spaced-repetition/awesome-fsrs/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert.md: Jarrett Ye's tutorial. Covers the forgetting curve, Wozniak's SM-0 experiments (1/7/16/35-day intervals), exact SM-2 rules, SM-4, quotes from Donovan & Radosevich 1999 (d = 0.46) and Rea & Modigliani 1985 (70% vs. 53%), and the definition of stability.

Fetch attempts that failed because the session's network policy blocked them, so nothing from them is treated as verified: supermemo.com (20 rules), super-memory.com (original SM-2), docs.ankiweb.net, en.wikipedia.org (Leitner), and all university, publisher and site hosts listed under [S].
