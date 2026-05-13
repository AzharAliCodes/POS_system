<template>
  <div class="ct-page">
    <div class="ct-header">
      <div class="ct-header-left">
        <v-icon class="ct-icon">mdi-transfer</v-icon>
        <div>
          <div class="ct-title">Stock Transfer</div>
          <div class="ct-sub">Move stock between warehouses</div>
        </div>
      </div>
    </div>

    <div class="ct-direction-bar">
      <v-btn-toggle v-model="direction" mandatory density="compact" color="primary" variant="outlined">
        <v-btn value="home_to_shop"><v-icon size="16" class="mr-1">mdi-home</v-icon> Warehouse → Shop</v-btn>
        <v-btn value="shop_to_home"><v-icon size="16" class="mr-1">mdi-storefront</v-icon> Shop → Warehouse</v-btn>
      </v-btn-toggle>
      <div class="ct-direction-label">
        <v-icon size="14" class="mr-1">mdi-arrow-right</v-icon>
        From <b>{{ fromWH }}</b> to <b>{{ toWH }}</b>
      </div>
    </div>

    <div class="ct-layout">
      <div class="ct-panel">
        <div class="ct-panel-title">
          <v-icon size="16" class="mr-1">mdi-package-variant</v-icon>
          Select Items
          <span class="ct-avail-label">(items with stock in {{ fromWHShort }})</span>
        </div>
        <div class="ct-search-row">
          <v-text-field v-model="search" placeholder="Search..." prepend-inner-icon="mdi-magnify"
            variant="outlined" density="compact" hide-details clearable />
          <v-btn-toggle v-model="showFilter" density="compact" variant="outlined" mandatory>
            <v-btn value="all" size="small">All</v-btn>
            <v-btn value="low" size="small" color="orange">Low</v-btn>
            <v-btn value="gst" size="small" color="teal">GST</v-btn>
          </v-btn-toggle>
          <v-btn icon size="small" variant="text" @click="loadItems" :loading="loading">
            <v-icon size="16">mdi-refresh</v-icon>
          </v-btn>
        </div>
        <div class="ct-item-list" v-if="!loading">
          <div v-for="item in filteredItems" :key="item.item_code"
            class="ct-item-row"
            :class="{ 'ct-selected': isSelected(item), 'ct-item-low': item.shop_qty < item.min_qty }"
            @click="toggleItem(item)">
            <div class="ct-item-body">
              <div class="ct-item-name">{{ item.item_name }}</div>
              <div class="ct-item-meta">
                Shop: <b :class="item.shop_qty > 0 ? 'ct-ok-text' : 'ct-zero-text'">{{ fmt(item.shop_qty) }}</b>
                &nbsp;·&nbsp; WH: <b>{{ fmt(item.home_qty) }}</b>
                &nbsp;·&nbsp; {{ item.stock_uom }}
                <span v-if="item.gst_applicable" class="ct-gst-badge">GST</span>
              </div>
            </div>
            <div class="ct-item-chips">
              <v-chip v-if="item.shop_qty < item.min_qty && item.shop_qty > 0" color="orange" size="x-small" variant="flat">LOW</v-chip>
              <v-chip v-if="item.shop_qty <= 0 && direction === 'shop_to_home'" color="error" size="x-small" variant="flat">EMPTY</v-chip>
              <v-icon v-if="isSelected(item)" color="primary" size="18">mdi-check-circle</v-icon>
            </div>
          </div>
          <div v-if="!filteredItems.length" class="ct-empty">No items with stock in {{ fromWHShort }}</div>
        </div>
        <div v-else class="ct-loading"><v-progress-circular indeterminate color="primary" /></div>
      </div>

      <div class="ct-panel">
        <div class="ct-panel-title">
          <v-icon size="16" class="mr-1">mdi-cart</v-icon>
          Transfer Cart
          <v-chip size="x-small" color="primary" variant="flat" class="ml-2">{{ cart.length }}</v-chip>
        </div>
        <div v-if="!cart.length" class="ct-cart-empty">
          <v-icon size="40" color="#ddd">mdi-cart-outline</v-icon>
          <div>Select items from the left</div>
        </div>
        <div v-else>
          <div v-for="(e, i) in cart" :key="e.item_code" class="ct-cart-row">
            <div class="ct-cart-info">
              <div class="ct-cart-name">{{ e.item_name }}</div>
              <div class="ct-cart-meta">Available: {{ fmt(e.from_qty) }} {{ e.stock_uom }}</div>
            </div>
            <div class="ct-cart-qty">
              <v-btn icon size="x-small" variant="text" @click="adj(i,-1)"><v-icon size="14">mdi-minus</v-icon></v-btn>
              <v-text-field v-model.number="e.qty" type="number" :min="1" :max="e.from_qty"
                variant="outlined" density="compact" hide-details style="width:70px" />
              <v-btn icon size="x-small" variant="text" @click="adj(i,1)"><v-icon size="14">mdi-plus</v-icon></v-btn>
            </div>
            <v-btn icon size="x-small" variant="text" color="error" @click="cart.splice(i,1)">
              <v-icon size="14">mdi-close</v-icon>
            </v-btn>
          </div>
          <v-textarea v-model="notes" label="Notes (optional)" variant="outlined"
            density="compact" rows="2" hide-details class="mt-3" />
          <div class="ct-cart-footer">
            <v-btn size="small" variant="text" color="error" @click="cart=[];notes=''">Clear</v-btn>
            <v-btn color="primary" variant="flat" :loading="submitting" @click="submit" style="flex:1;margin-left:8px">
              <v-icon size="16" class="mr-1">mdi-transfer</v-icon>
              Transfer {{ cart.length }} item{{ cart.length > 1 ? 's' : '' }}
            </v-btn>
          </div>
        </div>
        <div class="ct-recent">
          <div class="ct-recent-title"><v-icon size="14" class="mr-1">mdi-history</v-icon>Recent Transfers</div>
          <div v-if="!recent.length" class="ct-recent-empty">No transfers yet</div>
          <div v-for="t in recent" :key="t.name" class="ct-recent-row">
            <div class="ct-recent-ref">{{ t.name }}</div>
            <div class="ct-recent-meta">
              {{ t.posting_date }} ·
              {{ t.from_warehouse === 'Home Warehouse - CT' ? 'WH→Shop' : 'Shop→WH' }}
              · {{ fmt(t.total_qty) }} units
            </div>
          </div>
        </div>
      </div>
    </div>

    <v-dialog v-model="doneDialog" max-width="360">
      <v-card>
        <v-card-text class="text-center pa-8">
          <v-icon size="56" color="success">mdi-check-circle</v-icon>
          <div style="font-size:20px;font-weight:800;margin-top:10px">Transfer Done!</div>
          <div style="color:#7C3AED;font-weight:600;margin-top:4px">{{ doneRef }}</div>
          <v-btn color="primary" variant="flat" class="mt-4" @click="doneDialog=false">Done</v-btn>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue"
const SHOP = "Stores - CT"; const HOME = "Home Warehouse - CT"
const direction = ref("home_to_shop")
const fromWH = computed(() => direction.value === "home_to_shop" ? HOME : SHOP)
const toWH   = computed(() => direction.value === "home_to_shop" ? SHOP : HOME)
const fromWHShort = computed(() => direction.value === "home_to_shop" ? "Warehouse" : "Shop")
const items = ref([]); const cart = ref([]); const recent = ref([])
const search = ref(""); const showFilter = ref("all")
const loading = ref(false); const submitting = ref(false)
const notes = ref(""); const doneDialog = ref(false); const doneRef = ref("")
const fmt = v => parseFloat(v||0).toFixed(2).replace(/\.00$/,"")
const isSelected = item => cart.value.some(c => c.item_code === item.item_code)
const filteredItems = computed(() => {
  let list = items.value.filter(i => direction.value === "home_to_shop" ? i.home_qty > 0 : i.shop_qty > 0)
  if (search.value) { const q = search.value.toLowerCase(); list = list.filter(i => i.item_name?.toLowerCase().includes(q)) }
  if (showFilter.value === "low") list = list.filter(i => i.shop_qty < i.min_qty)
  if (showFilter.value === "gst") list = list.filter(i => i.gst_applicable)
  return list
})
const toggleItem = item => {
  const idx = cart.value.findIndex(c => c.item_code === item.item_code)
  if (idx >= 0) { cart.value.splice(idx, 1); return }
  const fromQty = direction.value === "home_to_shop" ? item.home_qty : item.shop_qty
  const suggested = Math.min(Math.max(item.min_qty*3 - item.shop_qty, item.min_qty, 1), fromQty)
  cart.value.push({ item_code: item.item_code, item_name: item.item_name, stock_uom: item.stock_uom, from_qty: fromQty, qty: suggested })
}
const adj = (i, d) => { const e = cart.value[i]; const n = (e.qty||1)+d; if (n>=1&&n<=e.from_qty) e.qty=n }
const loadItems = async () => {
  loading.value = true
  try { const r = await frappe.call({ method: "posawesome.posawesome.api.city_trader_stock.get_stock_overview" }); items.value = r.message||[] }
  finally { loading.value = false }
}
const loadRecent = async () => {
  try { const r = await frappe.call({ method: "posawesome.posawesome.api.city_trader_stock.get_recent_transfers" }); recent.value = r.message||[] }
  catch(e) {}
}
const submit = async () => {
  const bad = cart.value.filter(c => !c.qty || c.qty > c.from_qty)
  if (bad.length) { frappe.msgprint("Some quantities exceed available stock"); return }
  submitting.value = true
  try {
    const r = await frappe.call({ method: "posawesome.posawesome.api.city_trader_stock.create_stock_transfer",
      args: { items: JSON.stringify(cart.value.map(c=>({item_code:c.item_code,qty:c.qty,uom:c.stock_uom}))),
        from_wh: fromWH.value, to_wh: toWH.value, notes: notes.value } })
    doneRef.value = r.message?.name; doneDialog.value = true
    cart.value = []; notes.value = ""
    await loadItems(); await loadRecent()
  } catch(e) { frappe.msgprint("Transfer failed — check stock availability") }
  finally { submitting.value = false }
}
watch(direction, () => { cart.value = [] })
onMounted(async () => { await loadItems(); await loadRecent() })
</script>

<style scoped>
.ct-page{padding:16px;background:#f8f9fa;min-height:100vh}
.ct-header{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.ct-icon{font-size:30px;color:#7C3AED}
.ct-title{font-size:20px;font-weight:800;color:#1a1a2e}
.ct-sub{font-size:12px;color:#888}
.ct-direction-bar{display:flex;align-items:center;gap:16px;margin-bottom:14px;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.ct-direction-label{font-size:13px;color:#666}
.ct-layout{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.ct-panel{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.ct-panel-title{font-size:14px;font-weight:700;display:flex;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:4px}
.ct-avail-label{font-size:11px;color:#888;font-weight:400}
.ct-search-row{display:flex;gap:8px;align-items:center;margin-bottom:8px}
.ct-item-list{max-height:calc(100vh - 360px);overflow-y:auto}
.ct-item-row{display:flex;justify-content:space-between;align-items:center;padding:9px 10px;border-radius:8px;cursor:pointer;border:1.5px solid transparent;margin-bottom:3px;transition:.15s}
.ct-item-row:hover{background:#f0f9ff;border-color:#BAE6FD}
.ct-selected{background:#EFF6FF;border-color:#3B82F6!important}
.ct-item-low{border-left:3px solid #F59E0B}
.ct-item-name{font-size:13px;font-weight:600;color:#1a1a2e}
.ct-item-meta{font-size:11px;color:#888;margin-top:2px}
.ct-item-chips{display:flex;align-items:center;gap:4px}
.ct-ok-text{color:#10B981}
.ct-zero-text{color:#EF4444}
.ct-gst-badge{background:#CCFBF1;color:#0F766E;border-radius:4px;padding:0 4px;font-size:10px;font-weight:700;margin-left:4px}
.ct-cart-empty{text-align:center;padding:40px;color:#aaa;display:flex;flex-direction:column;align-items:center;gap:8px}
.ct-cart-row{display:flex;align-items:center;gap:6px;padding:7px;border-radius:8px;border:1px solid #E5E7EB;margin-bottom:5px}
.ct-cart-info{flex:1}
.ct-cart-name{font-size:13px;font-weight:600}
.ct-cart-meta{font-size:11px;color:#888}
.ct-cart-qty{display:flex;align-items:center;gap:2px}
.ct-cart-footer{display:flex;justify-content:space-between;align-items:center;margin-top:10px;padding-top:10px;border-top:1px solid #E5E7EB}
.ct-recent{margin-top:14px;padding-top:14px;border-top:1px solid #E5E7EB}
.ct-recent-title{font-size:12px;font-weight:700;color:#888;display:flex;align-items:center;margin-bottom:8px}
.ct-recent-empty{font-size:12px;color:#ccc;text-align:center;padding:8px}
.ct-recent-row{padding:6px 8px;border-radius:6px;background:#F9FAFB;margin-bottom:4px}
.ct-recent-ref{font-size:12px;font-weight:700;color:#374151}
.ct-recent-meta{font-size:11px;color:#9CA3AF}
.ct-empty,.ct-loading{text-align:center;padding:40px;color:#aaa}
@media(max-width:768px){.ct-layout{grid-template-columns:1fr}}
</style>
