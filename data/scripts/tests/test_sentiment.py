import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
"""Offline tests for data/scripts/analyze_sentiment.py (lexicon model only —
vader/transformer are optional deps exercised manually)."""
import importlib.util
import unittest

SCRIPT = os.path.join(REPO, "data", "scripts", "analyze_sentiment.py")
spec = importlib.util.spec_from_file_location("analyze_sentiment", SCRIPT)
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)


class TestLexicon(unittest.TestCase):
    def test_positive(self):
        self.assertGreater(sa.lexicon_score("I love this, great clean energy"), 0.05)

    def test_negative(self):
        self.assertLess(sa.lexicon_score("gross aftertaste and a terrible crash"), -0.05)

    def test_negation_flips(self):
        pos = sa.lexicon_score("this is good")
        neg = sa.lexicon_score("this is not good")
        self.assertGreater(pos, 0)
        self.assertLess(neg, 0)

    def test_intensifier_amplifies(self):
        base = sa.lexicon_score("this is good")
        amped = sa.lexicon_score("this is really good")
        self.assertGreater(amped, base)

    def test_empty_is_neutral(self):
        self.assertEqual(sa.lexicon_score(""), 0.0)
        self.assertEqual(sa.label_of(0.0), "neu")

    def test_labels(self):
        self.assertEqual(sa.label_of(0.5), "pos")
        self.assertEqual(sa.label_of(-0.5), "neg")


class TestThemes(unittest.TestCase):
    def test_theme_tagging(self):
        tags = sa.themes_of("tastes great but too expensive and I crashed hard")
        self.assertIn("taste", tags)
        self.assertIn("price", tags)
        self.assertIn("crash", tags)
        self.assertNotIn("packaging", tags)

    def test_all_theme_patterns_compile_and_match_something(self):
        probes = {"taste": "the flavor", "sweetness": "too sweet",
                  "energy": "caffeine kick", "crash": "gave me a headache",
                  "price": "great value", "health": "zero sugar",
                  "packaging": "can arrived dented"}
        for theme, text in probes.items():
            self.assertIn(theme, sa.themes_of(text), theme)


class TestBrands(unittest.TestCase):
    def test_brand_from_text(self):
        self.assertEqual(sa.brand_from_text("i only drink redbull"), "Red Bull")
        self.assertEqual(sa.brand_from_text("alani is better"), "Alani Nu")
        self.assertIsNone(sa.brand_from_text("prime-time television show"))

    def test_norm_brand(self):
        self.assertEqual(sa.norm_brand("celsius"), "Celsius")


class TestAgg(unittest.TestCase):
    def test_percentages_sum(self):
        agg = sa.Agg()
        for s in (0.5, -0.5, 0.0, 0.9):
            agg.add(s)
        row = agg.row()
        self.assertEqual(row["n"], 4)
        self.assertAlmostEqual(
            row["pct_pos"] + row["pct_neg"] + row["pct_neu"], 100.0, places=0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
