"""On-demand catalog search. Does not touch notification queries or item history."""
import re
from urllib.parse import urlparse, urlencode
from pyVintedVN import Vinted
from apify_catalog import available, fetch_rows, normalize_row, CatalogProviderError


VINTED_HOST = re.compile(r"^(?:www\.)?vinted\.[a-z]{2,3}$", re.I)

def build_url(search):
    search = search.strip()
    if not search:
        raise ValueError("Inserisci una ricerca o un URL di Vinted.")
    if len(search) > 1200:
        raise ValueError("Ricerca troppo lunga.")
    if search.startswith(("http://", "https://")):
        parsed = urlparse(search)
        if parsed.scheme != "https" or not parsed.hostname or not VINTED_HOST.fullmatch(parsed.hostname) or parsed.port is not None or parsed.path != "/catalog" or parsed.username:
            raise ValueError("Usa un link HTTPS a /catalog su un dominio Vinted valido.")
        return search
    return "https://www.vinted.it/catalog?" + urlencode({"search_text": search, "order": "newest_first"})

def search_catalog(search, pages=1, include="", exclude="", max_price=None, with_details=False):
    """Return (matching listings, examined count), without persisting or notifying."""
    url = build_url(search)
    pages = max(1, min(int(pages), 3))
    include_terms = [t.strip().casefold() for t in include.split(",") if t.strip()]
    exclude_terms = [t.strip().casefold() for t in exclude.split(",") if t.strip()]
    found, seen, examined = [], set(), 0
    if not available():
        raise CatalogProviderError(
            "Il vecchio motore Vinted non è più disponibile. Configura APIFY_TOKEN in Portainer."
        )
    items = fetch_rows(url, max_items=pages * 40, with_details=with_details)
    for raw in items:
        try:
            item = normalize_row(raw)
        except ValueError:
            continue
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        examined += 1
        title = (item["title"] + " " + (item["description"] if with_details else "")).casefold()
        if any(term not in title for term in include_terms):
            continue
        if any(term in title for term in exclude_terms):
            continue
        if max_price is not None and item["price"] > max_price:
            continue
        found.append(item)
    return found, examined

            if str(item.id) in seen:
                continue
            seen.add(str(item.id))
            examined += 1
            # The catalog API wrapper currently exposes titles, not full descriptions.
            title = (item.title or "").casefold()
            if any(term not in title for term in include_terms):
                continue
            if any(term in title for term in exclude_terms):
                continue
            try:
                price = float(item.price)
            except (ValueError, TypeError):
                continue
            if max_price is not None and price > max_price:
                continue
            found.append({"title": item.title, "price": price, "currency": item.currency,
                          "url": item.url, "photo": item.photo})
    return found, examined
