import json, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import steward  # noqa: E402

def run(*a):
    return subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "steward.py"), *a],
                          capture_output=True, text=True)

class Money(unittest.TestCase):
    def test_cents(self):
        self.assertEqual(steward.cents("12.5"), 1250)
        self.assertEqual(steward.cents(0.1), 10)
        self.assertEqual(steward.fmt(-305), "-3.05")

    def test_allocate_sums_exactly(self):
        for total in (1, 100, 799, 1001):
            s = steward.allocate(total, {"a": 1, "b": 1, "c": 1})
            self.assertEqual(sum(s.values()), total)
        self.assertEqual(steward.allocate(10, {"a": 0, "b": 0}), {"a": 5, "b": 5})

class Split(unittest.TestCase):
    def test_example_matches_quote(self):
        r = run("split", os.path.join(ROOT, "examples", "team-lunch.json"), "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["matches_quote"])
        self.assertEqual(len(out["transfers"]), 4)

    def test_gap_is_reported(self):
        d = {"quote_total": "20.00", "lines": [{"who": "a", "price": "10"}, {"who": "b", "price": "9"}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(d, f)
        r = run("split", f.name, "--json")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["gap"], "-1.00")

class Offers(unittest.TestCase):
    def test_verdicts(self):
        r = run("offers", os.path.join(ROOT, "examples", "weekly-offers.json"), "--json")
        v = {x["offer"]: x["verdict"] for x in json.loads(r.stdout)}
        self.assertEqual(v["Spend 40 save 5"], "USE IF QUOTE CONFIRMS")
        self.assertEqual(v["Spend 70 save 10"], "SKIP")
        self.assertEqual(v["Spend 50 save 6"], "ONLY IF FILLER IS WANTED")
        self.assertEqual(v["Free delivery"], "DROP")
        self.assertEqual(v["Yogurt 2-for-1"], "DROP")

class Ledger(unittest.TestCase):
    def test_add_and_summary(self):
        p = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        run("ledger", "add", "--file", p, "--merchant", "Grocer", "--total", "46.3", "--date", "2026-10-21", "--quote-ref", "Q1")
        run("ledger", "add", "--file", p, "--merchant", "Grocer", "--total", "10", "--date", "2026-10-22")
        r = run("ledger", "summary", "--file", p, "--month", "2026-10")
        self.assertIn("2 order(s) in 2026-10, total 56.30", r.stdout)
        self.assertIn("1 order(s) have no quote", r.stdout)

if __name__ == "__main__":
    unittest.main()
