"""Secure FNB Online Banking Enterprise payroll-payment export."""

import csv
import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime
from frappe.utils.file_manager import save_file

ALLOWED_EXPORT_ROLES = ("HR Manager", "Accounts Manager", "System Manager")
FNB_FORMAT = "FNB OBE CSV"
FNB_VERSION = "BInSol - U ver 1.00"
FNB_COLUMNS = (
	"RECIPIENT NAME", "RECIPIENT ACCOUNT", "RECIPIENT ACCOUNT TYPE", "BRANCHCODE",
	"AMOUNT", "OWN REFERENCE", "RECIPIENT REFERENCE", "EMAIL 1 NOTIFY",
	"EMAIL 1 ADDRESS", "EMAIL 1 SUBJECT", "EMAIL 2 NOTIFY", "EMAIL 2 ADDRESS",
	"EMAIL 2 SUBJECT", "EMAIL 3 NOTIFY", "EMAIL 3 ADDRESS", "EMAIL 3 SUBJECT",
	"EMAIL 4 NOTIFY", "EMAIL 4 ADDRESS", "EMAIL 4 SUBJECT", "EMAIL 5 NOTIFY",
	"EMAIL 5 ADDRESS", "EMAIL 5 SUBJECT", "FAX 1 NOTIFY", "FAX 1 CODE",
	"FAX 1 NUMBER", "FAX 1 SUBJECT", "FAX 2 NOTIFY", "FAX 2 CODE",
	"FAX 2 NUMBER", "FAX 2 SUBJECT", "SMS 1 NOTIFY", "SMS 1 CODE",
	"SMS 1 NUMBER", "SMS 2 NOTIFY", "SMS 2 CODE", "SMS 2 NUMBER",
)

ACCOUNT_TYPE_CODES = {
	"current": "1", "current account": "1", "cheque": "1", "cheque account": "1",
	"checking": "1", "checking account": "1", "savings": "2", "savings account": "2",
	"transmission": "3", "transmission account": "3", "bond": "4", "bond account": "4",
	"subscription share": "6", "subscription share account": "6",
	"fnb card account": "F", "wesbank": "W",
}
DISABLED_FORMATS = {"absa", "nedbank", "standard bank", "standard_bank"}


@dataclass(frozen=True)
class PaymentRecipient:
	salary_slip: str
	employee: str
	recipient_name: str
	bank_account: str
	account_number: str
	account_type_code: str
	branch_code: str
	amount: str
	recipient_reference: str


@dataclass(frozen=True)
class PaymentBatchSnapshot:
	batch_name: str
	payroll_entry: str
	company: str
	payment_date: str
	company_bank_account: str
	own_account_number: str
	recipients: tuple[PaymentRecipient, ...]
	source_hash: str

	@property
	def total_amount(self) -> Decimal:
		return sum((Decimal(row.amount) for row in self.recipients), Decimal("0.00"))


def normalize_bank_format(bank_format: str | None) -> str:
	value = (bank_format or "").strip()
	if value.casefold() in {"fnb", FNB_FORMAT.casefold()}:
		return FNB_FORMAT
	if value.casefold() in DISABLED_FORMATS:
		frappe.throw(
			_("Automated {0} payroll files are disabled because an exact current official layout has not been onboarded. Contact the bank and complete a controlled file-format onboarding before use.").format(frappe.bold(value)),
			title=_("Manual Bank Onboarding Required"),
		)
	frappe.throw(_("Unsupported bank format: {0}").format(frappe.bold(value or _("Not set"))))


def validate_payment_batch_header(batch) -> tuple[frappe._dict, frappe._dict]:
	"""Validate the submitted payroll and nominated company account."""
	normalize_bank_format(batch.bank_format)
	_validate_action_date(batch.payment_date)

	payroll = frappe.db.get_value(
		"Payroll Entry", batch.payroll_entry,
		["name", "company", "docstatus", "start_date", "end_date"], as_dict=True,
	)
	if not payroll:
		frappe.throw(_("Payroll Entry {0} does not exist.").format(frappe.bold(batch.payroll_entry)))
	if payroll.docstatus != 1:
		frappe.throw(_("Payroll Entry {0} must be submitted before creating a payment batch.").format(frappe.bold(payroll.name)))
	if batch.company != payroll.company:
		frappe.throw(_("Payroll Payment Batch company must match Payroll Entry company {0}.").format(frappe.bold(payroll.company)))

	account = _get_bank_accounts([batch.bank_account]).get(batch.bank_account)
	if not account:
		frappe.throw(_("Company Bank Account {0} does not exist.").format(frappe.bold(batch.bank_account)))
	if account.disabled or not account.is_company_account or account.company != batch.company:
		frappe.throw(_("Bank Account {0} must be an enabled company account for {1}.").format(frappe.bold(account.name), frappe.bold(batch.company)))
	_normalize_digits(account.bank_account_no, _("Company bank account number"), exact_length=11)
	return payroll, account


def build_payment_batch_snapshot(batch) -> PaymentBatchSnapshot:
	"""Build and validate the immutable source snapshot for one payment batch."""
	payroll, company_account = validate_payment_batch_header(batch)
	slips = frappe.get_all(
		"Salary Slip",
		filters={"payroll_entry": batch.payroll_entry, "docstatus": ["<", 2]},
		fields=["name", "employee", "employee_name", "net_pay", "currency", "company", "docstatus"],
		order_by="employee asc, name asc",
	)
	if not slips:
		frappe.throw(_("No Salary Slips were found for Payroll Entry {0}.").format(frappe.bold(batch.payroll_entry)))
	drafts = [row.name for row in slips if row.docstatus == 0]
	if drafts:
		frappe.throw(_("Submit all Salary Slips before creating the payment file. Draft slips: {0}").format(", ".join(drafts)))

	employees = _get_employees([row.employee for row in slips])
	account_names = [batch.bank_account]
	for slip in slips:
		employee = employees.get(slip.employee)
		if not employee or not employee.za_payroll_payable_bank_account:
			frappe.throw(_("Employee {0} must have a Payroll Payable Bank Account.").format(frappe.bold(slip.employee)))
		account_names.append(employee.za_payroll_payable_bank_account)
	accounts = _get_bank_accounts(account_names)

	recipients = []
	seen_employees = set()
	for slip in slips:
		if slip.employee in seen_employees:
			frappe.throw(_("Payroll Entry {0} contains more than one submitted Salary Slip for employee {1}.").format(frappe.bold(batch.payroll_entry), frappe.bold(slip.employee)))
		seen_employees.add(slip.employee)
		if slip.company != batch.company or slip.currency != "ZAR":
			frappe.throw(_("Salary Slip {0} must belong to {1} and use ZAR.").format(frappe.bold(slip.name), frappe.bold(batch.company)))
		employee = employees[slip.employee]
		bank_account = accounts.get(employee.za_payroll_payable_bank_account)
		recipients.append(_build_recipient(slip, employee, bank_account, payroll.end_date))

	own_account = _normalize_digits(company_account.bank_account_no, _("Company bank account number"), exact_length=11)
	payload = {
		"batch_name": batch.name,
		"payroll_entry": batch.payroll_entry,
		"company": batch.company,
		"payment_date": str(getdate(batch.payment_date)),
		"company_bank_account": batch.bank_account,
		"own_account_number": own_account,
		"recipients": [asdict(row) for row in recipients],
	}
	source_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
	return PaymentBatchSnapshot(
		batch_name=batch.name,
		payroll_entry=batch.payroll_entry,
		company=batch.company,
		payment_date=str(getdate(batch.payment_date)),
		company_bank_account=batch.bank_account,
		own_account_number=own_account,
		recipients=tuple(recipients),
		source_hash=source_hash,
	)


def render_fnb_obe_csv(snapshot: PaymentBatchSnapshot) -> tuple[str, str]:
	"""Render the official 36-column FNB OBE Payments CSV structure."""
	hash_total = calculate_fnb_hash_total(snapshot.own_account_number, [row.account_number for row in snapshot.recipients])
	rows = [
		[FNB_VERSION, *([""] * 35)],
		[getdate(snapshot.payment_date).strftime("%d-%m-%Y"), *([""] * 35)],
		[snapshot.own_account_number, hash_total, *([""] * 34)],
		list(FNB_COLUMNS),
	]
	for recipient in snapshot.recipients:
		rows.append([
			_format_text(recipient.recipient_name, 20, _("Recipient name")), recipient.account_number, recipient.account_type_code,
			recipient.branch_code, recipient.amount, snapshot.batch_name[:20],
			recipient.recipient_reference[:20], *([""] * 29),
		])

	stream = io.StringIO(newline="")
	csv.writer(stream, lineterminator="\r\n").writerows(rows)
	return stream.getvalue(), hash_total


def calculate_fnb_hash_total(own_account: str, recipient_accounts: list[str]) -> str:
	"""Return FNB's right-most 12 digits of the numeric account total."""
	total = int(_normalize_digits(own_account, _("Company bank account number")))
	for account in recipient_accounts:
		total += int(_normalize_digits(account, _("Recipient bank account number")))
	return str(total).zfill(12)[-12:]


@frappe.whitelist(methods=["POST"])
def generate_eft_file(
	payment_batch: str | None = None,
	payroll_entry: str | None = None,
	bank_format: str | None = None,
) -> dict:
	"""Generate or reuse a private FNB OBE file for a submitted payment batch."""
	frappe.only_for(ALLOWED_EXPORT_ROLES)
	if payroll_entry or bank_format:
		frappe.throw(_("Generate EFT files from a submitted Payroll Payment Batch, not directly from a Payroll Entry."))
	if not isinstance(payment_batch, str) or not payment_batch.strip():
		frappe.throw(_("Payroll Payment Batch is required."))
	frappe.has_permission("Payroll Payment Batch", "write", doc=payment_batch, throw=True)
	frappe.db.get_value("Payroll Payment Batch", payment_batch, "name", for_update=True)
	batch = frappe.get_doc("Payroll Payment Batch", payment_batch)
	if batch.docstatus != 1:
		frappe.throw(_("Submit Payroll Payment Batch {0} before generating its EFT file.").format(frappe.bold(payment_batch)))

	snapshot = build_payment_batch_snapshot(batch)
	if batch.eft_source_hash:
		if batch.eft_source_hash != snapshot.source_hash:
			frappe.throw(
				_("Salary Slip or Bank Account data changed after this batch was submitted. Cancel and amend the batch before generating another payment file."),
				title=_("Payment Snapshot Changed"),
			)
		if existing := _get_existing_private_file(batch):
			return {"file_url": existing.file_url, "filename": existing.file_name, "reused": True}

	content, hash_total = render_fnb_obe_csv(snapshot)
	filename = _safe_filename(f"FNB_OBE_{batch.name}_{snapshot.payment_date}.csv")
	file_doc = save_file(filename, content.encode("utf-8"), batch.doctype, batch.name, is_private=1, df="eft_file_path")
	if not file_doc.is_private or file_doc.attached_to_doctype != batch.doctype or file_doc.attached_to_name != batch.name:
		frappe.throw(_("The generated payment file could not be attached privately to this batch."))

	# These are validated, generated audit fields; the row lock prevents duplicate attachments.
	batch.db_set({
		"total_employees": len(snapshot.recipients),
		"total_amount": snapshot.total_amount,
		"eft_source_hash": snapshot.source_hash,
		"fnb_hash_total": hash_total,
		"eft_file_generated": 1,
		"eft_file_path": file_doc.file_url,
		"eft_generated_on": now_datetime(),
	}, notify=True)
	return {"file_url": file_doc.file_url, "filename": file_doc.file_name, "reused": False}


def _build_recipient(slip, employee, account, payroll_end_date) -> PaymentRecipient:
	if not account or account.disabled or account.is_company_account:
		frappe.throw(_("Employee {0} must be linked to an enabled recipient Bank Account.").format(frappe.bold(slip.employee)))
	if account.party_type != "Employee" or account.party != slip.employee:
		frappe.throw(_("Bank Account {0} must be linked to Employee {1}.").format(frappe.bold(account.name), frappe.bold(slip.employee)))
	amount = _format_amount(slip.net_pay, slip.name)
	account_number = _normalize_digits(account.bank_account_no, _("Recipient bank account number"), max_length=20)
	branch_code = _normalize_digits(account.branch_code, _("Recipient branch code"), exact_length=6)
	account_type_code = ACCOUNT_TYPE_CODES.get(_normalized_label(account.account_type))
	if not account_type_code:
		frappe.throw(_("Bank Account {0} has an unsupported Account Type. Use a current/cheque, savings, transmission, bond, subscription share, FNB card, or WesBank account type.").format(frappe.bold(account.name)))
	return PaymentRecipient(
		salary_slip=slip.name, employee=slip.employee,
		recipient_name=(employee.employee_name or slip.employee_name or slip.employee).strip(),
		bank_account=account.name, account_number=account_number,
		account_type_code=account_type_code, branch_code=branch_code, amount=amount,
		recipient_reference=f"Salary {getdate(payroll_end_date).strftime('%Y%m')} {slip.employee}",
	)


def _get_employees(employee_names: list[str]) -> dict[str, frappe._dict]:
	rows = frappe.get_all(
		"Employee", filters={"name": ["in", sorted(set(employee_names))]},
		fields=["name", "employee_name", "za_payroll_payable_bank_account"],
	)
	return {row.name: row for row in rows}


def _get_bank_accounts(account_names: list[str]) -> dict[str, frappe._dict]:
	rows = frappe.get_all(
		"Bank Account", filters={"name": ["in", sorted(set(filter(None, account_names)))]},
		fields=["name", "account_name", "bank", "account_type", "bank_account_no", "branch_code", "disabled", "is_company_account", "company", "party_type", "party"],
	)
	return {row.name: row for row in rows}


def _get_existing_private_file(batch):
	if not batch.eft_file_generated or not batch.eft_file_path:
		return None
	return frappe.db.get_value(
		"File",
		{"file_url": batch.eft_file_path, "is_private": 1, "attached_to_doctype": batch.doctype, "attached_to_name": batch.name, "attached_to_field": "eft_file_path"},
		["name", "file_name", "file_url"], as_dict=True,
	)


def _validate_action_date(value) -> None:
	action_date = getdate(value)
	today = getdate()
	if action_date < today or action_date > add_days(today, 365):
		frappe.throw(_("Payment Date must be today or no more than 365 days in the future."))


def _normalize_digits(value, label: str, *, exact_length: int | None = None, max_length: int | None = None) -> str:
	digits = str(value or "").strip()
	if not digits.isdigit():
		frappe.throw(_("{0} must contain digits only.").format(label))
	if exact_length and len(digits) != exact_length:
		frappe.throw(_("{0} must contain exactly {1} digits.").format(label, exact_length))
	if max_length and len(digits) > max_length:
		frappe.throw(_("{0} cannot exceed {1} digits.").format(label, max_length))
	return digits


def _format_amount(value, salary_slip: str) -> str:
	try:
		amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	except (InvalidOperation, TypeError):
		frappe.throw(_("Salary Slip {0} has an invalid Net Pay amount.").format(frappe.bold(salary_slip)))
	if amount <= 0:
		frappe.throw(_("Salary Slip {0} must have a positive Net Pay amount.").format(frappe.bold(salary_slip)))
	formatted = f"{amount:.2f}"
	if len(formatted) > 11:
		frappe.throw(_("Salary Slip {0} Net Pay exceeds the FNB amount field length.").format(frappe.bold(salary_slip)))
	return formatted


def _normalized_label(value) -> str:
	return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def _format_text(value, max_length: int, label: str) -> str:
	text = re.sub(r"\s+", " ", str(value or "")).strip()
	if not text:
		frappe.throw(_("{0} is required.").format(label))
	if text[0] in "=+@":
		frappe.throw(_("{0} cannot start with a spreadsheet formula character.").format(label))
	return text[:max_length]


def _safe_filename(value: str) -> str:
	return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
