<template>
	<div class="pa-4">

		<!-- Header -->
		<div class="d-flex justify-space-between align-center mb-4">

			<div>

				<div class="text-h5 font-weight-bold">
					Sales Report List
				</div>

				<div class="text-caption text-grey">
					Daily Sales Invoice Summary
				</div>

			</div>

			<v-btn
				color="primary"
				prepend-icon="mdi-refresh"
				@click="fetchReport"
				:loading="loading"
			>
				Refresh
			</v-btn>

		</div>

		<!-- Filters -->
		<v-card
			class="pa-4 mb-4"
			variant="outlined"
		>

			<v-row dense>

				<v-col cols="12" md="4">

					<v-text-field
						v-model="fromDate"
						label="From Date"
						type="date"
						variant="outlined"
						density="compact"
						hide-details
					/>

				</v-col>

				<v-col cols="12" md="4">

					<v-text-field
						v-model="toDate"
						label="To Date"
						type="date"
						variant="outlined"
						density="compact"
						hide-details
					/>

				</v-col>

				<v-col cols="12" md="4">

					<v-btn
						block
						height="40"
						color="primary"
						@click="fetchReport"
						:loading="loading"
					>
						Fetch Report
					</v-btn>

				</v-col>

			</v-row>

		</v-card>

		<!-- Table -->
		<v-card variant="outlined">

			<v-table density="comfortable">

				<thead>

					<tr>
						<th>Date</th>
						<th>Invoice</th>
						<th>Customer</th>
						<th class="text-right">
							Total Qty
						</th>
						<th class="text-right">
							Grand Total
						</th>
						<th class="text-center">
							Action
						</th>
					</tr>

				</thead>

				<tbody>

					<tr
						v-for="(row, i) in items"
						:key="i"
					>

						<td>
							{{ formatDate(row.date) }}
						</td>

						<td>
							{{ row.invoice }}
						</td>

						<td>
							{{ row.customer }}
						</td>

						<td class="text-right">
							{{ Number(row.total_qty || 0) }}
						</td>

						<td class="text-right font-weight-bold">
							{{ currency(row.grand_total) }}
						</td>

						<td class="text-center">
							<v-btn
								color="error"
								size="small"
								variant="tonal"
								icon="mdi-delete"
								:loading="deletingInvoice === row.invoice"
								@click="deleteInvoice(row.invoice)"
							/>
						</td>

					</tr>

					<!-- Totals -->
					<tr
						v-if="items.length"
						class="bg-grey-lighten-4 font-weight-bold"
					>

						<td
							colspan="3"
							class="text-right"
						>
							TOTALS
						</td>

						<td class="text-right">
							{{ Number(totalQty) }}
						</td>

						<td class="text-right">
							{{ currency(totalGrand) }}
						</td>

						<td />

					</tr>

					<!-- Empty State -->
					<tr
						v-if="!loading && items.length === 0"
					>

						<td
							colspan="6"
							class="text-center py-6 text-grey"
						>
							No data found
						</td>

					</tr>

				</tbody>

			</v-table>

		</v-card>

	</div>
</template>

<script setup>
import {
	ref,
	computed,
	onMounted,
} from "vue";

// Today's date autofill
const today = new Date()
	.toISOString()
	.slice(0, 10);

// Filters
const fromDate = ref(today);

const toDate = ref(today);

// State
const loading = ref(false);

const items = ref([]);

const deletingInvoice = ref(null);

// Currency formatter
function currency(value) {

	const num = Number(value || 0);

	return "₹ " + num.toLocaleString(
		"en-IN",
		{
			minimumFractionDigits:
				num % 1 === 0 ? 0 : 2,

			maximumFractionDigits: 2,
		}
	);
}

// Date formatter
function formatDate(date) {

	if (!date) return "";

	const [y, m, d] =
		date.split("-");

	return `${d}-${m}-${y}`;
}

// Totals
const totalQty = computed(() => {

	return items.value.reduce(
		(sum, row) =>
			sum + Number(row.total_qty || 0),
		0
	);
});

const totalGrand = computed(() => {

	return items.value.reduce(
		(sum, row) =>
			sum + Number(row.grand_total || 0),
		0
	);
});

// Delete invoice
async function deleteInvoice(invoice) {

	const confirmed = confirm(
		"Delete invoice " + invoice + " ?"
	);

	if (!confirmed) return;

	deletingInvoice.value = invoice;

	try {

		await frappe.call({
			method:
				"custom_app.custom_app.api.delete_sales_invoice",
			args: {
				invoice_name: invoice,
			},
		});

		frappe.show_alert({
			message: "Invoice " + invoice + " deleted successfully",
			indicator: "green",
		});

		// Remove from local list instantly
		items.value = items.value.filter(
			(row) => row.invoice !== invoice
		);

	} catch (err) {

		frappe.show_alert({
			message: "Delete failed",
			indicator: "red",
		});

		console.error(err);

	} finally {

		deletingInvoice.value = null;
	}
}

// Fetch report
async function fetchReport() {

	loading.value = true;

	try {

		const response =
			await frappe.call({

				method:
					"frappe.desk.query_report.run",

				args: {

					report_name:
						"sales report list",

					filters: {

						from_date:
							fromDate.value,

						to_date:
							toDate.value,
					},

					ignore_prepared_report:
						false,

					are_default_filters:
						true,
				},
			});

		const result =
			response.message.result || [];

		items.value = result;

	} catch (error) {

		console.error(error);

		frappe.show_alert({
			message: "Failed to fetch report",
			indicator: "red",
		});

	} finally {

		loading.value = false;
	}
}

// Initial fetch
onMounted(() => {

	fetchReport();
});
</script>