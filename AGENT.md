# AGENT RULES

## Code style

* Indentation is 2 spaces, in every file (Python, HTML, CSS, JavaScript, JSON).
* Never write comments in code (Python, HTML, CSS, JavaScript). No inline comments, no block comments, no docstrings, no section dividers.
* Comments are allowed only in specifications and in files directly tied to a specification, for example the JSON files at the root (`structure.json`, `config.draft.json`).
* Every string in code is written in English: log messages, error messages, labels, placeholders, user-facing text, identifiers.
* Names are explicit and in English.

## Optimization

* Always think about optimization first.
* Always start from what exists: reuse the current mechanisms, and introduce a change only when it is necessary.
* Always look for a clever solution that avoids introducing a big loop. Prefer work done per cycle, per batch, and per element from the point of view of the element itself (at its visit, at its reception, at its reinforcement): there is always a place where the process takes the least time.

## Git

* An agent never commits.
* An agent never changes the history or the state of the git repository: no add, stash, reset, checkout, merge, rebase, tag or any equivalent.
* Only consultation is possible (status, diff, log, show), and only with explicit authorization from the user.

# AGENT.md

* Do not modify this file unless the user explicitly asks.
