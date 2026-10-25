import unittest
from unittest.mock import patch
from catalog_search import build_url, search_catalog

class CatalogSearchTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertIn("search_text=iPad", build_url("iPad"))
        for url in ["https://evil.com/catalog", "http://www.vinted.it/catalog",
                    "https://www.vinted.it/not-catalog", ""]:
            with self.assertRaises(ValueError):
                build_url(url)

    @patch("catalog_search.Vinted")
    def test_only_manual_fetch_and_filters(self, vinted):
        from types import SimpleNamespace
        objects = [
            SimpleNamespace(id=1, title="iPad Pro 11 M2 Pencil", price="500", currency="EUR", url="https://www.vinted.it/items/1", photo=None),
            SimpleNamespace(id=2, title="Custodia iPad M2", price="20", currency="EUR", url="https://www.vinted.it/items/2", photo=None),
            SimpleNamespace(id=3, title="iPad Pro 11 M1 Pencil", price="300", currency="EUR", url="https://www.vinted.it/items/3", photo=None),
        ]
        vinted.return_value.items.search.return_value = objects
        results, examined = search_catalog("iPad", pages=1, include="M2", exclude="custodia", max_price=600)
        self.assertEqual(examined, 3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "iPad Pro 11 M2 Pencil")
        vinted.return_value.items.search.assert_called_once()

if __name__ == "__main__":
    unittest.main()
