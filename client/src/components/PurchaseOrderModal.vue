<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="shortage-header">
              <div class="shortage-title-section">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <!-- CREATE MODE -->
            <form v-if="mode === 'create'" class="po-form" @submit.prevent="handleFormSubmit">
              <div class="summary-card danger">
                <div class="summary-label">Shortage Amount</div>
                <div class="summary-value">{{ shortage }} units</div>
              </div>

              <div v-if="submitError" class="form-error">{{ submitError }}</div>

              <div class="form-grid">
                <div class="form-field">
                  <label class="field-label" for="supplier-name">Supplier Name</label>
                  <input
                    id="supplier-name"
                    v-model="form.supplier_name"
                    type="text"
                    class="field-input"
                    placeholder="Enter supplier name"
                    required
                  />
                </div>

                <div class="form-field">
                  <label class="field-label" for="quantity">Quantity</label>
                  <input
                    id="quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    class="field-input"
                    required
                  />
                </div>

                <div class="form-field">
                  <label class="field-label" for="unit-cost">Unit Cost</label>
                  <input
                    id="unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    min="0"
                    step="0.01"
                    class="field-input"
                    required
                  />
                </div>

                <div class="form-field">
                  <label class="field-label" for="expected-delivery">Expected Delivery Date</label>
                  <input
                    id="expected-delivery"
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="field-input"
                    required
                  />
                </div>

                <div class="form-field form-field-full">
                  <label class="field-label" for="notes">Notes</label>
                  <textarea
                    id="notes"
                    v-model="form.notes"
                    class="field-input field-textarea"
                    placeholder="Optional notes"
                    rows="3"
                  ></textarea>
                </div>
              </div>

              <div class="line-total-card">
                <div class="summary-label">Line Total</div>
                <div class="summary-value">{{ formatCurrency(lineTotal) }}</div>
              </div>

              <div v-if="confirmingSubmit" class="confirm-bar">
                <span class="confirm-message">
                  Create this purchase order for {{ formatCurrency(lineTotal) }}? This cannot be undone.
                </span>
                <div class="confirm-actions">
                  <button type="button" class="btn-secondary" :disabled="submitting" @click="confirmingSubmit = false">
                    Cancel
                  </button>
                  <button type="button" class="btn-primary" :disabled="submitting" @click="submitForm">
                    {{ submitting ? 'Creating...' : 'Confirm & Create' }}
                  </button>
                </div>
              </div>
            </form>

            <!-- VIEW MODE -->
            <div v-else class="po-view">
              <div v-if="loadingPO" class="po-loading">Loading purchase order...</div>
              <div v-else-if="loadError" class="form-error">{{ loadError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">PO ID</div>
                  <div class="info-value order-id">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span class="badge info">{{ purchaseOrder.status }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">Supplier</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Quantity</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Unit Cost</div>
                  <div class="info-value">{{ formatCurrency(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Line Total</div>
                  <div class="info-value">{{ formatCurrency(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Created</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div class="info-item form-field-full" v-if="purchaseOrder.notes">
                  <div class="info-label">Notes</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
              <div v-else class="po-loading">No purchase order found.</div>

              <div v-if="cancelError" class="form-error">{{ cancelError }}</div>

              <div v-if="purchaseOrder && purchaseOrder.status === 'pending' && !confirmingCancel" class="cancel-po-row">
                <button class="btn-danger-outline" @click="confirmingCancel = true">Cancel Purchase Order</button>
              </div>

              <div v-if="confirmingCancel" class="confirm-bar">
                <span class="confirm-message">Cancel this purchase order? This cannot be undone.</span>
                <div class="confirm-actions">
                  <button class="btn-secondary" :disabled="cancelling" @click="confirmingCancel = false">Keep It</button>
                  <button class="btn-danger" :disabled="cancelling" @click="cancelPO">
                    {{ cancelling ? 'Cancelling...' : 'Confirm Cancel' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
            <button
              v-if="mode === 'create' && !confirmingSubmit"
              class="btn-primary"
              :disabled="submitting"
              @click="confirmingSubmit = true"
            >
              Create Purchase Order
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const { translateProductName, currentCurrency } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created', 'po-cancelled'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const defaultForm = () => ({
  supplier_name: '',
  quantity: shortage.value > 0 ? shortage.value : 1,
  unit_cost: 0,
  expected_delivery_date: '',
  notes: ''
})

const form = ref(defaultForm())
const submitting = ref(false)
const submitError = ref(null)
const confirmingSubmit = ref(false)

const purchaseOrder = ref(null)
const loadingPO = ref(false)
const loadError = ref(null)

const confirmingCancel = ref(false)
const cancelling = ref(false)
const cancelError = ref(null)

const lineTotal = computed(() => {
  const qty = Number(form.value.quantity) || 0
  const cost = Number(form.value.unit_cost) || 0
  return qty * cost
})

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const formatCurrency = (value) => {
  const amount = Number(value) || 0
  return `${currencySymbol.value}${amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const close = () => {
  emit('close')
}

const resetCreateState = () => {
  form.value = defaultForm()
  submitError.value = null
  submitting.value = false
  confirmingSubmit.value = false
}

const submitForm = async () => {
  if (!props.backlogItem) return
  submitting.value = true
  submitError.value = null
  try {
    const payload = {
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name,
      quantity: Number(form.value.quantity),
      unit_cost: Number(form.value.unit_cost),
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes || undefined
    }
    const response = await api.createPurchaseOrder(payload)
    emit('po-created', response)
  } catch (err) {
    submitError.value = err.response?.data?.detail || 'Failed to create purchase order'
  } finally {
    submitting.value = false
    confirmingSubmit.value = false
  }
}

const handleFormSubmit = () => {
  if (!confirmingSubmit.value) {
    confirmingSubmit.value = true
    return
  }
  submitForm()
}

const cancelPO = async () => {
  if (!purchaseOrder.value || !props.backlogItem) return
  cancelling.value = true
  cancelError.value = null
  try {
    await api.cancelPurchaseOrder(purchaseOrder.value.id)
    confirmingCancel.value = false
    emit('po-cancelled', { backlog_item_id: props.backlogItem.id })
    close()
  } catch (err) {
    cancelError.value = err.response?.data?.detail || 'Failed to cancel purchase order'
  } finally {
    cancelling.value = false
  }
}

const loadPurchaseOrder = async () => {
  if (!props.backlogItem) return

  if (props.backlogItem.purchase_order) {
    purchaseOrder.value = props.backlogItem.purchase_order
    return
  }

  loadingPO.value = true
  loadError.value = null
  purchaseOrder.value = null
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    if (err.response?.status === 404) {
      loadError.value = 'No purchase order found for this item.'
    } else {
      loadError.value = 'Failed to load purchase order'
    }
  } finally {
    loadingPO.value = false
  }
}

watch(
  () => [props.isOpen, props.mode],
  ([isOpen, mode]) => {
    if (isOpen && mode === 'create') {
      resetCreateState()
    }
    if (isOpen && mode === 'view') {
      confirmingCancel.value = false
      cancelling.value = false
      cancelError.value = null
      loadPurchaseOrder()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.close-button:hover {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.shortage-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 1.5rem;
}

.shortage-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.priority-badge.medium {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.priority-badge.low {
  background: var(--color-info-subtle);
  color: var(--color-info);
}

.summary-card {
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid;
  margin-bottom: 1.5rem;
}

.summary-card.danger {
  border-color: var(--color-danger);
  background: var(--color-danger-subtle);
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text);
}

.summary-card.danger .summary-value {
  color: var(--color-danger);
}

.form-error {
  background: var(--color-danger-subtle);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field-full {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.field-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.938rem;
  color: var(--color-text);
  background: var(--color-surface);
  font-family: inherit;
  transition: border-color 0.15s ease;
}

.field-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.field-textarea {
  resize: vertical;
}

.line-total-card {
  margin-top: 1.5rem;
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface-alt);
}

.po-loading {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.info-value {
  font-size: 0.938rem;
  color: var(--color-text);
  font-weight: 500;
}

.info-value.order-id {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--color-accent);
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.badge.info {
  background: var(--color-info-subtle);
  color: var(--color-info);
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--color-border);
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-bar {
  margin-top: 1.5rem;
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface-alt);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.confirm-message {
  color: var(--color-text);
  font-size: 0.938rem;
  flex: 1;
  min-width: 200px;
}

.confirm-actions {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.cancel-po-row {
  margin-top: 1.5rem;
}

.btn-danger-outline {
  padding: 0.625rem 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-danger);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-danger-outline:hover {
  background: var(--color-danger-subtle);
}

.btn-danger {
  padding: 0.625rem 1.25rem;
  background: var(--color-danger);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
  border-color: #b91c1c;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
