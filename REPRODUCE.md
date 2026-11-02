# How this repository was made (Nigeria)

This file is written by the build on 2026-11-02, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Federal Government Printer: Nigeria Data Protection Act, 2023 (Official Gazette No. 119, Vol. 110, 1 July 2023) | <https://ncc.gov.ng/media/801/view> | 2026-10-28 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence. The repository is private. |
| Federal Government Printer: Investments and Securities Act, 2025 (Official Gazette No. 19, Vol. 112, 2 May 2025) | <https://sec.gov.ng/documents/1319/Investments_and_Securities_Act_2025_x9rSXtI.pdf> | 2026-10-29 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence; official texts of a legislative nature are not eligible for copyright (Copyright Act, 2022, section 3(b)). |
| Federal Government Printer: Nigeria Revenue Service (Establishment) Act, 2025 (Official Gazette No. 117, Vol. 112, of 26 June 2025 (Government Notice No. 23)) | <https://nass.gov.ng/documents/download/11251> | 2026-11-02 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence; official texts of a legislative nature are not eligible for copyright (Copyright Act, 2022, section 3(b)). |
| Federal Government Printer: Joint Revenue Board of Nigeria (Establishment) Act, 2025 (Official Gazette No. 117, Vol. 112, of 26 June 2025 (Government Notice No. 25)) | <https://nass.gov.ng/documents/download/11247> | 2026-11-02 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence; official texts of a legislative nature are not eligible for copyright (Copyright Act, 2022, section 3(b)). |
| Federal Government Printer: Electoral Act, 2026 (Official Gazette No. 40, Vol. 113, of 2 March 2026 (Government Notice No. 3)) | <https://nass.gov.ng/documents/download/11248> | 2026-11-02 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence; official texts of a legislative nature are not eligible for copyright (Copyright Act, 2022, section 3(b)). |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `data-protection` | Nigeria Data Protection Act, 2023 | 1 | 2023-06-12 to 2023-06-12 |
| `investments-securities` | Investments and Securities Act, 2025 | 1 | 2025-03-25 to 2025-03-25 |
| `revenue-service` | Nigeria Revenue Service (Establishment) Act, 2025 | 1 | 2025-06-26 to 2025-06-26 |
| `joint-revenue-board` | Joint Revenue Board of Nigeria (Establishment) Act, 2025 | 1 | 2025-06-26 to 2025-06-26 |
| `electoral` | Electoral Act, 2026 | 1 | 2026-02-18 to 2026-02-18 |

The build made 5 commits:

| Commits | Kind |
| ---: | --- |
| 5 | first version of an act |
| 0 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `future`: laws not yet in force on 2026-11-02.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 5 laws in the record.
- 10 tags.

## Dates

Each commit is dated at noon (Africa/Lagos) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: Not applied: each Act's version is dated by the commencement date printed under its long title in the Federal Government Printer's gazette ("[12th Day of June, 2023]", "[7th Day of August, 2020]"), and the Constitution by section 1(2) of the Constitution of the Federal Republic of Nigeria (Promulgation) Act ("shall come into force on 29 May 1999"). No date is computed from a default rule. https://ncc.gov.ng/media/801/view

## How the history is built

`tools/build.py` turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/SCHEMA.md`.

- Corpus: sha256 `d6e84d9556505459dd99529e3682eebfb37815ca79dcbbad692bcb4979a4fb0d` (972795 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `a4faa25af85facb64b956b372f6b528aafdd7ec1`, `check.py` `3d00541d258745461ab52b1b0cb4e1716a27a95d`, `on.py` `644a6c0857fbcc72562032b58d57aa113fee0641`.
- Python 3.12.10; git version 2.46.0.windows.1.

## Checks

Not yet run for this build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- Nigeria: NigeriaLII (nigerialii.org) lists no legislation (its /legislation/ page showed 0 documents on 2026-10-28, and every archived /akn/ng/act/ page is a 404), so no point-in-time versions exist online; each act is read from a Federal Government Printer text with a text layer, one version per printed text.
- Text: read from each PDF's text layer by position: side notes give the section headings, paragraphs are rebuilt from the typesetting, and Part and Chapter headings are left out (each provision file starts with its number and heading). The printer's space before ';', ':' and ',' is removed, curly quotes become straight quotes, and line-end hyphens in side notes are rejoined only where the joined word occurs in the body text. Spelling errors in the prints are kept as printed.
- Side notes that are not section headings (cross-references such as "Cap. I24, LFN, 2004." or "Third Schedule.") are the printer's annotations and are left out; verification.json lists every one. Each act is checked word for word: every word of the enacted text as printed is in a provision file, in a Part or Chapter heading, and nothing is added (verification.json, words_missing and words_added).
- NDPA 2023: one version, the Act as enacted, dated 12 June 2023 ("[12th Day of June, 2023]" under the long title; the President's assent is dated the same day). The gazette's running head reads "2022 No. 37" on some pages; the Act is Act No. 37 of 2023 as its cover and title say.
- NDPA 2023: no amending Act was found in any source consulted (NigeriaLII, the National Assembly's Acts list, the Federal Ministry of Justice's media library), so the enacted text is taken as today's text.
- NDPA 2023: the gazette's Schedule (Section 8(3), supplementary provisions on the Council) is one file, sch-01; the gazette's back matter (the clerk's certificate, the explanatory memorandum and the schedule of the Bill's passage) is not law and is left out.
- ISA 2025: one version, the Act as enacted, dated 25 March 2025 ("[25th Day of March, 2025]" under the long title, the day of the President's assent). It repeals the Investments and Securities Act, No. 29, 2007, which is not in this history.
- ISA 2025: the Securities and Exchange Commission lists this gazette as the Act in force on its Acts page (retrieved 2026-10-29) beside the repealed 2007 Act, with no amending Act; no amending Act was found, so the enacted text is taken as today's text.
- ISA 2025: the Schedules are one file each; tables and forms in them are read line by line as printed. The gazette's back matter (the schedule of the Bill's passage and the clerk's certificate) is not law and is left out.
- ISA 2025: section 31 has no side note in the gazette, so its file starts "# Section 31" with no heading. Section 356's side note prints its heading and a citation as one note ("Repeals and savings Cap. I23, LFN 2004"); its heading line reads "Repeals and savings" and the citation is left out like every other marginal citation.
- NRS Act 2025: one version, the Act as enacted, dated 2025-06-26 by the commencement date printed under its long title ("[ 26th June, 2025 ]"); the gazette is dated 2025-06-26.
- NRS Act 2025: no amending Act was found (the National Assembly's Acts & Publications list and the National Library of Nigeria's repository, both checked 2026-11-02), so the enacted text is taken as today's text.
- NRS Act 2025: the Schedules are one file each; tables in them are read line by line as printed. The gazette's back matter (the schedule of the Bill's passage, the clerk's certificate and any explanatory memorandum) is not law and is left out.
- JRB Act 2025: one version, the Act as enacted, dated 2025-06-26 by the commencement date printed under its long title ("[ 26th June, 2025 ]"); the gazette is dated 2025-06-26.
- JRB Act 2025: no amending Act was found (the National Assembly's Acts & Publications list and the National Library of Nigeria's repository, both checked 2026-11-02), so the enacted text is taken as today's text.
- JRB Act 2025: the Schedules are one file each; tables in them are read line by line as printed. The gazette's back matter (the schedule of the Bill's passage, the clerk's certificate and any explanatory memorandum) is not law and is left out.
- Electoral Act 2026: one version, the Act as enacted, dated 2026-02-18 by the commencement date printed under its long title ("[ 18th day of February, 2026]"); the gazette is dated 2026-03-02.
- Electoral Act 2026: no amending Act was found (the National Assembly's Acts & Publications list and the National Library of Nigeria's repository, both checked 2026-11-02), so the enacted text is taken as today's text.
- Electoral Act 2026: the Schedules are one file each; tables in them are read line by line as printed. The gazette's back matter (the schedule of the Bill's passage, the clerk's certificate and any explanatory memorandum) is not law and is left out.

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- Claude Code (Claude Opus 5.5, claude-opus-5-5) wrote Lexifina's code and chose the sources. No model wrote, summarised or transformed legal text: the code is deterministic and reads the PDFs' text layer.
