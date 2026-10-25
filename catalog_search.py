"""On-demand catalog search. Does not touch notification queries or item history."""
import re
from urllib.parse import urlparse, urlencode
from pyVintedVN import Vinted

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

def search_catalog(search, pages=1, include="", exclude="", max_price=None):
    """Return (matching listings, examined count), without persisting or notifying."""
    url = build_url(search)
    pages = max(1, min(int(pages), 3))
    include_terms = [t.strip().casefold() for t in include.split(",") if t.strip()]
    exclude_terms = [t.strip().casefold() for t in exclude.split(",") if t.strip()]
    found, seen, examined = [], set(), 0
    client = Vinted()
    for page in range(1, pages + 1):
        items = client.items.search(url, nbr_items=40, page=page)
        if not items:
            break
        for item in items:
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
