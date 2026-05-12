<template>
	<td :colspan="colspan" class="ma-0 pa-0 posa-expanded-row-cell">
		<div
			v-if="isExpanded"
			class="posa-expanded-content responsive-expanded-content"
			:class="expandedContentClasses"
		>
			<div class="posa-item-details-form">

				<!-- Basic Information: QTY + UOM only -->
				<div class="posa-form-section">
					<div class="posa-section-header">
						<v-icon size="small" class="section-icon">mdi-information-outline</v-icon>
						<span class="posa-section-title">{{ __("Item Details") }}</span>
					</div>
					<div class="posa-form-row">
						<div class="posa-form-field">
							<v-text-field
								density="compact"
								variant="outlined"
								color="primary"
								:label="frappe._('Item Code')"
								class="pos-themed-input"
								hide-details
								v-model="item.item_code"
								disabled
								prepend-inner-icon="mdi-barcode"
							></v-text-field>
						</div>
						<div class="posa-form-field">
							<v-text-field
								density="compact"
								variant="outlined"
								color="primary"
								:label="frappe._('QTY')"
								class="pos-themed-input"
								hide-details
								:model-value="formatFloat(item.qty, hide_qty_decimals ? 0 : undefined)"
								@change="onQtyChange(item, $event)"
								:rules="[isNumber]"
								:disabled="!!item.posa_is_replace"
								prepend-inner-icon="mdi-numeric"
							></v-text-field>
						</div>
						<div class="posa-form-field">
							<v-select
								density="compact"
								class="pos-themed-input"
								:label="frappe._('UOM')"
								v-model="item.uom"
								:items="item.item_uoms"
								variant="outlined"
								item-title="uom"
								item-value="uom"
								hide-details
								@update:model-value="calcUom(item, $event)"
								:disabled="!!item.posa_is_replace || (isReturnInvoice && invoice_doc.return_against)"
								prepend-inner-icon="mdi-weight"
							></v-select>
						</div>
					</div>
				</div>

				<!-- Pricing: Rate + Discount % only -->
				<div class="posa-form-section">
					<div class="posa-section-header">
						<v-icon size="small" class="section-icon">mdi-currency-rupee</v-icon>
						<span class="posa-section-title">{{ __("Price") }}</span>
					</div>
					<div class="posa-form-row">
						<div class="posa-form-field">
							<v-text-field
								density="compact"
								variant="outlined"
								color="primary"
								:label="frappe._('Rate')"
								class="pos-themed-input"
								hide-details
								:model-value="formatCurrency(item.rate)"
								@change="[
									setFormatedCurrency(item, 'rate', null, false, $event),
									calcPrices(item, $event.target.value, $event),
								]"
								:disabled="!pos_profile.posa_allow_user_to_edit_rate || !!item.posa_is_replace"
								prepend-inner-icon="mdi-currency-rupee"
							></v-text-field>
						</div>
						<div class="posa-form-field">
							<v-text-field
								density="compact"
								variant="outlined"
								color="primary"
								:label="frappe._('Discount %')"
								class="pos-themed-input"
								hide-details
								:model-value="formatFloat(Math.abs(item.discount_percentage || 0))"
								@change="[
									setFormatedCurrency(item, 'discount_percentage', null, false, $event),
									calcPrices(item, $event.target.value, $event),
								]"
								:disabled="!pos_profile.posa_allow_user_to_edit_item_discount || !!item.posa_is_replace || !!item.posa_offer_applied"
								prepend-inner-icon="mdi-percent"
							></v-text-field>
						</div>
						<div class="posa-form-field">
							<v-text-field
								density="compact"
								variant="outlined"
								color="primary"
								:label="frappe._('Total')"
								class="pos-themed-input"
								hide-details
								:model-value="formatCurrency(item.qty * item.rate)"
								disabled
								prepend-inner-icon="mdi-calculator"
							></v-text-field>
						</div>
					</div>
				</div>

				<!-- Serial Numbers (only if needed) -->
				<div class="posa-form-section" v-if="item.has_serial_no || item.serial_no">
					<div class="posa-section-header">
						<v-icon size="small" class="section-icon">mdi-barcode-scan</v-icon>
						<span class="posa-section-title">{{ __("Serial Numbers") }}</span>
					</div>
					<div class="posa-form-row">
						<div class="posa-form-field full-width">
							<v-autocomplete
								v-model="item.serial_no_selected"
								:items="getSerialOptions(item)"
								item-title="serial_no"
								item-value="serial_no"
								variant="outlined"
								density="compact"
								chips
								color="primary"
								class="pos-themed-input"
								:label="frappe._('Serial No')"
								multiple
								@update:model-value="setSerialNo(item)"
								prepend-inner-icon="mdi-barcode"
							></v-autocomplete>
						</div>
					</div>
				</div>

				<!-- Batch (only if needed) -->
				<div class="posa-form-section" v-if="item.has_batch_no || item.batch_no">
					<div class="posa-section-header">
						<v-icon size="small" class="section-icon">mdi-package-variant-closed</v-icon>
						<span class="posa-section-title">{{ __("Batch") }}</span>
					</div>
					<div class="posa-form-row">
						<div class="posa-form-field">
							<v-autocomplete
								v-model="item.batch_no"
								:items="getBatchOptions(item)"
								item-title="batch_no"
								variant="outlined"
								density="compact"
								color="primary"
								class="pos-themed-input"
								:label="frappe._('Batch No')"
								@update:model-value="setBatchQty(item, $event)"
								hide-details
								prepend-inner-icon="mdi-package-variant-closed"
							></v-autocomplete>
						</div>
					</div>
				</div>

			</div>
		</div>
		<div v-else class="expanded-placeholder"></div>
	</td>
</template>

<script setup lang="ts">
import { getDisplayableBatchOptions } from "../../../composables/pos/shared/useBatchSerial";
import type { CartItem, POSProfile, InvoiceDoc } from "../../../types/models";

interface Props {
	item: CartItem | any;
	isExpanded: boolean;
	colspan: number;
	pos_profile: POSProfile | any;
	invoiceType?: string;
	isReturnInvoice?: boolean;
	invoice_doc?: InvoiceDoc | any;
	hide_qty_decimals: boolean;
	expandedContentClasses: any;
	formatFloat: (_val: any, _precision?: number) => string;
	formatCurrency: (_val: any, _precision?: number) => string;
	currencySymbol: (_currency?: string) => string;
	isNumber: (_val: any) => boolean | string;
	setFormatedCurrency: (_item: any, _field: string, _value: any, _force?: boolean, _event?: any) => void;
	calcPrices: (_item: any, _value: any, _event?: any) => void;
	calcUom: (_item: any, _uom: string) => void;
	changePriceListRate: (_item: any) => void;
	getSerialOptions: (_item: any) => any[];
	setSerialNo: (_item: any) => void;
	setBatchQty: (_item: any, _event: any) => void;
	validateDueDate: (_item: any) => void;
}

defineProps<Props>();

const emit = defineEmits<{
	"qty-change": [item: CartItem, event: any];
}>();

const __ = (window as any).__ || ((s: string) => s);
const frappe = (window as any).frappe || { _: (s: string) => s };

const onQtyChange = (item: CartItem, event: any) => {
	emit("qty-change", item, event);
};

const getRaw = (item: any) => item?.raw || {};
const getBatchOptions = (item: any) => getDisplayableBatchOptions(item?.batch_no_data);
</script>

<style scoped>
.expanded-placeholder { min-height: 4px; }
</style>
