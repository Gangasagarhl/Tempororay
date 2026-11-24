# Field-to-Test Loop: SSD failure analysis, from recordings to a test script

A web application for one machine. It reads the CSV exports of a protocol-analyzer recording of the traffic between a
computer and a solid-state drive (PCI Express and NVMe), finds the errors with fixed code, and writes a test script that
replays a failure. AI agents do the drafting; a named person, the admin, approves every step. No model is trained.

**Be aware.** Every recording here is synthetic: made by the project's own generator, none from a real drive. The
application was written and tested on Linux. On 24 November 2026 it ran on Windows for the first time (the addition to build
26: the server started, and the offline test suites ran in Git Bash); some build 26 test groups use Linux-only parts of Python
and fail on Windows, as `docs/CHANGES_2026-11-24.md` section 9 records.

## What is here

| File | What it is |
|---|---|
| `field_to_test_loop_2026-11-24_build26_addition_windows_adk_etl_pcmark10.zip` + `.SHA256.txt` | **the newest code**: build 26 plus Windows ADK ETL + XML, every command under every process, I/O latency in 5 µs buckets and PCMark 10 Storage (unpacks to `13_production_app`; see "The addition to build 26" below) |
| `field_to_test_loop_2026-11-15_build26_three_rules_on_every_installation.zip` + `.SHA256.txt` | build 26 as it was (unpacks to `13_production_app`) |
| `field_to_test_loop_sample_recordings.zip` + `.SHA256.txt` | five small synthetic recordings for the tests and a first analysis (unpack **inside** `13_production_app`) |
| `document.html` | the whole system explained, with where the work stands on 15 November 2026 (build 24; build 25 adds what the README section on build 25 says) and, at the top, the addition of 24 November (Windows ADK ETL, every command, PCMark 10). Download it and open it in a browser |
| `errors.html` | the errors an analyzer export can hold, explained |
| `research.html` | research ideas that came out of the work |
| `lecroy_export_column_names.zip` + `.SHA256.txt` | the column names of the analyzer's CSV exports |

To get everything at once: the green **Code** button, then **Download ZIP**.

## On the Windows laptop

You need Python 3.10 or newer (from python.org, with "Add python.exe to PATH" ticked) and Git for Windows.

```powershell
# PowerShell, in the folder with the downloaded files
Expand-Archive .\field_to_test_loop_2026-11-24_build26_addition_windows_adk_etl_pcmark10.zip -DestinationPath C:\f2t
Expand-Archive .\field_to_test_loop_sample_recordings.zip -DestinationPath C:\f2t\13_production_app
cd C:\f2t\13_production_app
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r deploy\requirements.txt
.\.venv\Scripts\python.exe deploy\preflight.py
.\.venv\Scripts\python.exe run_app.py          # then open http://127.0.0.1:8077
```

The full instructions, with what to expect at every step, are in the code zip: `13_production_app\deploy\WINDOWS.md`.

## Sentences to give an AI coding agent

Open the agent in `C:\f2t\13_production_app` and give it these one at a time.

1. **Get to know it.**
   `Read deploy/WINDOWS.md from top to bottom, then README_FIRST.md. Follow the rules of section 2 of WINDOWS.md in everything you do. Tell me in ten lines what this application is and what has never been run on Windows. Change nothing yet.`
2. **Install and first check.**
   `Do steps 1 to 3 of section 4 of deploy/WINDOWS.md. Show me every FAIL and WARN line exactly as printed.`
3. **The tests.**
   `Do step 4 of section 4: run the offline suites in Git Bash. Sort every failure into kind A, B or C as the file says, and show me the list before you change anything. Then fix them one at a time. Never delete a test and never weaken what it checks. Keep Linux working.`
4. **By hand.**
   `Do step 5 of section 4 with me: start the application and go through the 31 checks. Do check 18 before I use the Terminal agent button.`
5. **Write it down.**
   `Write docs/WINDOWS_RESULTS.md as step 6 of section 4 describes: what ran, what failed, what you changed, what stays open.`
6. **Windows trace files (.etl).**
   `Read reference_library/windows_wpa/NOTES.md. Help me collect the eight items of its section 7 on this laptop, then tell me what is needed to write the column list.`

7. **Know what was added on 15 November.**
   `Read docs/CHANGES_2026-11-15.md, sections 0, 17, 18 and 19, then docs/CHANGES_2026-11-15_round2.md, sections 0, 0a, 15, 16 and 17, and docs/OPPORTUNITY_COVERAGE_2026-11-15.md. Tell me in fifteen lines what is new, what is only tested on synthetic data, and what must be tried once with a real model, the real opencode and a real file.`
8. **A recording of any tool (VIAVI or another), given as CSV.**
   `I exported a recording to delimited text with the tool's own export. Start an analysis on its folder (the start page no longer asks which tool made it; a folder without a CSV file says so, and the terminal agent can be asked about its files). Show me what Family 1 learned for each column and which meanings have no source. Then help me write one rule in the file's own words and take it through Family 4. Write what worked and what did not to docs/REAL_ENVIRONMENT_RESULTS.md.`
9. **Close the gaps to the project's statement (needs real captures, a drive, a bench).**
   `Read docs/OPPORTUNITY_STATEMENT.md, docs/OPPORTUNITY_COVERAGE_2026-11-15.md and deploy/REAL_ENVIRONMENT_WORK.md. Follow its rules. Start with items A1 to A3 on the real capture I give you: evaluate, show me what fails with the rows that prove it, fix it with a test, evaluate again. Write every result to docs/REAL_ENVIRONMENT_RESULTS.md. Ask me before anything touches a drive.`
10. **Build what is still not built.**
   `From section 3 of deploy/REAL_ENVIRONMENT_WORK.md, take the items in order (B1, the lab bench connection, first). For each: show me your plan in ten lines, build it, add its test, run bash run_tests.sh --offline, and write the new verdict of the statements it touches.`
11. **The NVMe command-level error rules, end to end (new in build 24).**
   `Read sections 4, 5 and 6 of docs/CHANGES_2026-11-15_round2.md. On the sample S17_io_timeout_abort_reset, start an analysis, and on page 3 choose the NVMe command timeout and the rule families "A command never completed", "The host sent an Abort" and "A read could not be recovered" under Errors > NVMe errors > NVMe command level errors. Take each through its result card, approve, and open one error of a family through isolation, cause, solution and its test. Show me every screen sentence that is wrong or unclear, with a screenshot. Change nothing before I agree.`
12. **The rule families with a real model (Family 4 writes their code).**
   `Read section 16 of docs/CHANGES_2026-11-15_round2.md. With the model I connect in Settings, choose one rule family that finds rows and one that finds nothing. Show me the requirements card, the code, and the Tester's comparison with the application's reference implementation. Count the model calls and the cards. Write the result to docs/REAL_ENVIRONMENT_RESULTS.md.`
13. **Timing learned on the procedural graph, on a real bench.**
   `Read section 8 of docs/CHANGES_2026-11-15_round2.md and the work items about the graph in deploy/REAL_ENVIRONMENT_WORK.md. The four constants there were chosen, not measured. Plan with me how to measure them on the real drive, and ask me before anything touches a drive.`
14. **My decisions.**
   `Read section 14 and section 18 of docs/CHANGES_2026-11-15_round2.md (45 decisions, and the ones section 18 adds). Put them to me ten at a time, each with the choice that is built today and what changes if I choose otherwise. Change nothing until I answer.`

**Where the work stands against the project's statement** (inside the code zip: `docs/OPPORTUNITY_COVERAGE_2026-11-15.md`).
The design has no code per measuring tool: any tool's recording is converted to CSV by the people who have the tool, and
the agent families learn the columns from the files. Of 16 statements, 0 are fully covered, 14 partly, 2 not; these
verdicts were not raised for what was built on 14 and 15 November, because nothing has run on real data yet.

**The addition to build 26 (24 November 2026)** adds, without taking anything away: a field on the start page for the category
of the input (Windows ADK, Teledyne LeCroy PCIe, PCMark 10 Storage, another tool, or recognised from the files).
*Windows ADK (ETL + XML):* the assessment's traces and XML files in any folder layout and under any names, no CSV needed;
each trace decoded with xperf; a run is PASS when the mean Fast Startup time of its iterations is at most 14 s; every run is
kept and the PASS runs make a benchmark; Compare ranks phase (pre-logon, logon, post-logon), process, command and file, and
lists **every command under every process** (disk and file I/O, page faults, driver time, every begin/end a Windows component
logs, child processes and threads, CPU, waits, DLL loads, every other event type) with its files, DLLs, drivers and modules;
I/O latency in 5 µs buckets; a summary whose numbers are checked. On the owner's real traces it finds the 128 s wait of the
volume-snapshot driver and 133 s of CPU in Ntfs.sys before the logon screen. *PCMark 10 Storage:* .pcmark10-result archives or
their CSV / XML read with UL's documented names (layout detected from each file), compared with a baseline of good results.
This is the first build that was run on Windows: the whole offline suite ran on a Windows laptop (Python 3.12, Git Bash)
on this build and on build 26 as it was. No test group and no test has another result than on build 26: 55 of 73 groups pass
(the two new groups, 27 and 19 tests, included), and the same 18 groups fail on build 26 too, for Windows reasons (Linux-only
parts of Python, the sample recordings not unpacked, Unix file behaviour); `docs/CHANGES_2026-11-24.md` section 9 has the list. Every Windows
ADK XML there was synthetic and no real PCMark 10 result was available; the pages were not looked at in a browser.

**Build 26 (15 November 2026)** makes a new installation keep only the three NVMe command rules as well: on the first start the
37 other rule families go straight to Deleted items (Restore brings one back); an existing library is left as it is. Every
test group this touches passes.

**Build 25 (15 November 2026, afternoon)** changes, on the owner's word: page 3 and the Rules library are one tree you open
level by level (section, kind of recording, level, group, item), with "Add" at every level and "Use it in this analysis" for a
rule the analysis does not use yet; under Errors, NVMe errors, NVMe command level errors only three rules are kept (NVMe command
timeout, Read failed, The command was aborted because the host asked), the other rule families are in Deleted items and can be
restored; every rule of Data analytics reads one CSV file on its own, never the tree. An independent check of the three rules
against the raw CSV files found two faults, both fixed (a completed command with empty status cells was called "never
completed"; a status written "81h" was read as decimal). Every test group these changes touch passes, and the measured evidence
passes; the record is section 18 of `docs/CHANGES_2026-11-15_round2.md` inside the code zip.

**Build 24 (15 November 2026, second round)** adds: one field for the REA agent; a start page without the question
"which tool exported this" (a folder without a CSV file says so, and the terminal agent can be asked about its files);
a rules library in a clear hierarchy (section, kind of recording, level, group, item) with add and edit in sight;
under Errors, NVMe errors, NVMe command level errors, 52 researched rule families, 38 of them runnable and offered (none
chosen in advance), taken in a strict order: rule, code, result approved by the admin, errors listed, isolation, cause and
solution, test; without a model they run the application's reference implementation, with a model the coding family
writes their code and the Tester compares it with that reference; timing kept as data on the procedural graph and
learned from earlier lab runs without training anything (on the simulated drive, with history of the same kind of
defect, the search needed a median of 10 lab runs instead of 48; with stale or wrong history it was worse in most single
cases); a repair of the engine, which could lose an approval pressed at the wrong instant. All 66 offline test groups
pass on Linux; the 10 groups through a running application and the browser pass with the stand-in except six checks
that need a real model's answer. One check of the measured evidence ("a defect that shows only 3 times in 10 is still
caught") found 8 of 10 instead of at least 9 in one run and 10 of 10 in the run before; it draws at random, and it was
being run again when this was pushed. The record is `docs/CHANGES_2026-11-15_round2.md` inside the code zip.

**Build 23 (15 November 2026)** adds, among other things: a start page that takes a recording of any tool; a reader for
CSV files as real tools write them (semicolon, tab, a header that is not on line 1, UTF-16, decimal commas); errors that
a rule finds in any CSV file, each with its own page and isolation; learning from earlier searches; the cause of a command
that never completed; a hand-over package of approved tests for a validation suite; the review cards of the agent
families handed to the terminal agent (the opencode program); and a recheck of the coding family's code by that agent.
All 70 test groups pass on Linux, on synthetic recordings and a simulated drive. One run with a real model on a CSV
disguised as another tool's export: 15 of 15 column meanings right, the rule's result exact. Nothing has run on Windows,
on a real capture of any tool, or on a real drive.

The agent must never print an API key, and nothing goes to this repository without the owner's word.
