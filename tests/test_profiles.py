# SPDX-License-Identifier: MIT
import unittest

from paperfig.profiles import load_profile


class ProfileTests(unittest.TestCase):
    def test_target_profiles_have_sources(self) -> None:
        for venue in (
            "nature-machine-intelligence",
            "icml 2026",
            "neurips 2026",
            "eccv 2026",
        ):
            with self.subTest(venue=venue):
                profile = load_profile(venue)
                self.assertEqual("interpreted-working-profile", profile["status"])
                self.assertTrue(profile["sources"])
                self.assertEqual("2026-08-10", str(profile["verified_on"]))

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported venue profile"):
            load_profile("imaginary venue")


if __name__ == "__main__":
    unittest.main()
