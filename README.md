# Nigeria: law history in git

The federal law of Nigeria as a git history: one file per provision, one commit per law on the day it took effect, and the law that made each change as the commit's author. `git blame` names the law behind every paragraph; `git log` lists every change to a provision; `tools/on.py` gives the text in force on any day.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ng/`. Every version is read from a Federal Government Printer text (an Official Gazette supplement, or the Federal Ministry of Justice's print of the Constitution) with a text layer. No OCR is used.

**What is in it now**

| Folder | Act | Versions | In force from | Branch | Today's text? |
| --- | --- | ---: | --- | --- | --- |
| `data-protection/` | Nigeria Data Protection Act, 2023 (Act No. 37 of 2023) | 1 | 2023-06-12 | `main` | Yes: no amending Act found |
| `companies/` | Companies and Allied Matters Act, 2020 (Act No. 3 of 2020) | 1 | 2020-08-07 | `preview` only | No: amended by the Business Facilitation (Miscellaneous Provisions) Act, 2022, not yet applied |
| `constitution/` | Constitution of the Federal Republic of Nigeria, 1999 | 1 | 1999-05-29 | `preview` only | No: as promulgated; none of the Alteration Acts (2010, 2011, 2017-2018, 2023) is applied |

`main` holds only acts whose last version has been checked to be today's text. The other acts are on the `preview` branch until their amendments are applied.

Each folder's `README.md` lists every provision, how often it changed and when.

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What did section 37 say on 2023-06-12? | `python tools/on.py 2023-06-12 data-protection sec-037` |
| The same, with raw git (bash) | `git show $(git rev-list -1 --before="2023-06-12T23:59:59Z" main -- data-protection/sec-037.md):data-protection/sec-037.md` |
| The same, in PowerShell | `$r = git rev-list -1 --before="2023-06-12T23:59:59Z" main -- data-protection/sec-037.md; git show "$($r):data-protection/sec-037.md"` |
| Which law wrote each line? | `git blame data-protection/sec-037.md` |
| Every change, word by word | `git log -p --word-diff data-protection/sec-037.md` |
| Every law in the record, in order | `git log --reverse --format="%ad %an" --date=short main` |
| Everything one law changed | `git show law/<key>` (tags `law/<key>` mark each law's commit) |
| The whole act on a date | `python tools/on.py 2023-06-12 data-protection` |
| Which law gave a provision its wording on a date | `python tools/on.py --law 2023-06-12 data-protection sec-037` |

After a rebuild, refresh tags with `git fetch --force --tags`: a plain fetch keeps stale tags.

## Dates

- Each commit is dated at **noon, Africa/Lagos, on the day the change took effect**. The day is also in the `In-force:` trailer, which the tools read; assent and Gazette dates are trailers too.
- **An Act's day is its own commencement date**, printed under its long title in the Federal Government Printer's gazette ("[12th Day of June, 2023]"). The Constitution's day is 29 May 1999, set by section 1(2) of the Constitution of the Federal Republic of Nigeria (Promulgation) Act. No date is computed from a default rule.
- `--before="YYYY-MM-DD"` alone uses your clock's time of day, so a law that took effect that day may be missed before noon. Use `T23:59:59Z` as above, or the tool.

## How it is checked

- Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`); both must match `corpus.json`. Results are in `REPRODUCE.md`.
- **Word for word against the print:** for each act, every word of the enacted text as printed (from the enacting formula to the clerk's certificate) is in a provision file or in a Part or Chapter heading, and no word is added (`verification.json` in the build folder: `words_missing` and `words_added` are empty; the one exception is the Constitution's misprinted section number, below).
- **Against today's law:** the Data Protection Act's last version is the Act as enacted; no amending Act was found in NigeriaLII, the National Assembly's list of Acts or the Federal Ministry of Justice's library. The other two acts are not today's text, and are kept off `main`.
- The repository is rebuilt from the same data a second time and must give identical hashes.

## What "author" means

The author of a commit is the law that made the change, with an e-mail address that cannot exist, so `git blame` and `git log --author` name laws. The committer is always Lexifina.

- Each act here has one version: the act as enacted (or, for the Constitution, as promulgated), credited to its enacting law.
- Blame credits whole lines (one paragraph per line). Use `git log -p --word-diff` to see exactly which words each change made.

## What it does not show

- **Amendments not yet applied.** The Companies and Allied Matters Act, 2020 was amended by the Business Facilitation (Miscellaneous Provisions) Act, 2022 (in force February 2023); no official text of that Act with a text layer was found, so it is not applied.
- **The Constitution's alterations.** The Federal Ministry of Justice's print is titled "With the First, Second and Third Alterations", but its body is the Constitution as promulgated in 1999 (for example, section 75 still refers to "the 1991 census", which the First Alteration Act deleted); the three Alteration Acts follow it only as gazettes. They are not applied yet. Nor are the Fourth Alteration Acts (2017-2018) or the Fifth Alteration Acts (2023), for which no official text-layer source was found. There is no official consolidation of the Constitution after 2011 online.
- **Misprints are kept.** The print numbers section 281 of the Constitution "285"; it is filed as `sec-281`. Section 267 has no side note in the print, so its file has no heading. Spelling errors in the prints are kept as printed.
- **Side notes that are not headings** ("Cap. I24, LFN, 2004.", "Third Schedule.") are the printer's cross-references and are left out. Part and Chapter headings are left out; each file starts with its own number and heading.
- **Tables** in Schedules (the Constitution's list of States and Local Government Areas, the Companies Act's forms and accounts formats) are read line by line as printed, without their table layout.
- **No OCR.** Scanned texts (such as the National Assembly's copies of the Alteration Acts) are not used.

## How it is built

`tools/fetch.py` downloads each source PDF once with curl (archive copies through the shared Internet Archive client), checks that it is a whole PDF and that its sha256 matches the pin, and writes `tools/sources.json`. `tools/parse.py` reads only that cache: `tools/gazette.py` reads each printed line with its position (PyMuPDF), tells side notes from the body by position, takes each section's heading from the side note level with its first line, rebuilds paragraphs from the typesetting, and writes `corpus.json`. The shared builder `tools/build.py` turns that into the commits. `REPRODUCE.md` lists every source, command, tool version and decision, and the result of the hash-for-hash rebuild.

## Sources

| Source | What it gives | Used for |
| --- | --- | --- |
| Federal Government Printer, Official Gazette No. 119, Vol. 110, 1 July 2023 ([copy served by the Nigerian Communications Commission](https://ncc.gov.ng/media/801/view)) | Nigeria Data Protection Act, 2023, Act No. 37 | `data-protection/` |
| Federal Government Printer, Official Gazette No. 124, Vol. 107, 10 August 2020 ([Corporate Affairs Commission copy](https://pre.cac.gov.ng/assets/images/CAMA-NOTE%20FINAL-FULL-VERSION.pdf), read from the Internet Archive's capture of 1 March 2021) | Companies and Allied Matters Act, 2020, Act No. 3 | `companies/` |
| Federal Ministry of Justice, "Constitution of the Federal Republic of Nigeria, 1999 [With the First, Second and Third Alterations]" ([justice.gov.ng](https://justice.gov.ng/wp-content/uploads/2020/09/Nigerian-Constitution.pdf), read from the Internet Archive's capture of 15 October 2021) | The Promulgation Act, the Constitution as promulgated, and the gazettes of the three Alteration Acts of 2010 | `constitution/` |
| [Internet Archive](https://web.archive.org/) | Archived copies of the two files no longer served at their original address | Reading them |

Sources looked at and not used: [NigeriaLII](https://nigerialii.org) lists no legislation; the National Assembly's [Acts and Publications](https://nass.gov.ng/documents/magazine) has the 1999 Constitution only as a clipped web printout and the First and Third Alteration Acts only as scans; the unofficial [Laws of the Federation](https://lawsofnigeria.placng.org) (PLAC) copy of the 2004 revised edition is not an official text.

## Licence

See [LICENSE](LICENSE). The texts are Nigerian federal legislation as printed by the Federal Government Printer and the Federal Ministry of Justice; the copies used state no licence. This repository is private. Lexifina's arrangement, messages, tables and tools are CC0.

This repository is not legal advice. Nigeria's federal laws are published in English, so there is no separate summary in another language.
