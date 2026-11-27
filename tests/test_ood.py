"""The held-out rules keep every rule the public ones do."""

import itertools
import random
import unittest
from pathlib import Path

from nerodebench.generate import TIERS, generate, load_rules, public_rules
from nerodebench.generate.reading import Lexicon, check_english
from nerodebench.generate.spec import HEADS, INTROS, TASKS, choose_style, compile_spec, render, sample_spec, sentence_ok
from nerodebench.score import score_response
from nerodebench.store import fingerprint, problems, reference_answer

ROOT = Path(__file__).resolve().parent.parent
RULES = load_rules(ROOT / "rules" / "ood.py")
PUBLIC = public_rules()


def words(alphabet, n):
    for k in range(n + 1):
        for w in itertools.product(alphabet, repeat=k):
            yield "".join(w)


class HeldOutAtomTest(unittest.TestCase):
    def test_every_atom_builds_the_language_its_definition_names(self):
        rng = random.Random(1)
        for atom in RULES.atoms.values():
            for alphabet in [("x", "y"), ("1", "2", "3")]:
                for _ in range(30):
                    p = atom.sample(rng, alphabet)
                    d = atom.build(alphabet, p)
                    for w in words(alphabet, 6 if len(alphabet) == 2 else 5):
                        self.assertEqual(d.accepts(w), atom.holds(w, p), f"{atom.name} {p} {w!r}")

    def test_wordings_follow_the_public_rules(self):
        rng = random.Random(2)
        for atom in RULES.atoms.values():
            for _ in range(20):
                p = atom.sample(rng, ("x", "y", "z"))
                yes, no = atom.variants(p, False), atom.variants(p, True)
                self.assertEqual(len(set(yes + no)), len(yes + no), atom.name)
                for w in yes + no:
                    self.assertNotRegex(w, r"\b(and|or)\b", f"{atom.name}: {w}")

    def test_nothing_held_out_is_public(self):
        self.assertFalse(set(RULES.atoms) & set(PUBLIC.atoms))
        self.assertFalse(set(RULES.wording.heads) & set(HEADS))
        self.assertFalse(set(RULES.wording.tasks) & set(TASKS))
        self.assertFalse(set(RULES.wording.intros[0] + RULES.wording.intros[1]) & set(INTROS["all"] + INTROS["any"]))
        public_symbols = {"a", "b", "c", "0", "1", "2"}
        for alphabets in RULES.alphabets.values():
            for a in alphabets:
                self.assertNotEqual(set(a), set(a) & public_symbols, a)
                self.assertNotIn("q", a, "q reads as a state name (q0, q1, ...)")

    def test_every_held_out_question_reads_back_to_exactly_its_language(self):
        rng = random.Random(3)
        lexicon = Lexicon.of(RULES.wording)
        for i in range(250):
            alphabet = rng.choice([("x", "y"), ("x", "y", "z")])
            spec = sample_spec(rng, RULES.atoms, alphabet, rng.randint(1, 4), nested=rng.random() < 0.5)
            style = choose_style(rng, spec, RULES.atoms, RULES.wording)
            if sentence_ok(spec) and "atom" not in spec and i % 2:
                style["form"] = "sentence"
            text = render(spec, RULES.atoms, alphabet, style, RULES.wording)
            check = check_english(text, RULES.atoms, alphabet, compile_spec(spec, RULES.atoms, alphabet), lexicon)
            self.assertTrue(check.ok, f"{check}\n{text}")


class HeldOutItemTest(unittest.TestCase):
    def test_every_family_and_tier_makes_valid_items(self):
        for family, tiers in TIERS.items():
            for tier in tiers:
                with self.subTest(family=family, tier=tier):
                    for item in generate(family, tier, 4, "ood-test", RULES):
                        self.assertEqual(item["meta"]["rules"], "ood-v1")
                        self.assertTrue(set(item["alphabet"]) <= set("xyzuv123"), item["alphabet"])
                        self.assertEqual(problems({**item, "split": "private-ood"}), [])
                        self.assertEqual(score_response(item, reference_answer(item))["verdict"], "correct")
                        fingerprint(item)
                        if family == "A":
                            self.assertTrue(set(item["meta"]["atoms"]) <= set(RULES.atoms))


if __name__ == "__main__":
    unittest.main()
