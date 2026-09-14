# Progress

Last updated: 14 September 2026

## Where we are right now

Phase 1, Foundations. Setup complete, memory system being built.

## Next step

Set up the CI robot on GitHub so it checks work automatically.
Then start Phase 2, Product 1 (Triage), beginning with the product spec.

## Done so far

### Session 1 - Setup
- Created the repo github.com/SurabhiDeb/chatbot-lab
- Cloned it to /Users/surabhideb/Desktop/chatbot-lab with GitHub Desktop
- Confirmed VS Code opens it and Python 3.13.5 is installed
- Learned: repository, clone, commit, push, terminal, markdown

### Session 2 - Memory system
- Created the CONTEXT folder
- Did the full loop for the first time: write in VS Code, commit in
  GitHub Desktop, push, confirm on GitHub
- Built the five CONTEXT files

## Not started yet

- Python virtual environment
- CI (the automatic checking robot)
- Product 1 Triage, all six beats
- Products 2, 3, 4

## Where we are right now

Phase 2, Product 1 (Triage). Beat 1 done, Beat 2 in progress.

## Next step

Fix the case-sensitivity bug in check_data.py, then build the crude
classifier that calls the Claude API.

### Session 3 - CI
- Built .github/workflows/hello.yml, saw it pass and fail on purpose
- Learned: CI, workflow, runner, YAML, exit codes, fail fast

### Session 4 - Triage spec and first script
- Wrote products/triage/SPEC.md, 8 teams, 4 urgency tiers,
  5 escalation triggers, 7 critical failures
- Wrote products/triage/data/seed.csv, 20 labelled messages
- Set up .venv and .gitignore
- Wrote check_data.py, first Python program, and it found a real bug
  (spreadsheet rewrote true to TRUE)
- Key insight: escalation recall 99%, precision 70%. Under-escalation
  costs far more than over-escalation.
- TODO: need 60-100 labelled messages, five teams have only one example
- TODO: get Anthropic API key with a spend limit set