import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
"""Offline tests for data/scripts/run_all.py command-building + classify."""
import importlib.util
import unittest

SCRIPT = os.path.join(REPO, "data", "scripts", "run_all.py")
spec = importlib.util.spec_from_file_location("run_all", SCRIPT)
ra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ra)


class Args(object):
    """Stand-in for argparse.Namespace with runner defaults."""
    def __init__(self, **kw):
        self.headless = kw.get("headless", False)
        self.fresh = kw.get("fresh", False)
        self.sleep = kw.get("sleep", None)
        self.terms = kw.get("terms", None)
        self.light = kw.get("light", False)
        self.deep = kw.get("deep", False)


class TestBuildCommand(unittest.TestCase):
    def test_only_supported_flags_are_passed(self):
        args = Args(headless=True, fresh=True, sleep=4.0,
                    terms=["energy drink"])
        # youtube supports only sleep — must NOT get headless/fresh/terms
        yt = ra.build_command(ra.BY_NAME["youtube"], args)
        self.assertIn("--sleep", yt)
        self.assertNotIn("--headless", yt)
        self.assertNotIn("--fresh", yt)
        self.assertNotIn("--terms", yt)

    def test_browser_scraper_gets_headless_and_terms(self):
        args = Args(headless=True, terms=["Celsius energy drink"])
        wm = ra.build_command(ra.BY_NAME["walmart"], args)
        self.assertIn("--headless", wm)
        self.assertIn("--terms", wm)
        self.assertIn("Celsius energy drink", wm)

    def test_fresh_only_where_supported(self):
        args = Args(fresh=True)
        self.assertIn("--fresh", ra.build_command(ra.BY_NAME["walmart"], args))
        # amazon does not support --fresh
        self.assertNotIn("--fresh", ra.build_command(ra.BY_NAME["amazon"], args))

    def test_light_mode_adds_caps(self):
        cmd = ra.build_command(ra.BY_NAME["amazon"], Args(light=True))
        self.assertIn("--max-products", cmd)
        self.assertIn("5", cmd)

    def test_deep_mode_adds_bigger_caps(self):
        cmd = ra.build_command(ra.BY_NAME["walmart"], Args(deep=True))
        self.assertIn("--review-pages", cmd)
        self.assertIn("40", cmd)

    def test_retailers_excludes_kroger_via_fixed_args(self):
        cmd = ra.build_command(ra.BY_NAME["retailers"], Args())
        self.assertIn("--retailers", cmd)
        self.assertNotIn("kroger", cmd)
        self.assertIn("target", cmd)

    def test_kroger_has_its_own_entry(self):
        self.assertIn("kroger", ra.BY_NAME)
        cmd = ra.build_command(ra.BY_NAME["kroger"], Args())
        self.assertTrue(cmd[1].endswith("scrape_kroger.py"))

    def test_command_targets_the_right_script(self):
        cmd = ra.build_command(ra.BY_NAME["reddit"], Args())
        self.assertTrue(cmd[1].endswith("scrape_reddit.py"))


class TestClassify(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(ra.classify(0, ["  wrote x (10 rows)"]), "OK")

    def test_blocked(self):
        self.assertEqual(
            ra.classify(1, ["BLOCKED: Walmart challenge..."]), "BLOCKED")

    def test_failed(self):
        self.assertEqual(ra.classify(1, ["Traceback", "ValueError"]), "FAILED")


class TestRegistry(unittest.TestCase):
    def test_every_scraper_has_a_script(self):
        for s in ra.SCRAPERS:
            path = os.path.join(REPO, "data", "scripts",
                                "scrape_%s.py" % s["name"])
            self.assertTrue(os.path.exists(path), path)

    def test_light_and_deep_flags_cover_all_scrapers(self):
        names = {s["name"] for s in ra.SCRAPERS}
        self.assertEqual(set(ra.LIGHT_FLAGS), names)
        self.assertEqual(set(ra.DEEP_FLAGS), names)

    def test_order_is_api_first_browser_last(self):
        groups = [s["group"] for s in ra.SCRAPERS]
        self.assertEqual(groups[0], "api")   # youtube leads
        self.assertEqual(groups[1], "api")   # reddit second


if __name__ == "__main__":
    unittest.main(verbosity=1)
