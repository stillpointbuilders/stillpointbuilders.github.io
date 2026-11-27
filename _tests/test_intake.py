"""Public intake routing contract. Run with python3 -m unittest discover -s _tests."""

import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = "https://stillpointbuilders.com/#estimate"
PHONE = "tel:+19842542131"


class Page(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.links = {}
        self.forms = []
        self.current_link = None
        self.link_text = []
        self.source = (ROOT / filename).read_text(encoding="utf-8")
        self.feed(self.source)
        self.close()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a":
            self.current_link = attrs.get("href")
            self.link_text = []
        if tag == "form":
            self.forms.append(attrs)

    def handle_data(self, data):
        if self.current_link is not None:
            self.link_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_link is not None:
            label = " ".join("".join(self.link_text).split())
            self.links[label] = self.current_link
            self.current_link = None


class IntakeTests(unittest.TestCase):
    def test_every_request_opens_the_homepage_intake_without_javascript(self):
        page = Page("index.html")
        for label in ("Get Your Free Estimate", "Get Fast Track Quote", "Get Quick Quote",
                      "Schedule Consultation", "Schedule Inspection", "Start Your Transformation",
                      "Start your request"):
            with self.subTest(label=label):
                self.assertEqual(page.links.get(label), INTAKE)
        self.assertEqual(page.links["Contact"], "#contact")
        self.assertIn('id="contact"', page.source)

    def test_legacy_page_no_longer_collects_or_acknowledges_unsent_data(self):
        page = Page("index.html")
        self.assertEqual(page.forms, [])
        self.assertNotIn("alert(", page.source)
        self.assertNotIn("within 24 hours", page.source.lower())

    def test_old_confirmation_url_is_safe_to_open_directly(self):
        page = Page("thank-you.html")
        self.assertIn(INTAKE, page.links.values())
        self.assertIn("/", page.links.values())
        self.assertNotRegex(page.source.lower(), r"(we.ve received|has been received|within 24 hours)")

    def test_phone_fallback_matches_the_current_business_number(self):
        for filename in ("index.html", "thank-you.html"):
            with self.subTest(filename=filename):
                phones = {href for href in Page(filename).links.values() if href.startswith("tel:")}
                self.assertEqual(phones, {PHONE})
