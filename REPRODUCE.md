# How this repository was made (Nigeria)

This file is written by the build on 2026-10-28, the day the source data was retrieved. Everything below is enough to rebuild this repository hash for hash.

## Sources

| Source | Address | Retrieved | Requests | Licence |
| --- | --- | --- | ---: | --- |
| Federal Government Printer: Nigeria Data Protection Act, 2023 (Official Gazette No. 119, Vol. 110, 1 July 2023) | <https://ncc.gov.ng/media/801/view> | 2026-10-28 | 1 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence. The repository is private. |
| Federal Ministry of Justice: Constitution of the Federal Republic of Nigeria, 1999 [With the First, Second and Third Alterations] | <https://justice.gov.ng/wp-content/uploads/2020/09/Nigerian-Constitution.pdf> | 2026-10-28 | 1 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence. The repository is private. |
| Federal Government Printer: Companies and Allied Matters Act, 2020 (Official Gazette No. 124, Vol. 107, 10 August 2020) | <https://pre.cac.gov.ng/assets/images/CAMA-NOTE%20FINAL-FULL-VERSION.pdf> | 2026-10-28 | 1 | Federal Republic of Nigeria legislation as printed by the Federal Government Printer; the source states no licence. The repository is private. |

Every response is cached by the sha256 of its URL, and the table above lists every source with its retrieval date. Lexifina keeps its fetch scripts privately; `tools/parse.py` reads only the cache and writes `corpus.json`, so the same cache always gives the same corpus.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `data-protection` | Nigeria Data Protection Act, 2023 | 1 | 2023-06-12 to 2023-06-12 |
| `constitution` | Constitution of the Federal Republic of Nigeria, 1999 | 1 | 1999-05-29 to 1999-05-29 |
| `companies` | Companies and Allied Matters Act, 2020 | 1 | 2020-08-07 to 2020-08-07 |

The build made 3 commits:

| Commits | Kind |
| ---: | --- |
| 3 | first version of an act |
| 0 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `future`: laws not yet in force on 2026-10-28.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 3 laws in the record.
- 6 tags.

## Dates

Each commit is dated at noon (Africa/Lagos) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: Not applied: each Act's version is dated by the commencement date printed under its long title in the Federal Government Printer's gazette ("[12th Day of June, 2023]", "[7th Day of August, 2020]"), and the Constitution by section 1(2) of the Constitution of the Federal Republic of Nigeria (Promulgation) Act ("shall come into force on 29 May 1999"). No date is computed from a default rule. https://ncc.gov.ng/media/801/view

## Commands, in order

```sh
# fill the cache from the sources listed above (network; Lexifina's fetch scripts are kept privately)
python -X utf8 tools/parse.py                  # cache -> corpus.json (no network)
python -X utf8 tools/build.py <folder> --repo <empty folder> --docs-date 2026-10-28
python -X utf8 tools/check_repo.py <repo> --corpus <folder>/corpus.json --write
python -X utf8 tools/build.py <folder> --repo <another empty folder> --docs-date 2026-10-28 --compare <repo>
```

In the main Lexifina repository these files live as follows:
- `fetch.py`, `parse.py` and `repo/`: in `scripts/nigeria-law/`.
- `build.py`, `check_repo.py` (`check.py` there) and `on.py`: in `scripts/gitlaw_common/`, with the corpus format in `SCHEMA.md`.

## Exact inputs

- `corpus.json` sha256 `417d9d1844946c8da13089fae630fd494c3bb27c63bc3e050d35c4fc2fc75736` (1766270 bytes)
- Script blob hashes (`git hash-object`):

| Script | Blob |
| --- | --- |
| build.py | `2bfc4ac9df193a7be844556d7f69cdb9d93ec3f2` |
| check.py | `cd346c7ff9996d450240e3bab52bcae03b2bc865` |
| on.py | `644a6c0857fbcc72562032b58d57aa113fee0641` |
| fetch.py | `103c938027acd3d09ebb460fa6d7cc9024a319c9` |
| parse.py | `4c4c08f1ea0e14445ffd7556219bb316a2474016` |

- Tools:
  - Python 3.14.0
  - git version 2.52.0.windows.1
  - curl 8.21.0 (Windows) libcurl/8.21.0 Schannel zlib/1.3.2 WinIDN WinLDAP

## Checks

1 versions of 1 acts read back from git on the day each took effect and on the day before: 0 mismatches. Trailers: 0 commits whose trailers git cannot parse. Health: 0 merge commits on main, 0 commit dates that go backwards, 0 commits dated after the build.

A second build gave different hashes; see verification.json.

These results are from the check run on the build before this one, from the same corpus.

## Decisions made by hand

- Nigeria: NigeriaLII (nigerialii.org) lists no legislation (its /legislation/ page showed 0 documents on 2026-10-28, and every archived /akn/ng/act/ page is a 404), so no point-in-time versions exist online; each act is read from a Federal Government Printer text with a text layer, one version per printed text.
- Text: read from each PDF's text layer by position (gazette.py): side notes give the section headings, paragraphs are rebuilt from the typesetting, and Part and Chapter headings are left out (each provision file starts with its number and heading). The printer's space before ';', ':' and ',' is removed, curly quotes become straight quotes, and line-end hyphens in side notes are rejoined only where the joined word occurs in the body text. Spelling errors in the prints are kept as printed.
- Side notes that are not section headings (cross-references such as "Cap. I24, LFN, 2004." or "Third Schedule.") are the printer's annotations and are left out; verification.json lists every one. parse.py checks each act word for word: every word of the enacted text as printed is in a provision file, in a Part or Chapter heading, and nothing is added (verification.json, words_missing and words_added).
- NDPA 2023: one version, the Act as enacted, dated 12 June 2023 ("[12th Day of June, 2023]" under the long title; the President's assent is dated the same day). The gazette's running head reads "2022 No. 37" on some pages; the Act is Act No. 37 of 2023 as its cover and title say.
- NDPA 2023: no amending Act was found in any source consulted (NigeriaLII, the National Assembly's Acts list, the Federal Ministry of Justice's media library), so the enacted text is taken as today's text.
- NDPA 2023: the gazette's Schedule (Section 8(3), supplementary provisions on the Council) is one file, sch-01; the gazette's back matter (the clerk's certificate, the explanatory memorandum and the schedule of the Bill's passage) is not law and is left out.
- Constitution: the Federal Ministry of Justice's print is titled "[With the First, Second and Third Alterations]", and its foreword says the Federal Government Printer was directed to print the Constitution as altered. Its body is not altered: it still has, for example, "the 1991 census" in section 75 (deleted by the First Alteration Act), section 66(1)(h) (deleted by the same Act), no section 254A to 254F (inserted by the Third Alteration Act) and the Sixth Schedule's tribunals of "a Chairman and four other members" (replaced by the Second Alteration Act). The three Alteration Acts follow it only as gazettes. So the body is read as the Constitution as promulgated, in force from 29 May 1999, credited to the Promulgation Act (Act No. 24 of 1999, as the print styles it).
- Constitution: not applied, so missing from this history: the First Alteration Act, 2010 (Act No. 1, "[16th July, 2010]", assent 10 January 2011, Official Gazette No. 2 of 11 January 2011), the Second Alteration Act, 2010 (Act No. 2, "[29th November, 2010]", assent 10 January 2011, Gazette No. 3 of 12 January 2011), the Third Alteration Act, 2010 (Act No. 3, "[4th Day of March, 2011]", Gazette No. 20 of 7 March 2011), all three printed in the same PDF and replayable; and the Fourth Alteration Acts (2017-2018) and Fifth Alteration Acts (2023), for which no official text-layer source was found. The last version is therefore not today's text, and this part is not verified (no PUBLISH).
- Constitution: the print numbers section 281 as "285" (sections 280, "285", 282, 283, 284 and 285 follow one another, and the Arrangement of Sections lists 281); it is filed as sec-281, and its heading line reads 281. Nothing else is renumbered. Section 267 has no side note in the print, so its file starts "# Section 267" with no heading.
- Constitution: the Promulgation Act's own text and the print's foreword and Arrangement of Sections are left out; the Preamble ("We the People ...", spaced "We the P eople" in the print and kept so), the 320 sections and the seven Schedules are in the provision files. On the Schedule pages the margin holds table cells (capital cities), item numbers and paragraph headings: each is kept as a line of the Schedule at its own height (item numbers joined to their item). The First Schedule's table of States and Local Government Areas is read row by row as printed, without its table layout.
- CAMA 2020: one version, the Act as enacted, dated 7 August 2020 ("[7th Day of August, 2020]" under the long title; the President's assent is dated the same day).
- CAMA 2020: the Business Facilitation (Miscellaneous Provisions) Act, 2022 (in force February 2023) amended the Act (among others sections 127, 142, 149 and 868, as commentators report); no Federal Government Printer text of it with a text layer was found, so it is not applied. The last version is therefore not today's text, and this part is not verified (no PUBLISH).
- CAMA 2020: the fifteen Schedules are one file each (sch-01 to sch-15); forms and tables in them are read line by line as printed, without their table layout.

## What AI did and did not do

The fetch, parse and check scripts were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above, through code that anyone can rerun.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- Claude Code (Claude Opus 5.5, claude-opus-5-5) wrote fetch.py, get.py, gazette.py and parse.py and chose the sources. No model wrote, summarised or transformed legal text: parse.py is deterministic code reading the PDFs' text layer.
