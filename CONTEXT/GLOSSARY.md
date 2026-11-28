# Glossary

Plain English. Added to as we go.

**Repository (repo).** A project folder that tracks its own history. Every
change ever made is recorded and can be undone.

**Clone.** Downloading a repo from GitHub onto your computer, staying
connected so the two can sync.

**Commit.** A saved snapshot of your work with a note saying what changed.
Like a save point in a game.

**Push.** Sending your commits from your computer up to GitHub.

**Branch.** A parallel copy of the project where you can make changes
without affecting the original.

**Terminal.** A window where you type commands instead of clicking buttons.
It is how you run code.

**Markdown (.md).** Plain text with simple formatting. `#` makes a heading,
`-` makes a bullet. GitHub displays it nicely.

**CI (continuous integration).** A robot on GitHub that automatically checks
your work every time you save something to GitHub.

**Python.** The programming language we are writing in.

**VS Code.** The editor. Where you type code.

**GitHub Desktop.** The app that saves snapshots and syncs them to GitHub.
It cannot write or run code.

**Eval.** A test for an AI system, where the correct answer is fuzzy rather
than exact.

**RAG (retrieval augmented generation).** The bot looks things up in your
documents before answering, instead of guessing from memory.

Workflow in CI. A file that tells the robot what to do. It lives in a folder called .github/workflows.

Runner. The temporary cloud computer that does the work.

**C-numbers, two unrelated meanings.** The repo uses `C` followed by a digit
for two different things, and they do not line up.

In `SPEC.md`, C1 to C5 are *critical failure classes*. C1 is internal content
reaching a customer, C3 is an answer drawn from an archived or superseded
article, C5 is output that breaks the contract. Result rows carry these as a
field, `"critical": "C3"`.

In the dossier study, C0 to C5 are *experimental conditions*, one per run
file. C3 there is the shipped configuration, prompt v4 with the filtered
retriever on Haiku 4.5.

So "C3" means an archived-article failure or the shipped config depending on
which document you are in. The condition mapping is in
`products/policydesk/runs/conditions-notes.md`.
