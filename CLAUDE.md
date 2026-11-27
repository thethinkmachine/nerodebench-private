# CLAUDE.md

Notes for Claude Code sessions in this repository.

This is NerodeBench's **private** repository: the private splits' configs and secret
seeds, the held-out rules for `private-ood`, and later the frozen private items. The
generator, scorer and store are in the public repository beside it (`../nerodebench`);
read its CLAUDE.md for how they work.

## Rules that are load-bearing

- **Nothing from here goes anywhere public**: not to the public repository, an issue,
  a pull request, a chat with a third party, or a web request. That includes the seeds,
  the held-out atoms and wordings, and any private item. When the public repository
  needs a change these rules depend on, make the change there in general terms.
- **Held-out rules keep every public rule.** An atom's DFA must agree with its `holds`
  definition, no clause wording contains "and" or "or", a wording function raises for
  parameters the atom never takes, and every generated question must read back to exactly
  its language. `python -m unittest` checks all of it.
- **No alphabet symbol may be `q`**: state names are `q0`, `q1`, ...
- **Seeds change only at a refresh**, with a new version in the config.
- **LF line endings** (`.gitattributes`): item files are hashed.

## Commands

```bash
export PYTHONPATH=../nerodebench/src
python -m unittest
python -m nerodebench.store build builds/v1/private-iid.json -o build/v1
python -m nerodebench.store verify build/v1/private-iid.jsonl --against ../nerodebench/build/v1/public.manifest.json --regenerate builds/v1/private-iid.json
```

## Commits

No `Co-Authored-By` line or any other Claude attribution in commit messages. The
maintainer owns the repository (`thethinkmachine`); it stays private for good.
