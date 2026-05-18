from pathlib import Path

import frappe
from frappe import _


def resolve_app_path(*parts) -> Path:
	"""Resolve a packaged za_local path and reject traversal outside the app."""
	app_root = Path(frappe.get_app_path("za_local")).resolve()
	path = app_root.joinpath(*(str(part) for part in parts)).resolve()

	try:
		path.relative_to(app_root)
	except ValueError:
		frappe.throw(_("Invalid packaged file path: {0}").format("/".join(str(part) for part in parts)))

	return path


def ensure_app_path(path) -> Path:
	"""Validate an existing path object/string as belonging to the za_local app."""
	app_root = Path(frappe.get_app_path("za_local")).resolve()
	resolved_path = Path(path).resolve()

	try:
		resolved_path.relative_to(app_root)
	except ValueError:
		frappe.throw(_("Invalid packaged file path: {0}").format(resolved_path.name))

	return resolved_path


def read_app_json(path_or_first_part, *parts):
	"""Read packaged JSON after confirming the target stays under za_local."""
	if parts:
		path = resolve_app_path(path_or_first_part, *parts)
	else:
		path_arg = Path(path_or_first_part)
		path = ensure_app_path(path_arg) if path_arg.is_absolute() else resolve_app_path(path_arg)
	return frappe.get_file_json(str(path))


def read_app_text(path_or_first_part, *parts) -> str:
	"""Read packaged text after confirming the target stays under za_local."""
	if parts:
		path = resolve_app_path(path_or_first_part, *parts)
	else:
		path_arg = Path(path_or_first_part)
		path = ensure_app_path(path_arg) if path_arg.is_absolute() else resolve_app_path(path_arg)
	return frappe.read_file(str(path), raise_not_found=True)
