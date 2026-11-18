import unittest
import votes


class VotingTests(unittest.TestCase):
    def test_vote_semantics_and_grouping(self):
        rows = votes.load()
        self.assertEqual(len(rows), 30)
        for row in rows:
            self.assertEqual(row["dissent"], row["preferred_bps"] != row["majority_bps"])
        self.assertTrue(next(r for r in rows if r["meeting"] == "2025-06-06" and "Bhattacharya" in r["member"])["dissent"])
        report = votes.evaluate(rows)
        self.assertEqual((report["training"], report["testing"], report["dissent"]), (18,12,1))
        self.assertEqual(report["metrics"]["majority"]["balanced_accuracy"], 0.5)
        self.assertEqual(report["metrics"]["leaked"]["accuracy"], 1.0)

    def test_label_detector(self):
        with self.assertRaises(ValueError):
            votes.assert_clean([{"meeting":"2024-06-07","member":"Example","reason":"She voted no."}])
