import unittest
from earthworks_audit import audit
CONFIG = dict(absolute_tolerance_m3=1, relative_tolerance=0.02, maximum_interval_m=25)
S = [dict(station_m=0,cut_area_m2=10,fill_area_m2=0), dict(station_m=20,cut_area_m2=14,fill_area_m2=2)]
C = [dict(from_m=0,to_m=20,claimed_cut_m3=240,claimed_fill_m3=20)]

class EarthworksTests(unittest.TestCase):
    def test_hand_calculation(self):
        r = audit(S,C,CONFIG)
        self.assertEqual(r['totals'], {'cut_m3':240,'fill_m3':20,'net_cut_minus_fill_m3':220})
        self.assertEqual(r['review_items'],0)

    def test_relative_threshold(self):
        for delta, flagged in [(4.8,False),(4.81,True),(-4.81,True)]:
            r = audit(S,[dict(C[0],claimed_cut_m3=240+delta)],CONFIG)
            self.assertEqual(bool(r['review_items']),flagged)

    def test_zero_volume_uses_absolute_tolerance(self):
        s = [dict(r,cut_area_m2=0) for r in S]
        r = audit(s,[dict(C[0],claimed_cut_m3=2)],CONFIG)
        self.assertIn('CUT_DIFFERENCE_EXCEEDS_TOLERANCE',r['intervals'][0]['findings'])

    def test_missing_extra_claims(self):
        r = audit(S,[dict(C[0],to_m=21)],CONFIG)
        self.assertEqual(r['review_items'],2)
        self.assertEqual(len(r['unmatched_claims']),1)

    def test_out_of_order_or_duplicate_station(self):
        for s in [list(reversed(S)),[S[0],S[0]]]:
            with self.assertRaises(ValueError):
                audit(s,C,CONFIG)

    def test_duplicate_numeric_claim_keys(self):
        with self.assertRaises(ValueError):
            audit(S,C+[dict(C[0],from_m='0.0')],CONFIG)

    def test_negative_area(self):
        with self.assertRaises(ValueError):
            audit([dict(S[0],fill_area_m2=-1),S[1]],C,CONFIG)

    def test_long_interval_review(self):
        r = audit(S,C,dict(CONFIG,maximum_interval_m=10))
        self.assertIn('INTERVAL_EXCEEDS_DEMO_LIMIT',r['intervals'][0]['findings'])
