app_name = "za_local"
app_title = "South African Localization"
app_publisher = "Cohenix"
app_description = "Cohenix ZA_Local is a comprehensive South African localization module for Cohenix ERPthat provides essential features for businesses operating in South Africa. It covers statutory compliance requirements, tax regulations, payroll localization, and financial reporting specific to the South African context."
app_email = "info@cohenix.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "za_local",
# 		"logo": "/assets/za_local/logo.png",
# 		"title": "South African Localization",
# 		"route": "/za_local",
# 		"has_permission": "za_local.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/za_local/css/za_local.css"
# app_include_js = "/assets/za_local/js/za_local.js"

# include js, css files in header of web template
# web_include_css = "/assets/za_local/css/za_local.css"
# web_include_js = "/assets/za_local/js/za_local.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "za_local/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "za_local/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "za_local.utils.jinja_methods",
# 	"filters": "za_local.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "za_local.install.before_install"
# after_install = "za_local.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "za_local.uninstall.before_uninstall"
# after_uninstall = "za_local.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "za_local.utils.before_app_install"
# after_app_install = "za_local.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "za_local.utils.before_app_uninstall"
# after_app_uninstall = "za_local.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "za_local.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"za_local.tasks.all"
# 	],
# 	"daily": [
# 		"za_local.tasks.daily"
# 	],
# 	"hourly": [
# 		"za_local.tasks.hourly"
# 	],
# 	"weekly": [
# 		"za_local.tasks.weekly"
# 	],
# 	"monthly": [
# 		"za_local.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "za_local.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "za_local.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "za_local.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "za_local.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["za_local.utils.before_request"]
# after_request = ["za_local.utils.after_request"]

# Job Events
# ----------
# before_job = ["za_local.utils.before_job"]
# after_job = ["za_local.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"za_local.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

