# nerodebench-private

**Private. Never publish anything from this repository, or copy it into the public one.**

This repository holds what NerodeBench's leaderboard ranks on, and so what must stay
unseen: the private splits' build configs (with their secret seeds), the held-out rules
for `private-ood`, and, from v1.0, the frozen private items.

The public repository, [nerodebench](https://github.com/thethinkmachine/nerodebench), is
expected beside this one (`../nerodebench`). It has the generator, the scorer and the
item store; this repository only configures them.

## What is here

| Path | What |
| --- | --- |
| `rules/ood.py` | The held-out rules: six atoms, wordings and alphabets the public split never uses, a language source built from those atoms, and new Family C mutations |
| `builds/v1/private-iid.json` | 1,200 items: the public rules, a secret seed |
| `builds/v1/private-ood.json` | 400 items: the held-out rules, a secret seed |
| `tests/` | The held-out rules keep every public rule: each atom checked against its definition, every question read back to exactly its language |
| `data/` | The frozen private splits, from v1.0 (empty until the freeze) |

Both configs exclude the public manifest, and `private-ood` also excludes `private-iid`,
so no two splits ask about the same language.

## Commands

From this folder, with the public package on the path:

```text
export PYTHONPATH=../nerodebench/src            # Windows: set PYTHONPATH=..\nerodebench\src
python -m unittest

# Drafts go to build/ (git-ignored). Build the public split first, in ../nerodebench:
#   python -m nerodebench.store build builds/v1/public.json -o build/v1
python -m nerodebench.store build builds/v1/private-iid.json -o build/v1
python -m nerodebench.store build builds/v1/private-ood.json -o build/v1
python -m nerodebench.store verify build/v1/private-iid.jsonl --against ../nerodebench/build/v1/public.manifest.json --regenerate builds/v1/private-iid.json
python -m nerodebench.store verify build/v1/private-ood.jsonl --against ../nerodebench/build/v1/public.manifest.json --against build/v1/private-iid.manifest.json --regenerate builds/v1/private-ood.json
```

At the freeze, point each config's `exclude` at the frozen public manifest
(`../nerodebench/data/public/public.manifest.json`), build into `data/`, verify, commit
and tag `data-v1.0.0` (see the public `docs/freezing.md`).

## Handling private items

- Private items leave this machine only as API calls during evaluation. Use a provider's
  zero-data-retention option where one is offered.
- Never paste a private item into a chat, an issue or a public file. Publish private
  results as aggregates only.
- The private splits are refreshed every quarter with new seeds, because providers see
  the items when models are evaluated. A refresh changes only the seeds and the version.
