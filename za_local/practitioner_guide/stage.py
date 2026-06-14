"""Stage the South African localisation guides into Frappe Wiki "Wiki Spaces".

Two guides are published as separate spaces (see ``manifest.GUIDES``):

- SA Practitioner Guide  -> /sa-guide
- SA End-User Guide      -> /sa-user-guide

Usage:

    bench --site <site> execute za_local.practitioner_guide.stage.stage_space

Idempotent: matches each space, its section groups, and pages by route, and
refreshes page content in place. Existing pages are updated, not duplicated, so
re-running after editing any markdown file (or after a new release) brings the
on-site Wiki up to date.

Requires the Frappe Wiki app (provides the "Wiki Space" and "Wiki Document"
DocTypes). If Wiki is not installed the function exits with a clear message.
"""

from pathlib import Path

import frappe
from frappe import _

from za_local.practitioner_guide.manifest import GUIDES

CONTENT_DIRNAME = "content"


def _content_dir() -> Path:
	return Path(frappe.get_app_path("za_local", "practitioner_guide", CONTENT_DIRNAME))


def _read_page_body(filename: str) -> str:
	path = _content_dir() / filename
	if not path.exists():
		frappe.throw(f"SA guide content file not found: {filename}")
	return path.read_text(encoding="utf-8")


def _wiki_installed() -> bool:
	return frappe.db.exists("DocType", "Wiki Space") and frappe.db.exists("DocType", "Wiki Document")


def _get_or_create_space(space_def: dict) -> "frappe.Document":
	existing = frappe.db.get_value("Wiki Space", {"route": space_def["route"]}, "name")
	if existing:
		space = frappe.get_doc("Wiki Space", existing)
		changed = False
		if space.space_name != space_def["space_name"]:
			space.space_name = space_def["space_name"]
			changed = True
		if not space.is_published:
			space.is_published = 1
			changed = True
		if changed:
			space.save(ignore_permissions=True)
		# before_insert creates the root group only on insert; ensure it exists.
		if not space.root_group:
			space.create_root_group()
			space.save(ignore_permissions=True)
		return space

	space = frappe.new_doc("Wiki Space")
	space.space_name = space_def["space_name"]
	space.route = space_def["route"]
	space.is_published = 1
	space.show_in_switcher = 1
	space.insert(ignore_permissions=True)
	return space


def _upsert_document(*, route, title, parent, is_group, sort_order, content=None):
	"""Create or update a Wiki Document, matched by route. Refreshes content in place."""
	name = frappe.db.get_value("Wiki Document", {"route": route}, "name")
	if name:
		doc = frappe.get_doc("Wiki Document", name)
	else:
		doc = frappe.new_doc("Wiki Document")
		doc.route = route

	doc.title = title
	doc.parent_wiki_document = parent
	doc.is_group = 1 if is_group else 0
	doc.is_published = 1
	doc.sort_order = sort_order
	if content is not None:
		doc.content = content

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return doc.name


def _stage_guide(guide: dict) -> str:
	"""Publish (or refresh) a single guide's Wiki Space and return a one-line summary."""
	space_def = guide["space"]
	space = _get_or_create_space(space_def)
	space_route = space_def["route"]
	root_group = space.root_group

	section_count = 0
	page_count = 0
	for group_index, group in enumerate(guide["groups"]):
		group_route = f"{space_route}/{group['key']}"
		group_name = _upsert_document(
			route=group_route,
			title=group["title"],
			parent=root_group,
			is_group=True,
			sort_order=group_index,
		)
		section_count += 1

		for page_index, page in enumerate(group["pages"]):
			page_route = f"{group_route}/{page['slug']}"
			body = _read_page_body(page["file"])
			_upsert_document(
				route=page_route,
				title=page["title"],
				parent=group_name,
				is_group=False,
				sort_order=page_index,
				content=body,
			)
			page_count += 1

	return f"{space_def['space_name']} (/{space_route}): {section_count} sections, {page_count} pages"


def stage_space():
	"""Publish (or refresh) all SA localisation guides.

	Named ``stage_space`` for backward compatibility with the documented
	``bench execute`` command. Stages every guide in ``manifest.GUIDES``.
	"""
	if not _wiki_installed():
		msg = "Frappe Wiki app is not installed on this site. Install it first: bench get-app wiki && bench --site <site> install-app wiki"
		print(msg)
		return msg

	# No explicit frappe.db.commit(): the surrounding transaction is committed by
	# the request (whitelisted button) or by `bench execute` on success. Frappe's
	# transaction model discourages manual commits.
	summaries = [_stage_guide(guide) for guide in GUIDES]
	summary = "Staged SA localisation guides — " + "; ".join(summaries) + "."
	print(summary)
	return summary


@frappe.whitelist()
def is_wiki_available():
	"""Lightweight check used by the desk to decide whether to show the publish button."""
	return bool(_wiki_installed())


@frappe.whitelist()
def publish_practitioner_guide():
	"""Whitelisted action: publish/refresh all SA localisation Wiki guides.

	Returns a feedback dict for the za_local desk feedback helper. Restricted to
	System Manager because it writes site-wide Wiki content.
	"""
	frappe.only_for("System Manager")

	if not _wiki_installed():
		return {
			"title": _("Wiki Not Installed"),
			"indicator": "orange",
			"message": _(
				"The Frappe Wiki app is not installed on this site, so the guides "
				"cannot be published. Install it with: bench --site &lt;site&gt; install-app wiki"
			),
		}

	summary = stage_space()
	routes = ", ".join(f"/{guide['space']['route']}" for guide in GUIDES)
	return {
		"title": _("Documentation Guides Published"),
		"indicator": "green",
		"message": _("{0} Open them at: {1}.").format(summary, routes),
	}
