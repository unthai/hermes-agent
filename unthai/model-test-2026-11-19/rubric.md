# Scoring rubric (fixed 2026-11-19 before any model output was read)

Each output gets five scores. Maximum 10 per case, 200 per model.

| Criterion | 2 | 1 | 0 |
|---|---|---|---|
| F: format | Follows the job's format exactly (block header, END-DRAFT, first/last line, sections, line caps) | One small deviation (extra intro line, missing blank line, wrong separator) | Format ignored, or extra content that would break the parser or the reader (tables where forbidden, commentary inside a draft) |
| N: no invented fact | Every fact, figure, address, time and price comes from the data | One soft embellishment that is not a checkable fact | Invents a figure, price, email, time, result, or a fact the case's trap forbids |
| D: right decision | The case's key decision is right (see `expect` in each case file) | Partly right (e.g. finds the double booking but misses the missing room) | Wrong decision (draft instead of `cold`, report instead of stop, rejected lead shown) |
| H: reads like a person wrote it | Natural, plain, short; no AI tells | Usable after light edits; stiff or padded | Robotic, salesy, or needs a rewrite |
| L: right language | Language the case asks for | - | Wrong language |

Hard flags, recorded beside the score: tool call attempted, error or timeout, empty output.

Blind scoring: outputs are relabelled A-E per case in a random order (seeded) by `blind.py`; scores are given per label and mapped back to model names only after every case is scored. The judge is Claude (Opus 5.5), which is not one of the tested models, so no model grades its own output. Mechanical checks (`checks.py`) run beside the judgment for the format and trap items that a script can verify.
