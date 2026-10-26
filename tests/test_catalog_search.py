import os
import unittest
from unittest.mock import patch, MagicMock

from apify_catalog import CatalogProviderError, fetch_rows
from catalog_search import build_url, search_catalog


class CatalogSearchTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertIn("search_text=iPad", build_url("iPad"))
        for url in [
            "https://evil.com/catalog",
            "http://www.vinted.it/catalog",
            "https://www.vinted.it/not-catalog",
            "",
        ]:
            with self.assertRaises(ValueError):
                build_url(url)

    @patch("catalog_search.available", return_value=True)
    @patch("catalog_search.fetch_rows")
    def test_manual_search_filters(self, fetch, _available):
        fetch.return_value = [
            {"id": "1", "title": "iPad Pro 11 M2", "description": "Apple Pencil inclusa", "price": 500, "currency": "EUR", "url": "https://www.vinted.it/items/1"},
            {"id": "2", "title": "Custodia iPad M2", "price": 20, "currency": "EUR", "url": "https://www.vinted.it/items/2"},
            {"id": "3", "title": "iPad Pro M1", "price": 300, "currency": "EUR", "url": "https://www.vinted.it/items/3"},
        ]
        rows, checked = search_catalog(
            "iPad", include="M2, pencil", exclude="custodia",
            max_price=600, with_details=True,
        )
        self.assertEqual(checked, 3)
        self.assertEqual([r["id"] for r in rows], ["1"])
        fetch.assert_called_once()

    @patch("catalog_search.available", return_value=False)
    def test_no_secret_disables_provider(self, _available):
        with self.assertRaises(CatalogProviderError):
            search_catalog("iPad")

    @patch.dict(os.environ, {"APIFY_TOKEN": "test-secret"})
    @patch("apify_catalog.requests.post")
    def test_provider_request_and_errors(self, request_post):
        response = MagicMock()
        response.status_code = 201
        response.json.return_value = [
            {"id": "1", "url": "https://www.vinted.it/items/1", "title": "iPad", "price": 100}
        ]
        request_post.return_value = response
        rows = fetch_rows("https://www.vinted.it/catalog?search_text=ipad", max_items=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(request_post.call_args.kwargs["json"]["maxItemsPerQuery"], 10)
        self.assertNotIn("test-secret", str(request_post.call_args.kwargs["json"]))

        response.status_code = 402
        with self.assertRaisesRegex(CatalogProviderError, "Crediti"):
            fetch_rows("https://www.vinted.it/catalog?search_text=ipad")


if __name__ == "__main__":
    unittest.main()
