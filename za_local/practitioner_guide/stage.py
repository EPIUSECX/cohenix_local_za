"""Stage the SA Practitioner Guide into a Frappe Wiki "Wiki Space".

Usage:

    bench --site <site> execute za_local.practitioner_guide.stage.stage_space

Idempotent: matches the space, section groups, and pages by route, refreshing
page content in place. Safe to re-run after editing any markdown file.

Requires the Frappe Wiki app (provides the "Wiki Space" and "Wiki Document"
DocTypes). If Wiki is not installed the function exits with a clear message.
"""

from pathlib import Path

import frappe
from frappe import _

from za_local.practitioner_guide.manifest import GROUPS, SPACE

CONTENT_DIRNAME = "content"


def _content_dir() -> Path:
	return Path(frappe.get_app_path("za_local", "practitioner_guide", CONTENT_DIRNAME))


def _read_page_body(filename: str) -> str:
	path = _content_dir() / filename
	if not path.exists():
		frappe.throw(f"SA Practitioner Guide content file not found: {filename}")
	return path.read_text(encoding="utf-8")


def _wiki_installed() -> bool:
	return frappe.db.exists("DocType", "Wiki Space") and frappe.db.exists("DocType", "Wiki Document")


def _get_or_create_space() -> "frappe.Document":
	existing = frappe.db.get_value("Wiki Space", {"route": SPACE["route"]}, "name")
	if existing:
		space = frappe.get_doc("Wiki Space", existing)
		changed = False
		if space.space_name != SPACE["space_name"]:
			space.space_name = SPACE["space_name"]
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
	space.space_name = SPACE["space_name"]
	space.route = SPACE["route"]
	space.is_published = 1
	space.show_in_switcher = 1
	space.insert(ignore_permissions=True)
	return space


def _upsert_document(*, route, title, parent, is_group, sort_order, content=None):
	"""Create or update a Wiki Document, matched by route."""
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


def stage_space():
	"""Publish (or refresh) the entire SA Practitioner Guide Wiki Space."""
	if not _wiki_installed():
		msg = "Frappe Wiki app is not installed on this site. Install it first: bench get-app wiki && bench --site <site> install-app wiki"
		print(msg)
		return msg

	space = _get_or_create_space()
	space_route = SPACE["route"]
	root_group = space.root_group

	created_groups = 0
	created_pages = 0
	for group_index, group in enumerate(GROUPS):
		group_route = f"{space_route}/{group['key']}"
		group_name = _upsert_document(
			route=group_route,
			title=group["title"],
			parent=root_group,
			is_group=True,
			sort_order=group_index,
		)
		created_groups += 1

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
			created_pages += 1

	# No explicit frappe.db.commit(): the surrounding transaction is committed by
	# the request (whitelisted button) or by `bench execute` on success. Frappe's
	# transaction model discourages manual commits.
	summary = (
		f"SA Practitioner Guide staged at /{space_route}: "
		f"{created_groups} sections, {created_pages} pages."
	)
	print(summary)
	return summary


@frappe.whitelist()
def is_wiki_available():
	"""Lightweight check used by the desk to decide whether to show the publish button."""
	return bool(_wiki_installed())


@frappe.whitelist()
def publish_practitioner_guide():
	"""Whitelisted action: publish/refresh the SA Practitioner Guide Wiki Space.

	Returns a feedback dict for the za_local desk feedback helper. Restricted to
	System Manager because it writes site-wide Wiki content.
	"""
	frappe.only_for("System Manager")

	if not _wiki_installed():
		return {
			"title": _("Wiki Not Installed"),
			"indicator": "orange",
			"message": _(
				"The Frappe Wiki app is not installed on this site, so the practitioner "
				"guide cannot be published. Install it with: bench --site &lt;site&gt; install-app wiki"
			),
		}

	summary = stage_space()
	return {
		"title": _("Practitioner Guide Published"),
		"indicator": "green",
		"message": _("{0} Open it at /{1}.").format(summary, SPACE["route"]),
	}
