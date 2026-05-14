<template>
	<div class="gst-report-root pa-4">

		<!-- ── Screen: Header ─────────────────────────────────────── -->
		<div class="d-flex align-center justify-space-between mb-4 no-print">
			<div>
				<div class="text-h5 font-weight-bold">GST Sales Report</div>
				<div class="text-caption text-grey-darken-1">Items with GST applicable · 1% GST</div>
			</div>
			<div class="d-flex gap-2">
				<v-btn
					variant="outlined"
					prepend-icon="mdi-refresh" 
					@click="resetReport"  
					:disabled="loading"
				>Reset</v-btn>
				<v-btn
					color="primary"
					prepend-icon="mdi-printer"
					@click="printReport"
					:disabled="!items.length"
				>Print for CA</v-btn>
			</div>
		</div>

		<!-- ── Screen: Filter Panel ────────────────────────────────── -->
		<v-card class="mb-4 pa-4 no-print" variant="outlined">
			<v-row align="center" dense>
				<v-col cols="12" sm="4">
					<v-text-field
						v-model="fromDate"
						label="From Date"
						type="date"
						variant="outlined"
						density="compact"
						hide-details
					/>
				</v-col>
				<v-col cols="12" sm="4">
					<v-text-field
						v-model="toDate"
						label="To Date"
						type="date"
						variant="outlined"
						density="compact"
						hide-details
					/>
				</v-col>
				<v-col cols="12" sm="4">
					<v-btn
						color="primary"
						@click="fetchReport"
						:loading="loading"
						block
						height="40"
					>Fetch GST Sales</v-btn>
				</v-col>
			</v-row>
		</v-card>

		<!-- ── Screen: Summary Cards ───────────────────────────────── -->
		<v-row class="mb-4 no-print" v-if="items.length">
			<v-col cols="6" md="3">
				<v-card variant="outlined" class="pa-3 text-center">
					<div class="text-caption text-grey">Taxable Items</div>
					<div class="text-h6 font-weight-bold">{{ items.length }}</div>
				</v-card>
			</v-col>
			<v-col cols="6" md="3">
				<v-card variant="outlined" class="pa-3 text-center">
					<div class="text-caption text-grey">Total Invoices</div>
					<div class="text-h6 font-weight-bold">{{ uniqueInvoiceCount }}</div>
				</v-card>
			</v-col>
			<v-col cols="6" md="3">
				<v-card variant="outlined" class="pa-3 text-center">
					<div class="text-caption text-grey">Taxable Amount</div>
					<div class="text-h6 font-weight-bold">{{ fmt(summary.total_taxable) }}</div>
				</v-card>
			</v-col>
			<v-col cols="6" md="3">
				<v-card variant="outlined" class="pa-3 text-center">
					<div class="text-caption text-grey">GST Collected (1%)</div>
					<div class="text-h6 font-weight-bold text-orange-darken-2">{{ fmt(summary.total_gst) }}</div>
				</v-card>
			</v-col>
		</v-row> 

		<!-- ── Screen: Data Table ──────────────────────────────────── -->
		<v-card variant="outlined" class="no-print" v-if="items.length">
			<v-table density="compact">
				<thead>
					<tr>
						<th>#</th>
						<th>Date</th>
						<!-- <th>Invoice</th> -->
						<th>Customer</th>
						<th>Item</th>
						<th class="text-right">Qty</th>
						<th class="text-right">Rate (₹)</th>
						<th class="text-right">Taxable Amt (₹)</th>
						<th class="text-right">GST 1% (₹)</th>
						<th class="text-right">Total (₹)</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, i) in items" :key="i">
						<td class="text-grey">{{ i + 1 }}</td>
						<td>{{ fmtDate(row.date) }}</td>
						<!-- <td class="font-weight-medium" style="font-size:12px">{{ row.invoice }}</td> -->
						<td>{{ row.customer }}</td>
						<td class="font-weight-medium">{{ row.item }}</td>
						<td class="text-right">{{ row.qty }}</td>
						<td class="text-right">{{ fmt(row.rate) }}</td>
						<td class="text-right">{{ fmt(row.taxable_amount) }}</td>
						<td class="text-right text-orange-darken-2 font-weight-medium">{{ fmt(row.gst_amount) }}</td>
						<td class="text-right font-weight-bold">{{ fmt(row.grand_total) }}</td>
					</tr>
					<!-- Totals row -->
					<tr class="bg-grey-lighten-4 font-weight-bold">
						<!-- <td colspan="7" class="text-right">TOTALS</td> -->
						 <td colspan="6" class="text-right">TOTALS</td>
						<td class="text-right">{{ fmt(summary.total_taxable) }}</td>
						<td class="text-right text-orange-darken-2">{{ fmt(summary.total_gst) }}</td>
						<td class="text-right text-green-darken-2">{{ fmt(summary.total_grand) }}</td>
					</tr>
				</tbody>
			</v-table>
		</v-card>

		<!-- ── Empty state ─────────────────────────────────────────── -->
		<div v-if="!loading && searched && !items.length" class="text-center pa-12 text-grey no-print">
			<v-icon size="64" class="mb-3">mdi-file-search-outline</v-icon>
			<div class="text-h6">No GST-applicable items found</div>
			<div class="text-body-2 mt-1">Only items with a tax template are included in this report.</div>
		</div>

		<!-- ══════════════════════════════════════════════════════════
		     PRINT LAYOUT — visible only on print
		     ══════════════════════════════════════════════════════════ -->
		<div class="print-only" v-if="items.length">

			<!-- Cover / Title -->
			<div class="ca-header">
				<div class="ca-company">{{ summary.company || 'Your Company' }}</div>
				<div class="ca-title">GST SALES REPORT</div>
				<div class="ca-subtitle">Statement of Taxable Sales with 1% GST</div>
				<div class="ca-period">Period: {{ fmtDate(fromDate) }} &nbsp;to&nbsp; {{ fmtDate(toDate) }}</div>
				<div class="ca-generated">Generated on: {{ todayStr }}</div>
			</div>

			<div class="ca-divider"></div>

			<!-- Summary Box -->
			<div class="ca-summary-box">
				<table class="ca-summary-table">
					<tr>
						<td>Total Taxable Invoices</td>
						<td>{{ uniqueInvoiceCount }}</td>
						<td>Total Line Items</td>
						<td>{{ items.length }}</td>
					</tr>
					<tr>
						<td>Net Taxable Amount</td>
						<td>{{ fmt(summary.total_taxable) }}</td>
						<td>GST Collected @ 1%</td>
						<td class="gst-highlight">{{ fmt(summary.total_gst) }}</td>
					</tr>
					<tr class="grand-row">
						<td colspan="2"><strong>Grand Total (Incl. GST)</strong></td>
						<td colspan="2" class="grand-val"><strong>{{ fmt(summary.total_grand) }}</strong></td>
					</tr>
				</table>
			</div>

			<div class="ca-divider"></div>

			<!-- GST Breakup for CA -->
			<div class="ca-section-title">GST Breakup</div>
			<table class="ca-gst-breakup">
				<tr>
					<td>CGST @ 0.5%</td>
					<td>{{ fmt(summary.total_gst / 2) }}</td>
					<td>SGST @ 0.5%</td>
					<td>{{ fmt(summary.total_gst / 2) }}</td>
					<td>Total GST @ 1%</td>
					<td class="gst-highlight"><strong>{{ fmt(summary.total_gst) }}</strong></td>
				</tr>
			</table>

			<div class="ca-divider"></div>

			<!-- Detail Table -->
			<div class="ca-section-title">Item-wise Taxable Sales Detail</div>
			<table class="ca-detail-table">
				<thead>
					<tr>
						<th>Sr.</th>
						<th>Date</th>
						<th>Invoice No.</th>
						<th>Customer</th>
						<th>Item Name</th>
						<th>Qty</th>
						<th>Unit</th>
						<th>Rate (₹)</th>
						<th>Net Amt (₹)</th>
						<th>CGST 0.5% (₹)</th>
						<th>SGST 0.5% (₹)</th>
						<th>GST Total (₹)</th>
						<th>Grand Total (₹)</th>
					</tr>
				</thead>
				<tbody>
					<template v-for="(invoiceGroup, invName) in groupedByInvoice" :key="invName">
						<tr v-for="(row, ri) in invoiceGroup" :key="ri" :class="ri === 0 ? 'inv-first-row' : 'inv-cont-row'">
							<td>{{ itemIndex(invName, ri) }}</td>
							<td>{{ ri === 0 ? fmtDate(row.date) : '' }}</td>
							<td>{{ ri === 0 ? row.invoice : '' }}</td>
							<td>{{ ri === 0 ? row.customer : '' }}</td>
							<td class="item-name">{{ row.item }}</td>
							<td class="text-right">{{ row.qty }}</td>
							<td>{{ row.uom }}</td>
							<td class="text-right">{{ fmt(row.rate) }}</td>
							<td class="text-right">{{ fmt(row.taxable_amount) }}</td>
							<td class="text-right">{{ fmt(row.gst_amount / 2) }}</td>
							<td class="text-right">{{ fmt(row.gst_amount / 2) }}</td>
							<td class="text-right gst-col">{{ fmt(row.gst_amount) }}</td>
							<td class="text-right total-col">{{ fmt(row.grand_total) }}</td>
						</tr>
					</template>

					<!-- Grand Totals Row -->
					<tr class="ca-totals-row">
						<td colspan="8" class="text-right"><strong>GRAND TOTALS</strong></td>
						<td class="text-right"><strong>{{ fmt(summary.total_taxable) }}</strong></td>
						<td class="text-right"><strong>{{ fmt(summary.total_gst / 2) }}</strong></td>
						<td class="text-right"><strong>{{ fmt(summary.total_gst / 2) }}</strong></td>
						<td class="text-right gst-col"><strong>{{ fmt(summary.total_gst) }}</strong></td>
						<td class="text-right total-col"><strong>{{ fmt(summary.total_grand) }}</strong></td>
					</tr>
				</tbody>
			</table>

			<div class="ca-divider" style="margin-top:32px"></div>

			<!-- Signature Section -->
			<div class="ca-signatures">
				<div class="sig-block">
					<div class="sig-line"></div>
					<div class="sig-label">Prepared By</div>
				</div>
				<div class="sig-block">
					<div class="sig-line"></div>
					<div class="sig-label">Authorised Signatory</div>
				</div>
				<div class="sig-block">
					<div class="sig-line"></div>
					<div class="sig-label">Chartered Accountant</div>
				</div>
			</div>

			<div class="ca-footer">
				This is a computer-generated GST Sales Report. All figures are in Indian Rupees (₹).
				GST calculated at a flat rate of 1% on net taxable amount.
			</div>
		</div>

	</div>
</template>

<script setup>
import { ref, computed } from "vue";

// ── Date helpers ────────────────────────────────────────────────
const pad = (n) => String(n).padStart(2, "0");
const localDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

const today = new Date();
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);

const fromDate = ref(localDate(firstDay));
const toDate   = ref(localDate(today));
const loading  = ref(false);
const searched = ref(false);

const items   = ref([]);
const summary = ref({ total_taxable: 0, total_gst: 0, total_grand: 0, company: "" });

// ── Computed ────────────────────────────────────────────────────
const uniqueInvoiceCount = computed(() => {
	return new Set(items.value.map((r) => r.invoice)).size;
});

const groupedByInvoice = computed(() => {
	const groups = {};
	for (const row of items.value) {
		if (!groups[row.invoice]) groups[row.invoice] = [];
		groups[row.invoice].push(row);
	}
	return groups;
});

const todayStr = computed(() =>
	today.toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" })
);

// ── Helpers ─────────────────────────────────────────────────────
function fmt(n) {
	return "₹" + parseFloat(n || 0).toLocaleString("en-IN", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
}

function fmtDate(dateStr) {
	if (!dateStr) return "";
	const [y, m, d] = dateStr.split("-");
	return `${d}/${m}/${y}`;
}

// Running counter across invoice groups for Sr. column
function itemIndex(invoiceName, rowIndex) {
	let count = 0;
	for (const [invName, rows] of Object.entries(groupedByInvoice.value)) {
		if (invName === invoiceName) return count + rowIndex + 1;
		count += rows.length;
	}
	return rowIndex + 1;
}

// ── Data Fetch ───────────────────────────────────────────────────
async function fetchReport() {
	if (!fromDate.value || !toDate.value) {
		frappe?.show_alert?.({ message: "Please select both dates.", indicator: "orange" });
		return;
	}

	loading.value = true;
	searched.value = true;
	items.value = [];
	summary.value = { total_taxable: 0, total_gst: 0, total_grand: 0, company: "" };


try {
	const filters = {
		from_date: fromDate.value,
		to_date: toDate.value,
		company: "City Trader",
	};

	const res = await frappe.call({
		method: "frappe.desk.query_report.run",
		args: {
			report_name: "test gst",
			filters: filters,
			ignore_prepared_report: false,
			are_default_filters: true,
		},
	});

	const data = res.message || {};

	// Full rows from ERP report
	const rows = data.result || [];


	// GST-only rows
	items.value = rows;

	// Summary calculations
	// summary.value = {
	// 	total_net: items.value.reduce(
	// 		(sum, row) => sum + parseFloat(row.net_total || 0),
	// 		0
	// 	),

	// 	total_gst: items.value.reduce(
	// 		(sum, row) => sum + parseFloat(row["gst_1%___ct"] || 0),
	// 		0
	// 	),

	// 	total_grand: items.value.reduce(
	// 		(sum, row) => sum + parseFloat(row.grand_total || 0),
	// 		0
	// 	),

	// 	company: "City Trader",
	// };


summary.value = {
	total_taxable: items.value.reduce(
	(sum, row) => sum + parseFloat(row.taxable_amount || 0),
	0
),

	total_gst: items.value.reduce(
		(sum, row) => sum + parseFloat(row.gst_amount || 0),
		0
	),

	total_grand: items.value.reduce(
		(sum, row) => sum + parseFloat(row.grand_total || 0),
		0
	),

	company: "City Trader",
};



	if (!items.value.length) {
		frappe?.show_alert?.({
			message: "No GST-applicable items found for this period.",
			indicator: "blue",
		});
	}

} catch (err) {
	console.error("GST Report fetch error:", err);

	frappe?.show_alert?.({
		message: "Failed to fetch report data.",
		indicator: "red",
	});

} finally {
	loading.value = false;
}
 
}

function resetReport() {
	items.value   = [];
	summary.value = { total_taxable: 0, total_gst: 0, total_grand: 0, company: "" };
	searched.value = false;
}

function printReport() {
	window.print();
}
</script>

<style scoped>
/* ── Hide print section on screen ─────────────────────────────── */
.print-only {
	display: none;
}

/* ══════════════════════════════════════════════════════════════
   PRINT STYLES
   ══════════════════════════════════════════════════════════════ */
@media print {
	/* Hide screen UI */
	.no-print {
		display: none !important;
	}

	/* Show print section */
	.print-only {
		display: block !important;
		font-family: "Times New Roman", serif;
		color: #000;
		font-size: 11pt;
	}

	/* Reset outer padding for print */
	.gst-report-root {
		padding: 0 !important;
	}

	/* ── CA Header ── */
	.ca-header {
		text-align: center;
		margin-bottom: 12pt;
	}
	.ca-company {
		font-size: 15pt;
		font-weight: bold;
		text-transform: uppercase;
		letter-spacing: 1px;
	}
	.ca-title {
		font-size: 14pt;
		font-weight: bold;
		margin-top: 6pt;
		text-decoration: underline;
		letter-spacing: 2px;
	}
	.ca-subtitle {
		font-size: 10pt;
		color: #444;
		margin-top: 4pt;
	}
	.ca-period {
		font-size: 11pt;
		margin-top: 8pt;
		font-weight: bold;
	}
	.ca-generated {
		font-size: 9pt;
		color: #666;
		margin-top: 2pt;
	}

	/* ── Divider ── */
	.ca-divider {
		border-top: 2px solid #000;
		margin: 10pt 0;
	}

	/* ── Summary Box ── */
	.ca-summary-box {
		margin: 8pt 0;
	}
	.ca-summary-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 11pt;
	}
	.ca-summary-table td {
		padding: 4pt 8pt;
		border: 1px solid #888;
	}
	.ca-summary-table .grand-row td {
		background: #f0f0f0;
		font-size: 12pt;
	}
	.ca-summary-table .grand-val {
		text-align: right;
	}
	.gst-highlight {
		font-weight: bold;
	}

	/* ── GST Breakup ── */
	.ca-gst-breakup {
		width: 100%;
		border-collapse: collapse;
		font-size: 10pt;
		margin-bottom: 6pt;
	}
	.ca-gst-breakup td {
		padding: 3pt 8pt;
		border: 1px solid #aaa;
	}

	/* ── Section Title ── */
	.ca-section-title {
		font-size: 12pt;
		font-weight: bold;
		margin-bottom: 6pt;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	/* ── Detail Table ── */
	.ca-detail-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 9pt;
	}
	.ca-detail-table th {
		background: #e0e0e0;
		border: 1px solid #555;
		padding: 4pt 4pt;
		text-align: center;
		font-weight: bold;
		font-size: 8.5pt;
	}
	.ca-detail-table td {
		border: 1px solid #aaa;
		padding: 3pt 4pt;
		vertical-align: top;
	}
	.ca-detail-table .text-right {
		text-align: right;
	}
	.ca-detail-table .item-name {
		font-weight: 500;
	}
	.ca-detail-table .gst-col {
		background: #fffbe6;
	}
	.ca-detail-table .total-col {
		background: #f0fff0;
		font-weight: bold;
	}
	.ca-detail-table .inv-first-row {
		border-top: 1.5px solid #444;
	}
	.ca-totals-row td {
		background: #e8e8e8;
		font-size: 10pt;
		border-top: 2px solid #000;
	}

	/* ── Signatures ── */
	.ca-signatures {
		display: flex;
		justify-content: space-around;
		margin-top: 32pt;
	}
	.sig-block {
		text-align: center;
		width: 160pt;
	}
	.sig-line {
		border-top: 1px solid #000;
		margin-bottom: 4pt;
	}
	.sig-label {
		font-size: 9pt;
		color: #555;
	}

	/* ── Footer ── */
	.ca-footer {
		margin-top: 16pt;
		font-size: 8pt;
		color: #777;
		text-align: center;
		border-top: 1px solid #ccc;
		padding-top: 6pt;
	}

	/* Page break control */
	.ca-detail-table { page-break-inside: auto; }
	.ca-detail-table tr { page-break-inside: avoid; }
}
</style>
