"""Optional paid catalog provider for environments challenged by Cloudflare.

Requires an Apify API token. Never attempts to bypass Vinted's access controls
from the home server. Calls amitaviv/vinted-scraper on Apify instead.
"""
import os
from urllib.parse import urlparse

import requests

ACTOR_ENDPOINT = (
    "https://api.apify.com/v2/acts/"
    "amitaviv~vinted-scraper/run-sync-get-dataset-items"
)


class CatalogProviderError(RuntimeError):
    """Human-readable provider failure, without leaking credentials."""


def available():
    return bool(os.environ.get("APIFY_TOKEN", "").strip())


def fetch_rows(search_url, max_items=40, with_details=False, monitor_key=None):
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise CatalogProviderError(
            "Apify non configurato: aggiungi APIFY_TOKEN nello stack Portainer."
        )

    parsed = urlparse(search_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("URL di ricerca non valido.")

    count = max(1, min(120, int(max_items)))
    payload = {
        "startUrls": [{"url": search_url}],
        "maxItemsPerQuery": count,
        "includeDetails": bool(with_details),
        "includeBusinessNames": False,
        "includePrivateSellerData": False,
        "onlyNew": bool(monitor_key),
    }
    if monitor_key:
        payload["monitorKey"] = str(monitor_key)[:100]

    try:
        response = requests.post(
            ACTOR_ENDPOINT,
            headers={"Authorization": "Bearer " + token},
            json=payload,
            timeout=(15, 285),
        )
        if response.status_code == 401:
            raise CatalogProviderError("Token Apify non valido (401).")
        if response.status_code == 402:
            raise CatalogProviderError("Crediti Apify esauriti o pagamento richiesto (402).")
        if response.status_code == 403:
            raise CatalogProviderError("Accesso all'Actor Apify negato (403).")
        if response.status_code in (408, 504):
            raise CatalogProviderError(
                "Esecuzione Apify troppo lunga; verifica la Console Apify prima di riprovare."
            )
        if response.status_code != 201 and response.status_code != 200:
            raise CatalogProviderError(
                "Apify non ha completato la ricerca (HTTP "
                + str(response.status_code) + ")."
            )
        rows = response.json()
        if not isinstance(rows, list):
            raise CatalogProviderError("Formato di risposta Apify inatteso.")
        return [row for row in rows if isinstance(row, dict) and row.get("id") and row.get("url")]
    except requests.Timeout as exc:
        raise CatalogProviderError(
            "Timeout Apify. La ricerca può continuare ad avere un costo: controlla la Console."
        ) from exc
    except requests.RequestException as exc:
        raise CatalogProviderError("Connessione ad Apify non riuscita.") from exc
    except ValueError as exc:
        raise CatalogProviderError("La risposta Apify non contiene JSON valido.") from exc


def normalize_row(row):
    """Convert an actor row into our stable result schema."""
    try:
        amount = float(row["price"])
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("Prezzo non valido nel risultato Apify.") from exc
    return {
        "id": str(row["id"]),
        "title": str(row.get("title") or ""),
        "description": str(row.get("description") or ""),
        "price": amount,
        "currency": row.get("currency") or "EUR",
        "url": str(row["url"]),
        "photo": row.get("photoUrl") or row.get("thumbnailUrl"),
        "brand": row.get("brand") or "",
    }
