# SA Practitioner Guide (Wiki staging)

This package publishes the South African localisation practitioner documentation
into a Frappe **Wiki Space** named **"SA Practitioner Guide"** at route `/sa-guide`.

## Contents

- `manifest.py` — the navigation tree (sections and pages). Single source of truth.
- `content/*.md` — one markdown file per page.
- `stage.py` — idempotent staging script that creates/updates the Wiki Space,
  section groups, and pages from the manifest and markdown.

## Requirements

The target site must have the Frappe **Wiki** app installed (provides the
`Wiki Space` and `Wiki Document` DocTypes):

```bash
bench get-app wiki
bench --site <site> install-app wiki
```

## Stage (or refresh) the guide

Two ways, both idempotent and equivalent:

**From the desk (no terminal):** open **ZA Local Setup** (SA Overview workspace) and
click **Documentation → Publish Practitioner Guide**. The button appears only when the
Frappe Wiki app is installed and requires the System Manager role.

**From the command line:**

```bash
bench --site <site> execute za_local.practitioner_guide.stage.stage_space
```

Both match the space, sections and pages by route and refresh page content in place.
Re-run any time you edit a markdown file or the manifest. After staging, the guide is
available at `/<site>/sa-guide`.

## Whitelisted endpoints

- `za_local.practitioner_guide.stage.is_wiki_available` — returns whether the Wiki app is installed (used to gate the desk button).
- `za_local.practitioner_guide.stage.publish_practitioner_guide` — System-Manager-only action that stages the guide and returns a feedback dict.

## Editing

- **Edit a page:** change the markdown in `content/` and re-run staging.
- **Add a page:** add the `.md` file to `content/`, add an entry to the relevant
  group's `pages` list in `manifest.py`, and re-run staging.
- **Add a section:** append a new group dict to `GROUPS` in `manifest.py`.

Cross-page links use routes of the form `../<group-key>/<page-slug>`; keep them in
sync with the `key`/`slug` values in `manifest.py`.
