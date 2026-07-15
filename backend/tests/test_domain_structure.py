"""Architecture tests for the backend's domain-first package layout."""

import unittest
from pathlib import Path

APP_DIRECTORY = Path(__file__).resolve().parents[1] / "app"
DOMAIN_NAMES = (
    "auth",
    "chat",
    "common",
    "community",
    "course",
    "history",
    "place",
    "ranking",
    "weather",
)
LAYER_NAMES = ("application", "domain", "infrastructure", "presentation")


class DomainStructureTest(unittest.TestCase):
    def test_every_domain_exposes_the_standard_layer_packages(self) -> None:
        for domain_name in DOMAIN_NAMES:
            with self.subTest(domain=domain_name):
                domain_directory = APP_DIRECTORY / domain_name
                self.assertTrue((domain_directory / "__init__.py").is_file())

                for layer_name in LAYER_NAMES:
                    layer_directory = domain_directory / layer_name
                    self.assertTrue(layer_directory.is_dir())
                    self.assertTrue((layer_directory / "__init__.py").is_file())

    def test_domain_roots_do_not_contain_layer_implementation_modules(self) -> None:
        for domain_name in DOMAIN_NAMES:
            with self.subTest(domain=domain_name):
                domain_directory = APP_DIRECTORY / domain_name
                flat_modules = sorted(
                    path.name
                    for path in domain_directory.glob("*.py")
                    if path.name != "__init__.py"
                )
                self.assertEqual([], flat_modules)
