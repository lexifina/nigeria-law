# Nigeria: law history in git


The federal law of Nigeria as a git history: one file per section, one commit per version on the day it took effect, and the law that made each change as the commit's author. `git blame` names the law behind every paragraph; `git log` lists every change to a section; picking a date gives the text in force that day.

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is Nigeria's federal law, which global-law reads at `nigeria/national/acts/`.

**What is in it now:** 7 Acts of the National Assembly as enacted, one version each, in 1,067 provisions (1,034 sections and 33 Schedules): the Nigeria Data Protection Act, 2023; the Investments and Securities Act, 2025; the Nigeria Revenue Service (Establishment) Act, 2025; the Nigeria Tax Administration Act, 2025; the Joint Revenue Board of Nigeria (Establishment) Act, 2025; the Nigeria Tax Act, 2025; and the Electoral Act, 2026. [`REPRODUCE.md`](REPRODUCE.md) lists every act with its source; each act's `README.md` lists its provisions.

Each act is a folder named after its short title, with one file per section or Schedule (`data-protection/sec-037.md` is section 37 of the Nigeria Data Protection Act, 2023, Act No. 37 of 2023). The `preview` branch also holds the Constitution of 1999 as promulgated and the Companies and Allied Matters Act, 2020 as enacted, kept off `main` because their later amendments are not applied.

The text is in English, as the Federal Government Printer prints it.

## Questions as git commands

| Question | Command |
| --- | --- |
| Every change to section 37 of the Nigeria Data Protection Act | `git log -p --word-diff -- data-protection/sec-037.md` |
| Which law wrote each line of section 37? | `git blame data-protection/sec-037.md` |
| Every version of the Act, with the day each took effect | `git log --format="%h %(trailers:key=In-force,valueonly,separator=) %an" -- data-protection ':!*/README.md'` |
| Section 37 as in force on 1 January 2024 | `python tools/on.py 2024-01-01 data-protection sec-037` |

**Outside git**, we also host this record publicly, for free:

- **[Ask Claude about Nigerian law](https://global-law.lexifina.com/v1/try_claude?country=nigeria)**: opens Claude with a first question ready.
- **[Ask ChatGPT](https://global-law.lexifina.com/v1/try_chatgpt?country=nigeria)**: the same question in ChatGPT.
- **[Search Nigerian law on our site](https://lexifina.com/law?country=nigeria&q=personal+data)**: a search for "personal data", with each provision's text and its versions, no account needed.
- **[Developer REST API](https://global-law.lexifina.com/v1/search_law?query=personal+data&jurisdiction=nigeria)**: the same search as JSON, with no key. See the [documentation here](https://lexifina.com/api/global-law).

Both assistants read the record through the free Global law connector (MCP, `https://global-law.lexifina.com/mcp`); the first time, the chat gives you the link that adds it. Ask in English.

**Host it yourself easily.** All it takes is git and Python, and the tools run on your machine:

```sh
git clone --depth 1 https://github.com/lexifina/global-law && cd global-law
python3 tools/countries.py add nigeria/national/acts
python3 tools/law.py show 2026-01-01 nigeria/national/acts/data-protection/sec-037.md
```

Opened in Claude Code, Cursor, VS Code or Codex, the clone also starts a local MCP server with the same tools ([MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md)).

## Dates

Each commit is dated at noon, Africa/Lagos, on the day the version took effect, and carries it in its `In-force:` trailer:

- for an Act, the commencement date printed under its long title in the gazette ("[12th Day of June, 2023]"); the day of assent and the gazette's date are the `Enacted:` and `Published:` trailers;
- no day is computed from a default rule: the Nigeria Tax Act, 2025, gazetted on 26 June 2025, is dated 1 January 2026, the commencement date it prints.

Each Act is credited to itself, as the gazette numbers it (`Act No. 37 of 2023 <act-2023-37@federal-government-printer.invalid>`). So are the four later commits that correct 11 section headings in four Acts (a printer's cross-reference note had been read into the heading); they change no words of the law. The committer is Lexifina.

## How it is checked

- `tools/check_repo.py` reads every version back from git on the day it took effect and on the day before, and compares it with the corpus: 7 versions of 7 acts, 0 mismatches (see [`REPRODUCE.md`](REPRODUCE.md)).
- Word for word against the print: every word of each Act's enacted text as printed is in a provision file or in a Part or Chapter heading, and no word is added.
- Against today's law: no amending Act was found for any of the seven in the National Assembly's list of Acts or the National Library of Nigeria's repository (checked 2026-11-02); acts not checked to be today's text stay off `main`.
- History is append-only: no merge commits, no commit dates that go backwards, none dated after the build, and every commit's trailers parse; a text found wrong later is corrected in a new commit, not rewritten.

## What it does not show

- **Most federal law.** Older Acts, the Laws of the Federation of Nigeria, subsidiary legislation and case law are not here.
- **Earlier texts.** Each history starts with the Act as enacted; Acts it repealed (such as the Investments and Securities Act, 2007) are not here.
- **The Constitution and the Companies and Allied Matters Act, 2020 as in force.** On `preview` they are the 1999 text as promulgated, with none of the Alteration Acts (2010 to 2023), and the 2020 Act without the Business Facilitation (Miscellaneous Provisions) Act, 2022. The Petroleum Industry Act, 2021 is held back: later Acts are reported to amend it and none is applied.
- **Part and Chapter headings and the printer's cross-reference side notes** are left out; each file starts with its section number and heading. Misprints and spelling errors are kept as printed.
- **Table layout.** Tables in Schedules are read line by line as printed, so a cell that runs over several printed lines is split across lines (the Nigeria Tax Act's Ninth and Tenth Schedules).

## Sources

| Source | Kind | Past versions | Notes |
| --- | --- | --- | --- |
| Federal Government Printer, Official Gazette of the Federal Republic of Nigeria | Official gazette: each Act as enacted | no, the text as enacted | Read from copies with a text layer (no OCR); each copy's address is in `REPRODUCE.md` and its sha256 in `data/versions.json` |
| [National Assembly](https://nass.gov.ng), Acts and Publications | Gazette copies | as published | The four revenue and tax Acts of 2025 and the Electoral Act, 2026 |
| [Securities and Exchange Commission](https://sec.gov.ng) | Gazette copy | as published | The Investments and Securities Act, 2025, which it lists as the Act in force |
| [Nigerian Communications Commission](https://ncc.gov.ng) | Gazette copy | as published | The Nigeria Data Protection Act, 2023 |

## Licence

See [`LICENSE`](LICENSE). Official texts of a legislative nature are not eligible for copyright in Nigeria (Copyright Act, 2022, section 3(b)), and each Act was read from its own printed text, not from a compilation. The history, commit messages, tables and tools are CC0 1.0.

No AI model wrote, translated or corrected legal text, and none runs at build time; the scripts that read the sources and build the history were written by an AI model (see [`REPRODUCE.md`](REPRODUCE.md)).

## More

From [lexifina/global-law](https://github.com/lexifina/global-law):

- [FEATURES.md](https://github.com/lexifina/global-law/blob/main/FEATURES.md): every feature, and what every corpus must support (`git blame`, `law.py`, the MCP tools)
- [FAQ.md](https://github.com/lexifina/global-law/blob/main/FAQ.md): questions and answers · [CONTRIBUTING.md](https://github.com/lexifina/global-law/blob/main/CONTRIBUTING.md): proposing changes · [MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md): the MCP server · [REPRODUCE.md](https://github.com/lexifina/global-law/blob/main/REPRODUCE.md): how it was built · [CHANGELOG.md](https://github.com/lexifina/global-law/blob/main/CHANGELOG.md)
- [FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md): how current each corpus is · [Monitoring](https://github.com/lexifina/global-law/tree/main/monitoring): whether updates are running · [WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md): how each official source is watched for changes
- [performance/](https://github.com/lexifina/global-law/tree/main/performance): how fast the tools are, measured
- [visualisations/](https://github.com/lexifina/global-law/tree/main/visualisations): charts and bridges across the world's law
- [Vulnerabilities](https://github.com/lexifina/global-law/tree/main/vulnerabilities): mistakes in legislation as published
