<template>
  <div class="ct-stock-page">
    <!-- Header -->
    <div class="ct-header">
      <div class="ct-header-left">
        <v-icon class="ct-header-icon">mdi-warehouse</v-icon>
        <div>
          <div class="ct-title">Warehouse Stock</div>
          <div class="ct-subtitle">Live stock across Shop & Warehouse</div>
        </div>
      </div>
      <div class="ct-header-right">
        <v-btn icon variant="text" @click="loadData" :loading="loading" size="small">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <div class="ct-last-sync" v-if="lastSync">Updated {{ lastSync }}</div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="ct-cards">
      <div class="ct-card ct-card-shop">
        <div class="ct-card-icon"><v-icon size="28">mdi-storefront</v-icon></div>
        <div class="ct-card-body">
          <div class="ct-card-label">Shop (Stores)</div>
          <div class="ct-card-value">{{ totalShop }}</div>
          <div class="ct-card-sub">total units</div>
        </div>
      </div>
      <div class="ct-card ct-card-home">
        <div class="ct-card-icon"><v-icon size="28">mdi-home</v-icon></div>
        <div class="ct-card-body">
          <div class="ct-card-label">Warehouse (Home)</div>
          <div class="ct-card-value">{{ totalHome }}</div>
          <div class="ct-card-sub">total units</div>
        </div>
      </div>
      <div class="ct-card ct-card-alert">
        <div class="ct-card-icon"><v-icon size="28">mdi-alert-circle</v-icon></div>
        <div class="ct-card-body">
          <div class="ct-card-label">Low Stock Alerts</div>
          <div class="ct-card-value ct-alert-val">{{ lowStockItems.length }}</div>
          <div class="ct-card-sub">items need refill</div>
        </div>
      </div>
      <div class="ct-card ct-card-total">
        <div class="ct-card-icon"><v-icon size="28">mdi-package-variant</v-icon></div>
        <div class="ct-card-body">
          <div class="ct-card-label">Total Items</div>
          <div class="ct-card-value">{{ items.length }}</div>
          <div class="ct-card-sub">active SKUs</div>
        </div>
      </div>
    </div>

    <!-- Low Stock Alert Banner -->
    <div class="ct-alert-banner" v-if="lowStockItems.length > 0">
      <v-icon color="orange" class="mr-2">mdi-alert</v-icon>
      <span><strong>{{ lowStockItems.length }} items</strong> are below minimum shop quantity —
        <span class="ct-alert-link" @click="filterLow = !filterLow">
          {{ filterLow ? 'Show all' : 'Show only low stock' }}
        </span>
      </span>
    </div>

    <!-- Search + Filter -->
    <div class="ct-toolbar">
      <v-text-field
        v-model="search"
        placeholder="Search items..."
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="ct-search"
      />
      <v-select
        v-model="groupFilter"
        :items="['All Groups', ...itemGroups]"
        variant="outlined"
        density="compact"
        hide-details
        class="ct-group-filter"
      />
      <v-btn-toggle v-model="viewMode" density="compact" variant="outlined" mandatory>
        <v-btn value="all" size="small">All</v-btn>
        <v-btn value="low" size="small" color="orange">Low</v-btn>
        <v-btn value="zero" size="small" color="error">Zero</v-btn>
      </v-btn-toggle>
    </div>

    <!-- Stock Table -->
    <div class="ct-table-wrap">
      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :loading="loading"
        density="compact"
        class="ct-table"
        :items-per-page="50"
        hover
      >
        <template #item.shop_qty="{ item }">
          <div class="ct-qty-cell" :class="getShopQtyClass(item)">
            <v-icon size="14" class="mr-1" v-if="item.shop_qty < item.min_qty">mdi-alert-circle</v-icon>
            {{ fmtQty(item.shop_qty) }}
          </div>
        </template>
        <template #item.home_qty="{ item }">
          <div class="ct-qty-cell">{{ fmtQty(item.home_qty) }}</div>
        </template>
        <template #item.total_qty="{ item }">
          <strong>{{ fmtQty(item.shop_qty + item.home_qty) }}</strong>
        </template>
        <template #item.status="{ item }">
          <v-chip
            :color="getStatusColor(item)"
            size="x-small"
            variant="flat"
            class="ct-status-chip"
          >
            {{ getStatus(item) }}
          </v-chip>
        </template>
        <template #item.actions="{ item }">
          <v-btn
            v-if="item.shop_qty < item.min_qty && item.home_qty > 0"
            size="x-small"
            color="primary"
            variant="tonal"
            @click="quickTransfer(item)"
          >
            <v-icon size="14" class="mr-1">mdi-transfer</v-icon>
            Refill
          </v-btn>
        </template>
      </v-data-table>
    </div>

    <!-- Quick Transfer Dialog -->
    <v-dialog v-model="transferDialog" max-width="420">
      <v-card class="ct-dialog">
        <v-card-title class="ct-dialog-title">
          <v-icon class="mr-2" color="primary">mdi-transfer</v-icon>
          Quick Refill
        </v-card-title>
        <v-card-text>
          <div class="ct-transfer-item-name">{{ transferItem?.item_name }}</div>
          <div class="ct-transfer-meta">
            Shop: {{ transferItem?.shop_qty }} | Warehouse: {{ transferItem?.home_qty }} | Min: {{ transferItem?.min_qty }}
          </div>
          <v-text-field
            v-model.number="transferQty"
            label="Qty to transfer to Shop"
            type="number"
            :min="1"
            :max="transferItem?.home_qty"
            variant="outlined"
            density="compact"
            class="mt-4"
            autofocus
          />
          <div class="ct-transfer-hint">
            Suggested: {{ suggestedQty }} units
            <span class="ct-use-suggested" @click="transferQty = suggestedQty">Use this</span>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="transferDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="submitQuickTransfer" :loading="transferring">
            Transfer Now
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const items = ref([])
const loading = ref(false)
const lastSync = ref('')
const search = ref('')
const groupFilter = ref('All Groups')
const viewMode = ref('all')
const filterLow = ref(false)
const transferDialog = ref(false)
const transferItem = ref(null)
const transferQty = ref(0)
const transferring = ref(false)

const headers = [
  { title: 'Item', key: 'item_name', sortable: true, width: '220px' },
  { title: 'Group', key: 'item_group', sortable: true, width: '130px' },
  { title: 'UOM', key: 'stock_uom', width: '70px' },
  { title: 'Shop Stock', key: 'shop_qty', sortable: true, width: '110px' },
  { title: 'Warehouse', key: 'home_qty', sortable: true, width: '110px' },
  { title: 'Total', key: 'total_qty', sortable: true, width: '90px' },
  { title: 'Status', key: 'status', width: '100px' },
  { title: '', key: 'actions', width: '90px', sortable: false },
]

const totalShop = computed(() => items.value.reduce((s, i) => s + (i.shop_qty || 0), 0).toFixed(0))
const totalHome = computed(() => items.value.reduce((s, i) => s + (i.home_qty || 0), 0).toFixed(0))
const lowStockItems = computed(() => items.value.filter(i => i.shop_qty < i.min_qty))
const itemGroups = computed(() => [...new Set(items.value.map(i => i.item_group).filter(Boolean))])

const filteredItems = computed(() => {
  let list = items.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(i => i.item_name?.toLowerCase().includes(q) || i.item_code?.toLowerCase().includes(q))
  }
  if (groupFilter.value !== 'All Groups') list = list.filter(i => i.item_group === groupFilter.value)
  if (viewMode.value === 'low') list = list.filter(i => i.shop_qty < i.min_qty)
  if (viewMode.value === 'zero') list = list.filter(i => i.shop_qty <= 0)
  return list
})

const suggestedQty = computed(() => {
  if (!transferItem.value) return 0
  return Math.max(transferItem.value.min_qty * 3 - transferItem.value.shop_qty, transferItem.value.min_qty)
})

const fmtQty = (v) => parseFloat(v || 0).toFixed(2).replace(/\.00$/, '')
const getStatus = (item) => {
  if (item.shop_qty <= 0) return 'OUT'
  if (item.shop_qty < item.min_qty) return 'LOW'
  return 'OK'
}
const getStatusColor = (item) => {
  if (item.shop_qty <= 0) return 'error'
  if (item.shop_qty < item.min_qty) return 'orange'
  return 'success'
}
const getShopQtyClass = (item) => {
  if (item.shop_qty <= 0) return 'ct-qty-zero'
  if (item.shop_qty < item.min_qty) return 'ct-qty-low'
  return 'ct-qty-ok'
}

const loadData = async () => {
  loading.value = true
  try {
    const r = await frappe.call({ method: 'posawesome.posawesome.api.city_trader_stock.get_stock_overview' })
    items.value = r.message || []
    lastSync.value = new Date().toLocaleTimeString()
  } catch (e) {
    frappe.msgprint('Failed to load stock data')
  } finally {
    loading.value = false
  }
}

const quickTransfer = (item) => {
  transferItem.value = item
  transferQty.value = Math.max(item.min_qty * 3 - item.shop_qty, item.min_qty)
  transferDialog.value = true
}

const submitQuickTransfer = async () => {
  if (!transferQty.value || transferQty.value <= 0) return
  if (transferQty.value > transferItem.value.home_qty) {
    frappe.msgprint('Not enough stock in warehouse')
    return
  }
  transferring.value = true
  try {
    const r = await frappe.call({
      method: 'posawesome.posawesome.api.city_trader_stock.create_stock_transfer',
      args: {
        items: JSON.stringify([{ item_code: transferItem.value.item_code, qty: transferQty.value, uom: transferItem.value.stock_uom }])
      }
    })
    frappe.show_alert({ message: `Transfer ${r.message?.name} submitted!`, indicator: 'green' })
    transferDialog.value = false
    await loadData()
  } catch (e) {
    frappe.msgprint('Transfer failed: ' + (e.message || e))
  } finally {
    transferring.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.ct-stock-page { padding: 16px; background: #f8f9fa; min-height: 100vh; }
.ct-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.ct-header-left { display: flex; align-items: center; gap: 12px; }
.ct-header-icon { font-size: 32px; color: #00BCD4; }
.ct-title { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.ct-subtitle { font-size: 13px; color: #666; }
.ct-header-right { display: flex; align-items: center; gap: 8px; }
.ct-last-sync { font-size: 12px; color: #888; }
.ct-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.ct-card { background: #fff; border-radius: 12px; padding: 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.ct-card-shop { border-left: 4px solid #00BCD4; }
.ct-card-home { border-left: 4px solid #7C3AED; }
.ct-card-alert { border-left: 4px solid #F59E0B; }
.ct-card-total { border-left: 4px solid #10B981; }
.ct-card-icon { color: #888; }
.ct-card-label { font-size: 12px; color: #888; font-weight: 500; }
.ct-card-value { font-size: 28px; font-weight: 800; color: #1a1a2e; line-height: 1; }
.ct-card-sub { font-size: 11px; color: #aaa; }
.ct-alert-val { color: #F59E0B; }
.ct-alert-banner { background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 8px; padding: 10px 16px; margin-bottom: 12px; display: flex; align-items: center; font-size: 14px; }
.ct-alert-link { color: #D97706; cursor: pointer; text-decoration: underline; margin-left: 4px; }
.ct-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.ct-search { max-width: 300px; }
.ct-group-filter { max-width: 180px; }
.ct-table-wrap { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.ct-qty-cell { display: flex; align-items: center; font-weight: 600; }
.ct-qty-zero { color: #EF4444; }
.ct-qty-low { color: #F59E0B; }
.ct-qty-ok { color: #10B981; }
.ct-status-chip { font-weight: 700; letter-spacing: 0.5px; }
.ct-dialog-title { font-weight: 700; display: flex; align-items: center; padding: 16px; }
.ct-transfer-item-name { font-size: 18px; font-weight: 700; color: #1a1a2e; }
.ct-transfer-meta { font-size: 13px; color: #888; margin-top: 4px; }
.ct-transfer-hint { font-size: 13px; color: #888; margin-top: 6px; }
.ct-use-suggested { color: #00BCD4; cursor: pointer; margin-left: 8px; text-decoration: underline; }
@media (max-width: 900px) { .ct-cards { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .ct-cards { grid-template-columns: 1fr; } }
</style>
