<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider-row">
          <input
            type="range"
            class="budget-slider"
            min="0"
            :max="maxBudget"
            step="50"
            v-model.number="budget"
          />
          <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
        </div>

        <div v-if="recommendationsLoading" class="loading">{{ t('common.loading') }}</div>
        <div v-else-if="recommendationsError" class="error">{{ recommendationsError }}</div>
        <div v-else-if="recommendedItems.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <template v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th>{{ t('restocking.table.currentDemand') }}</th>
                  <th>{{ t('restocking.table.forecastedDemand') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.quantity') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendedItems" :key="item.item_sku">
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>{{ item.item_name }}</td>
                  <td>
                    <span :class="['badge', item.trend]">
                      {{ t(`trends.${item.trend}`) }}
                    </span>
                  </td>
                  <td>{{ item.current_demand }}</td>
                  <td><strong>{{ item.forecasted_demand }}</strong></td>
                  <td>{{ currencySymbol }}{{ item.unit_cost }}</td>
                  <td>{{ item.recommended_quantity }}</td>
                  <td><strong>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="stats-grid">
            <div class="stat-card info">
              <div class="stat-label">{{ t('restocking.totalCost') }}</div>
              <div class="stat-value">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</div>
            </div>
            <div class="stat-card success">
              <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
              <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
            </div>
          </div>
        </template>

        <div class="place-order-row">
          <button
            v-if="!confirmingPlaceOrder"
            class="place-order-btn"
            :disabled="recommendationsLoading || placingOrder || recommendedItems.length === 0"
            @click="confirmingPlaceOrder = true"
          >
            {{ placingOrder ? t('restocking.placingOrder') : t('restocking.placeOrderButton') }}
          </button>
        </div>

        <div v-if="confirmingPlaceOrder" class="confirm-row">
          <span class="confirm-message">
            {{ t('restocking.confirmPlaceOrderMessage', { count: recommendedItems.length, amount: currencySymbol + totalCost.toLocaleString() }) }}
          </span>
          <div class="confirm-actions">
            <button class="confirm-cancel-btn" :disabled="placingOrder" @click="confirmingPlaceOrder = false">
              {{ t('common.cancel') }}
            </button>
            <button class="confirm-place-btn" :disabled="placingOrder" @click="placeOrder">
              {{ placingOrder ? t('restocking.placingOrder') : t('restocking.confirmButton') }}
            </button>
          </div>
        </div>

        <div v-if="placeOrderSuccess" class="success">
          {{ t('restocking.orderPlacedSuccess') }}
          <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
        </div>
        <div v-else-if="placeOrderError" class="error">
          {{ t('restocking.orderPlacedError') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)

    const demandForecasts = ref([])
    const inventoryItems = ref([])

    const budget = ref(0)

    const recommendedItems = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const recommendationsLoading = ref(false)
    const recommendationsError = ref(null)

    const placingOrder = ref(false)
    const placeOrderSuccess = ref(false)
    const placeOrderError = ref(null)
    const confirmingPlaceOrder = ref(false)

    // Ceiling budget: the total spend needed to fully close every positive demand gap,
    // so the slider's top end always represents "fully restock everything forecasted".
    const maxBudget = computed(() => {
      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))
      const total = demandForecasts.value.reduce((sum, forecast) => {
        const gap = forecast.forecasted_demand - forecast.current_demand
        const inventoryItem = inventoryBySku.get(forecast.item_sku)
        if (gap > 0 && inventoryItem && typeof inventoryItem.unit_cost === 'number') {
          return sum + gap * inventoryItem.unit_cost
        }
        return sum
      }, 0)
      // Round up to a clean $100 increment and keep a sane floor for the slider range
      return Math.max(500, Math.ceil(total / 100) * 100)
    })

    let debounceTimer = null
    // Setting the initial budget below also fires the `watch(budget, ...)` below; this flag
    // lets loadInitialData suppress that one auto-triggered fetch since it already awaits its
    // own immediate (non-debounced) fetch for a snappier first paint.
    let skipNextBudgetWatch = false
    // Tracks the in-flight recommendations request so a stale response from a superseded
    // budget value can never overwrite the recommendations for the current budget.
    let currentAbortController = null

    const fetchRecommendations = async () => {
      if (currentAbortController) {
        currentAbortController.abort()
      }
      if (!budget.value || budget.value <= 0) {
        currentAbortController = null
        recommendedItems.value = []
        totalCost.value = 0
        remainingBudget.value = 0
        return
      }
      const controller = new AbortController()
      currentAbortController = controller
      try {
        recommendationsLoading.value = true
        recommendationsError.value = null
        const data = await api.getRestockRecommendations(budget.value, { signal: controller.signal })
        recommendedItems.value = data.recommended_items
        totalCost.value = data.total_cost
        remainingBudget.value = data.remaining_budget
      } catch (err) {
        if (axios.isCancel(err) || err.code === 'ERR_CANCELED' || err.name === 'CanceledError') {
          return
        }
        recommendationsError.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        if (currentAbortController === controller) {
          recommendationsLoading.value = false
        }
      }
    }

    // Debounce recommendation fetches while the slider is being dragged, so we don't
    // fire an API call on every intermediate value as it moves.
    const scheduleFetchRecommendations = () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        fetchRecommendations()
      }, 300)
    }

    watch(budget, () => {
      if (skipNextBudgetWatch) {
        skipNextBudgetWatch = false
        return
      }
      // A successful order reflects a specific budget/recommendation snapshot; once the
      // budget changes again that snapshot is stale, so clear the banners.
      placeOrderSuccess.value = false
      placeOrderError.value = null
      confirmingPlaceOrder.value = false
      scheduleFetchRecommendations()
    })

    const loadInitialData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        demandForecasts.value = forecastsData
        inventoryItems.value = inventoryData
        skipNextBudgetWatch = true
        budget.value = Math.round(maxBudget.value / 2)
        await fetchRecommendations()
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      placingOrder.value = true
      placeOrderError.value = null
      placeOrderSuccess.value = false
      try {
        await api.placeRestockOrder({
          budget: budget.value,
          items: recommendedItems.value
        })
        placeOrderSuccess.value = true
      } catch (err) {
        placeOrderError.value = 'Failed to place order: ' + err.message
      } finally {
        placingOrder.value = false
        confirmingPlaceOrder.value = false
      }
    }

    onMounted(loadInitialData)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      maxBudget,
      recommendedItems,
      totalCost,
      remainingBudget,
      recommendationsLoading,
      recommendationsError,
      placingOrder,
      placeOrderSuccess,
      placeOrderError,
      confirmingPlaceOrder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  transition: background 0.2s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  transition: background 0.2s ease;
}

.budget-slider::-moz-range-thumb:hover {
  background: #2563eb;
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
}

.budget-value {
  min-width: 120px;
  text-align: right;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 1.1rem;
  font-style: italic;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.confirm-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 1.25rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.confirm-message {
  color: #0f172a;
  font-size: 0.938rem;
  flex: 1;
  min-width: 200px;
}

.confirm-actions {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.confirm-cancel-btn {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
}

.confirm-cancel-btn:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.confirm-cancel-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-place-btn {
  padding: 0.625rem 1.25rem;
  background: #3b82f6;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
}

.confirm-place-btn:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
}

.confirm-place-btn:disabled {
  background: #cbd5e1;
  border-color: #cbd5e1;
  cursor: not-allowed;
}

.success {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #059669;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.success a {
  color: #059669;
  font-weight: 600;
  text-decoration: underline;
}
</style>
