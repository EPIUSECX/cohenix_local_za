(function () {
	function as_list(value) {
		if (!value) return [];
		if (Array.isArray(value)) return value.filter((item) => item !== undefined && item !== null && item !== "");
		return [value];
	}

	function escape_html(value) {
		return frappe.utils.escape_html(String(value ?? ""));
	}

	function render_details(details) {
		const rows = Array.isArray(details)
			? details
			: Object.entries(details || {}).map(([label, value]) => ({ label, value }));

		if (!rows.length) return "";

		return `
			<table class="table table-bordered" style="margin: 12px 0 0;">
				<tbody>
					${rows
						.map((row) => {
							const value = Array.isArray(row.value) ? row.value.join(", ") : row.value;
							const display_value = value === undefined || value === null || value === "" ? __("Not set") : value;
							return `
								<tr>
									<td style="width: 36%; font-weight: 600;">${escape_html(row.label)}</td>
									<td>${escape_html(display_value)}</td>
								</tr>
							`;
						})
						.join("")}
				</tbody>
			</table>
		`;
	}

	function render_list(title, items) {
		const rows = as_list(items);
		if (!rows.length) return "";

		return `
			<div style="margin-top: 14px;">
				<div style="font-weight: 600; margin-bottom: 6px;">${escape_html(title)}</div>
				<ul style="margin-bottom: 0; padding-left: 20px;">
					${rows.map((item) => `<li>${escape_html(item)}</li>`).join("")}
				</ul>
			</div>
		`;
	}

	function has_feedback_shape(value) {
		return Boolean(
			value &&
				typeof value === "object" &&
				(value.title || value.details || value.next_steps || value.warnings || value.indicator),
		);
	}

	function normalise_feedback(response) {
		if (!response) return null;
		if (has_feedback_shape(response)) return response;
		if (typeof response === "string") return { message: response };
		if (response.message && has_feedback_shape(response.message)) return response.message;
		if (typeof response.message === "string") return { message: response.message };
		return response;
	}

	function show_action_feedback(response, fallback_title) {
		const result = normalise_feedback(response);
		if (!result) return;

		const warnings = as_list(result.warnings);
		const indicator = result.indicator || (warnings.length ? "orange" : "green");
		const title = result.title || fallback_title || __("ZA Local");
		const message = result.message ? `<p>${escape_html(result.message)}</p>` : "";

		frappe.msgprint({
			title: __(title),
			indicator,
			wide: true,
			message: `
				${message}
				${render_details(result.details)}
				${render_list(__("Warnings"), warnings)}
				${render_list(__("Next Steps"), result.next_steps)}
			`,
		});
	}

	window.za_local = window.za_local || {};
	window.za_local.show_action_feedback = show_action_feedback;
})();
