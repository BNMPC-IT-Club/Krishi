"""Safety checks for the deterministic disease-treatment allow-list."""
from __future__ import annotations

import unittest

from backend.disease_guidance import get_disease_guidance


class DiseaseGuidanceTests(unittest.TestCase):
    def test_acrobat_is_only_listed_for_supported_potato_blight_classes(self) -> None:
        for class_label in ("Potato___Early_blight", "Potato___Late_blight"):
            with self.subTest(class_label=class_label):
                guidance = get_disease_guidance(class_label)
                self.assertEqual([item["registration_no"] for item in guidance["products"]], ["AP-353"])
                self.assertEqual(guidance["products"][0]["rate"], "৪ গ্রাম / ১ লিটার পানি")
                self.assertIn("আলু", guidance["products"][0]["label_scope"])

    def test_cabrio_cucurbit_powdery_mildew_mapping_matches_record(self) -> None:
        guidance = get_disease_guidance("Squash___Powdery_mildew")
        self.assertEqual([item["registration_no"] for item in guidance["products"]], ["AP-1770"])
        product = guidance["products"][0]
        self.assertEqual(product["label_scope"], "কুমড়াজাতীয় (Cucurbits) — Powdery mildew")
        self.assertEqual(product["rate"], "৩ গ্রাম / ১ লিটার পানি")
        self.assertEqual(product["source_url"], "https://ppw.krishi.gov.bd/pesticide-details/4522")

    def test_unverified_tomato_early_blight_product_is_withheld(self) -> None:
        guidance = get_disease_guidance("Tomato___Early_blight")
        self.assertEqual(guidance["products"], [])
        self.assertIn("স্বাধীনভাবে নিশ্চিত", guidance["product_note"])
        self.assertNotIn("Rosa 72SL", guidance["product_note"])

    def test_no_product_is_inferred_for_unverified_crop_disease_pairs(self) -> None:
        for class_label in (
            "Tomato___Late_blight",
            "Tomato___Spider_mites Two-spotted_spider_mite",
            "Corn_(maize)___Common_rust_",
        ):
            with self.subTest(class_label=class_label):
                self.assertEqual(get_disease_guidance(class_label)["products"], [])

    def test_healthy_class_never_gets_a_pesticide_recommendation(self) -> None:
        guidance = get_disease_guidance("Potato___healthy")
        self.assertEqual(guidance["category"], "healthy_class")
        self.assertEqual(guidance["products"], [])
        self.assertIn("সুস্থ", guidance["reason"])


if __name__ == "__main__":
    unittest.main()
