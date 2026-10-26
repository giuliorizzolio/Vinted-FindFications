"""Routes for manual catalog search, isolated from notification flows."""
from flask import Blueprint, render_template, request
from catalog_search import search_catalog
from apify_catalog import CatalogProviderError, available

catalogo_bp = Blueprint("catalogo", __name__)

@catalogo_bp.route("/catalogo", methods=["GET", "POST"])
def catalogo():
    values = {"search": "", "include": "", "exclude": "", "max_price": "", "pages": 1, "with_details": ""}
    results, examined, error, searched = [], 0, None, False
    if request.method == "POST":
        searched = True
        values = {key: request.form.get(key, "").strip() for key in values}
        try:
            pages = int(values["pages"])
            if not 1 <= pages <= 3:
                raise ValueError("Seleziona da 1 a 3 pagine.")
            values["pages"] = pages
            price = None
            if values["max_price"]:
                price = float(values["max_price"])
                if not 0 <= price <= 100000:
                    raise ValueError("Prezzo massimo non valido.")
            results, examined = search_catalog(values["search"], pages, values["include"], values["exclude"], price, bool(values["with_details"]))
        except (ValueError, TypeError, CatalogProviderError) as exc:
            error = str(exc)
        except Exception:
            error = "Vinted non è raggiungibile o ha rifiutato la richiesta. Riprova più tardi."
    return render_template("catalogo.html", filters=values, provider_ready=available(), results=results,
                           examined=examined, error=error, searched=searched)
