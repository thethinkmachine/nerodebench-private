"""The held-out rules for NerodeBench's private-ood split. NEVER PUBLISH.

Everything here is absent from the public generator, so a model trained on the
public split, or on the public generator, meets it for the first time:

- six atoms (Family A): properties of words the public specs never use;
- new wordings (Family A): openings, group intros and task lines;
- new alphabets (all families): symbol names the public split never uses;
- a new language source (Families B to D): combinations of the held-out atoms,
  where the public split uses random expressions;
- new mutations (Family C): swapping two symbols inside a subexpression, or
  swapping two of one state's moves, where the public split flips an accepting
  state, redirects one move or edits an expression.

Every atom keeps the public rules: its DFA is checked word by word against its
``holds`` definition (tests/test_ood.py), no wording contains "and" or "or",
and a wording function raises for parameters the atom never takes.
"""

from __future__ import annotations

from nerodebench.answers import regex_text
from nerodebench.automata import Dfa, LimitReached, dfa_of_nfa, minimize, nfa_of_regex
from nerodebench.generate.atoms import Atom, q
from nerodebench.generate.families import Retry
from nerodebench.generate.spec import Wording, compile_spec, sample_spec
from nerodebench.regexes import _nodes, _replace, regex_of_dfa, sym

NAME = "ood-v1"


def _table(alphabet, n, start, accept, move) -> Dfa:
    return Dfa(tuple(alphabet), start, frozenset(accept), tuple(tuple(move(s, a) for a in alphabet) for s in range(n)))


def _complement(d: Dfa) -> Dfa:
    return Dfa(d.alphabet, d.start, frozenset(set(range(d.n)) - set(d.accept)), d.delta)


def _two(rng, alphabet):
    x, y = rng.sample(list(alphabet), 2)
    return x, y


def _atom(name, sample, build, phrasings, holds) -> Atom:
    return Atom(name, sample, build, lambda p, negated: phrasings(p, negated)[0], holds, phrasings)


# ── no two equal neighbours ───────────────────────────────────────


def _no_repeat_build(alphabet, p):
    n = len(alphabet)
    # 0 start, 1..n "last symbol was alphabet[i-1]", n+1 dead.
    def move(s, a):
        i = alphabet.index(a) + 1
        if s == n + 1 or s == i:
            return n + 1
        return i

    return _table(alphabet, n + 2, 0, range(n + 1), move)


def _no_repeat_phrasings(p, negated):
    if p:
        raise ValueError("no_repeat takes no parameters")
    if negated:
        return ["some two adjacent symbols of the string are equal", "the string has the same symbol twice in a row somewhere"]
    return ["no two adjacent symbols of the string are equal", "the string never has the same symbol twice in a row"]


def _no_repeat_holds(word, p):
    return all(x != y for x, y in zip(word, word[1:]))


# ── a scattered subsequence ───────────────────────────────────────


def _subsequence_sample(rng, alphabet):
    return {"w": "".join(rng.choice(alphabet) for _ in range(rng.randint(2, 3)))}


def _subsequence_build(alphabet, p):
    w, n = p["w"], len(p["w"])
    return _table(alphabet, n + 1, 0, [n], lambda s, a: s if s == n else (s + 1 if a == w[s] else s))


def _subsequence_phrasings(p, negated):
    w = p["w"]
    if len(w) < 2:
        raise ValueError("a subsequence of at least two symbols")
    w = q(w)
    if negated:
        return [
            f"the symbols of {w} do not appear in the string in that order (even with gaps between them)",
            f"{w} is not a subsequence of the string (its symbols in order, gaps allowed)",
        ]
    return [
        f"the symbols of {w} appear in the string in that order (not necessarily next to each other)",
        f"{w} is a subsequence of the string (its symbols in order, gaps allowed)",
    ]


def _subsequence_holds(word, p):
    it = iter(word)
    return all(c in it for c in p["w"])


# ── every x is immediately followed by y ─────────────────────────


def _followed_sample(rng, alphabet):
    x, y = _two(rng, alphabet)
    return {"x": x, "y": y}


def _followed_build(alphabet, p):
    x, y = p["x"], p["y"]
    # 0 fine, 1 owes a y, 2 dead.
    def move(s, a):
        if s == 2:
            return 2
        if s == 1:
            return 0 if a == y else 2
        return 1 if a == x else 0

    return _table(alphabet, 3, 0, [0], move)


def _followed_phrasings(p, negated):
    if p["x"] == p["y"]:
        raise ValueError("x and y differ")
    x, y = q(p["x"]), q(p["y"])
    if negated:
        return [
            f"some {x} in the string is not immediately followed by {y}",
            f"at least one occurrence of {x} in the string does not have {y} right after it",
        ]
    return [f"every {x} in the string is immediately followed by {y}", f"each occurrence of {x} in the string has {y} right after it"]


def _followed_holds(word, p):
    return all(i + 1 < len(word) and word[i + 1] == p["y"] for i, c in enumerate(word) if c == p["x"])


# ── a difference of counts, modulo m ─────────────────────────────


def _diff_sample(rng, alphabet):
    x, y = _two(rng, alphabet)
    m = rng.choice([2, 3, 3, 4])
    return {"x": x, "y": y, "m": m, "r": rng.choice([0, 0, *range(1, m)])}


def _diff_build(alphabet, p):
    m = p["m"]
    return _table(alphabet, m, 0, [p["r"]], lambda s, a: (s + 1) % m if a == p["x"] else (s - 1) % m if a == p["y"] else s)


def _diff_phrasings(p, negated):
    x, y, m, r = p["x"], p["y"], p["m"], p["r"]
    if x == y or not (m >= 2 and 0 <= r < m):
        raise ValueError("bad parameters")
    x, y = q(x), q(y)
    diff = f"the number of times {x} occurs in the string minus the number of times {y} occurs"
    sub = f"subtracting the number of times {y} occurs in the string from the number of times {x} occurs gives"
    no = "not " if negated else ""
    if r == 0:
        return [f"{diff} is {no}divisible by {m}", f"{sub} {'a number that is not ' if negated else ''}a multiple of {m}"]
    return [f"{diff} is {no}congruent to {r} modulo {m}", f"{sub} a number {no}congruent to {r} modulo {m}"]


def _diff_holds(word, p):
    return (word.count(p["x"]) - word.count(p["y"])) % p["m"] == p["r"]


# ── overlapping occurrences of a block, modulo m ─────────────────


def _blocks_sample(rng, alphabet):
    m = rng.choice([2, 3])
    return {"w": "".join(rng.choice(alphabet) for _ in range(2)), "m": m, "r": rng.choice([0, 0, *range(1, m)])}


def _blocks_build(alphabet, p):
    w, m, r = p["w"], p["m"], p["r"]
    k = len(w) - 1
    index, order, rows = {((), 0): 0}, [((), 0)], []
    for tail, c in order:
        row = []
        for a in alphabet:
            seen = tail + (a,)
            c2 = (c + (1 if "".join(seen[-len(w):]) == w and len(seen) >= len(w) else 0)) % m
            state = (seen[-k:] if k else (), c2)
            if state not in index:
                index[state] = len(order)
                order.append(state)
            row.append(index[state])
        rows.append(tuple(row))
    return Dfa(tuple(alphabet), 0, frozenset(i for i, (_, c) in enumerate(order) if c == r), tuple(rows))


def _blocks_phrasings(p, negated):
    w, m, r = p["w"], p["m"], p["r"]
    if len(w) < 2 or not (m >= 2 and 0 <= r < m):
        raise ValueError("bad parameters")
    count = f"the number of times {q(w)} occurs in the string as a block (overlapping occurrences count separately)"
    no = "not " if negated else ""
    if r == 0:
        return [f"{count} is {no}divisible by {m}", f"{count} is {no}a multiple of {m}"]
    return [f"{count} is {no}congruent to {r} modulo {m}"]


def _blocks_holds(word, p):
    w = p["w"]
    return sum(1 for i in range(len(word) - len(w) + 1) if word[i : i + len(w)] == w) % p["m"] == p["r"]


# ── every symbol at odd (or even) positions ──────────────────────


def _parity_sample(rng, alphabet):
    # first = 1: the odd positions (1, 3, 5, ...); first = 2: the even ones.
    return {"symbol": rng.choice(alphabet), "first": rng.choice([1, 2])}


def _parity_build(alphabet, p):
    odd = p["first"] == 1
    # 0: the next position is odd, 1: even, 2: dead.
    def move(s, a):
        if s == 2:
            return 2
        if (s == 0) == odd and a != p["symbol"]:
            return 2
        return 1 - s

    return _table(alphabet, 3, 0, [0, 1], move)


def _parity_phrasings(p, negated):
    if p["first"] not in (1, 2):
        raise ValueError("first is 1 or 2")
    s = q(p["symbol"])
    par = "odd" if p["first"] == 1 else "even"
    where = "the first, third, fifth, ..." if par == "odd" else "the second, fourth, sixth, ..."
    if negated:
        return [
            f"some symbol in an {par} position of the string (counting from 1) is not {s}",
            f"not every symbol at the {par} positions of the string ({where}) is {s}",
        ]
    return [
        f"every symbol in an {par} position of the string (counting from 1) is {s}",
        f"every symbol at the {par} positions of the string ({where}) is {s}",
    ]


def _parity_holds(word, p):
    return all(c == p["symbol"] for c in word[p["first"] - 1 :: 2])


OOD_ATOMS = [
    _atom("no_repeat", lambda rng, a: {}, _no_repeat_build, _no_repeat_phrasings, _no_repeat_holds),
    _atom("subsequence", _subsequence_sample, _subsequence_build, _subsequence_phrasings, _subsequence_holds),
    _atom("followed_by", _followed_sample, _followed_build, _followed_phrasings, _followed_holds),
    _atom("count_difference_mod", _diff_sample, _diff_build, _diff_phrasings, _diff_holds),
    _atom("block_count_mod", _blocks_sample, _blocks_build, _blocks_phrasings, _blocks_holds),
    _atom("parity_positions", _parity_sample, _parity_build, _parity_phrasings, _parity_holds),
]

OOD_WORDING = Wording(
    heads=(
        "Let L be the set of strings over the alphabet {sigma}. A string is in L exactly when",
        "Over the alphabet {sigma}, a string should be accepted precisely when",
    ),
    intros=(
        ("every condition below is satisfied", "the following conditions are all met"),
        ("at least one condition below is satisfied", "one or more of the conditions below are met"),
    ),
    tasks=(
        "Build a DFA recognizing exactly this language.",
        "Design a deterministic finite automaton that accepts precisely these strings.",
    ),
)

OOD_ALPHABETS = {2: [("x", "y"), ("u", "v")], 3: [("x", "y", "z"), ("1", "2", "3")]}


# ── Families B to D: where languages come from ────────────────────


def ood_source(rng, alphabet, budget):
    """A language built from the held-out atoms, with an expression for it."""
    atoms = {a.name: a for a in OOD_ATOMS}
    n = 1 + budget[1] // 6
    spec = sample_spec(rng, atoms, alphabet, n, nested=False)
    d = minimize(compile_spec(spec, atoms, alphabet))
    if d.n > 14:
        raise Retry
    ast = regex_of_dfa(d)
    if len(regex_text(ast)) > 10 * budget[1]:
        raise Retry  # an expression too long to show
    return ast, d


def _swap_in_subexpression(rng, ast, alphabet):
    """Swap two symbols everywhere inside one random subexpression."""
    nodes = [(path, node) for path, node in _nodes(ast) if node[0] not in ("sym", "eps", "empty")]
    if not nodes:
        raise Retry
    path, node = rng.choice(nodes)
    x, y = rng.sample(list(alphabet), 2)

    def swap(t):
        k = t[0]
        if k == "sym":
            return sym(y if t[1] == x else x if t[1] == y else t[1])
        if k in ("cat", "union"):
            return (k, [swap(c) for c in t[1]])
        if k in ("star", "plus", "opt"):
            return (k, swap(t[1]))
        return t

    return _replace(ast, path, swap(node))


def ood_mutate(rng, ast, d, alphabet):
    """Family C's held-out edits."""
    if ast is not None and rng.random() < 0.6:
        ast2 = _swap_in_subexpression(rng, ast, alphabet)
        try:
            return ast2, minimize(dfa_of_nfa(nfa_of_regex(ast2), alphabet))
        except LimitReached:
            raise Retry from None
    q0 = rng.randrange(d.n)
    i, j = rng.sample(range(len(alphabet)), 2)
    rows = [list(r) for r in d.delta]
    rows[q0][i], rows[q0][j] = rows[q0][j], rows[q0][i]
    return None, minimize(Dfa(d.alphabet, d.start, d.accept, tuple(tuple(r) for r in rows)))


def rules(public):
    return public.with_atoms(OOD_ATOMS, only=True).with_(
        name=NAME, wording=OOD_WORDING, alphabets=OOD_ALPHABETS, source=ood_source, mutate=ood_mutate
    )
