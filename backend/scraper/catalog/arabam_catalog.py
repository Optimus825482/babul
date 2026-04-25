from services.vehicle_catalog_service import load_catalog


class ArabamCatalog:
    """Placeholder adapter for future arabam.com catalog discovery."""

    source = "arabam.com"

    def fetch(self):
        # The live arabam.com catalog parser will land here. Until then, keep
        # refresh deterministic and local by returning the current cache.
        return load_catalog()
