ZERO_RATED_CATEGORIES = {"Zero Rated", "Export Zero Rated"}


def sync_item_zero_rated_flag(doc, method=None):
	if not hasattr(doc, "custom_sa_vat_category") or not hasattr(doc, "is_zero_rated"):
		return

	doc.is_zero_rated = 1 if (doc.custom_sa_vat_category or "").strip() in ZERO_RATED_CATEGORIES else 0
