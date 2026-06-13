"""SA Practitioner Guide.

Staging package that publishes the South African localisation practitioner
documentation into a Frappe Wiki "Wiki Space".

Run on a site that has the Frappe Wiki app installed:

    bench --site <site> execute za_local.practitioner_guide.stage.stage_space

The operation is idempotent: re-running updates page content in place without
creating duplicate spaces, groups, or pages.
"""
