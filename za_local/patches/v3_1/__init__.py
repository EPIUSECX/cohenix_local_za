# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Patches for za_local app.

Note: This directory is reserved for one-time data migrations only.
Setup tasks (custom fields, property setters, master data) are handled
in za_local.setup.install hooks (after_install, after_migrate).

According to Frappe best practices:
- Patches = One-time data migrations (e.g., updating existing records)
- Install hooks = Setup tasks (e.g., creating custom fields, property setters)
"""
