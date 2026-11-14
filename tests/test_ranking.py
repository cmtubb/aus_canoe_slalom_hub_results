import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import ranking

def run(time, penalty=0):
    return {"time": time, "penalty": penalty}

def ranks(ranked):
    return [(entry["surname"], rank) for entry, rank in ranked]

class TestBestOfTwo(unittest.TestCase):

    def test_best_run_counts(self):
        entries = [{"surname": "A", "runs": [run(100, 50), run(110)]},
                   {"surname": "B", "runs": [run(105), run(120)]}]

        ranked, unplaced = ranking.rank_class("best_of_two", entries)

        self.assertEqual(ranks(ranked), [("B", 1), ("A", 2)])
        self.assertEqual(unplaced, [])

    def test_ties_share_rank(self):
        entries = [{"surname": "A", "runs": [run(100.1, 2), {"status": "DNS"}]},
                   {"surname": "B", "runs": [run(99.0)]},
                   {"surname": "C", "runs": [run(102.1)]},
                   {"surname": "D", "runs": [run(103.0)]}]

        ranked, _ = ranking.rank_class("best_of_two", entries)

        # 100.1 + 2 and 102.1 are equal to 0.01 s
        self.assertEqual(ranks(ranked), [("B", 1), ("A", 2), ("C", 2), ("D", 4)])

    def test_no_completed_run_is_unplaced(self):
        entries = [{"surname": "A", "runs": [{"status": "DNS"}, {"status": "DNS"}]},
                   {"surname": "B", "runs": [{"status": "CAP", "penalty": 50}, run(130)]},
                   {"surname": "C", "runs": [{"status": "DNF"}]}]

        ranked, unplaced = ranking.rank_class("best_of_two", entries)

        self.assertEqual(ranks(ranked), [("B", 1)])
        self.assertEqual([entry["surname"] for entry in unplaced], ["A", "C"])

class TestHeatsFinals(unittest.TestCase):

    def test_a_final_then_b_final_then_heats(self):
        entries = [{"surname": "HEATS_FAST", "heats": [run(80)], "final": None},
                   {"surname": "B1", "heats": [run(95)], "final": {"name": "B", **run(90)}},
                   {"surname": "A2", "heats": [run(92)], "final": {"name": "A", **run(99)}},
                   {"surname": "A1", "heats": [run(91)], "final": {"name": "A", **run(98)}},
                   {"surname": "HEATS_SLOW", "heats": [run(120)], "final": None}]

        ranked, _ = ranking.rank_class("heats_finals", entries)

        self.assertEqual(ranks(ranked), [("A1", 1), ("A2", 2), ("B1", 3), ("HEATS_FAST", 4), ("HEATS_SLOW", 5)])

    def test_final_dns_and_cap_ranked_on_heats(self):
        # Vic 2025 K1W: both in the A final, POTUGUNTLA CAP and HAMMOND DNS
        entries = [{"surname": "CASSERLEY", "heats": [run(136.67, 54), run(122.26, 2)],
                    "final": {"name": "A", **run(153.31, 108)}},
                   {"surname": "POTUGUNTLA", "heats": [{"status": "CAP"}, run(186.68, 154)],
                    "final": {"name": "A", "status": "CAP", "penalty": 52}},
                   {"surname": "HAMMOND", "heats": [run(195.01, 258), run(178.51, 108)],
                    "final": {"name": "A", "status": "DNS"}}]

        ranked, _ = ranking.rank_class("heats_finals", entries)

        self.assertEqual(ranks(ranked), [("CASSERLEY", 1), ("HAMMOND", 2), ("POTUGUNTLA", 3)])

    def test_ties_share_rank_within_a_final_only(self):
        entries = [{"surname": "A1", "heats": [run(90)], "final": {"name": "A", **run(100)}},
                   {"surname": "A2", "heats": [run(91)], "final": {"name": "A", **run(100)}},
                   {"surname": "B1", "heats": [run(92)], "final": {"name": "B", **run(100)}}]

        ranked, _ = ranking.rank_class("heats_finals", entries)

        self.assertEqual(ranks(ranked), [("A1", 1), ("A2", 1), ("B1", 3)])

    def test_no_completed_run_is_unplaced(self):
        entries = [{"surname": "A", "heats": [{"status": "DNS"}, {"status": "DNS"}], "final": None}]

        ranked, unplaced = ranking.rank_class("heats_finals", entries)

        self.assertEqual(ranked, [])
        self.assertEqual(len(unplaced), 1)

class TestPlacings(unittest.TestCase):

    def test_places_used_as_given(self):
        entries = [{"surname": "B", "place": 2}, {"surname": "A", "place": 1},
                   {"surname": "C", "place": 2}, {"surname": "D", "place": None}]

        ranked, unplaced = ranking.rank_class("placings", entries)

        self.assertEqual(ranks(ranked), [("A", 1), ("B", 2), ("C", 2)])
        self.assertEqual([entry["surname"] for entry in unplaced], ["D"])

if __name__ == "__main__":
    unittest.main()
