<template>
  <div class="card-picker">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="color: var(--text-dim); font-size:12px;">{{ label }}（已选 {{ selected.length }}/{{ max }}）</span>
      <button v-if="selected.length > 0" style="background:none; border:none; color:var(--red); font-size:12px; cursor:pointer;" @click="clearAll">清空</button>
    </div>
    <div class="card-grid">
      <div v-for="card in allCards" :key="card.code"
        class="pick-card"
        :class="{ selected: isSelected(card.code), disabled: isDisabled(card.code), [card.color]: true }"
        @click="toggleCard(card.code)">
        <span class="pick-rank">{{ card.rank }}</span>
        <span class="pick-suit">{{ card.suit }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '选牌' },
  max: { type: Number, default: 2 }
})

const emit = defineEmits(['update:modelValue'])

const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
const suits = [
  { symbol: '♠', code: 's', color: 'black' },
  { symbol: '♥', code: 'h', color: 'red' },
  { symbol: '♦', code: 'd', color: 'red' },
  { symbol: '♣', code: 'c', color: 'black' }
]

const allCards = computed(() => {
  const cards = []
  for (const suit of suits) {
    for (const rank of ranks) {
      cards.push({
        code: rank + suit.code,
        rank,
        suit: suit.symbol,
        color: suit.color
      })
    }
  }
  return cards
})

const selected = computed(() => {
  if (!props.modelValue) return []
  return props.modelValue.split(' ').filter(c => c.length > 0)
})

function isSelected(code) {
  return selected.value.includes(code)
}

function isDisabled(code) {
  return !isSelected(code) && selected.value.length >= props.max
}

function toggleCard(code) {
  let newSelected
  if (isSelected(code)) {
    newSelected = selected.value.filter(c => c !== code)
  } else {
    if (selected.value.length >= props.max) return
    newSelected = [...selected.value, code]
  }
  emit('update:modelValue', newSelected.join(' '))
}

function clearAll() {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.card-picker {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(13, 1fr);
  gap: 3px;
}
.pick-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 0.7;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}
.pick-card:hover:not(.disabled) {
  border-color: var(--gold);
  background: rgba(245, 158, 11, 0.1);
}
.pick-card.selected {
  background: var(--gold);
  border-color: var(--gold);
}
.pick-card.selected .pick-rank,
.pick-card.selected .pick-suit {
  color: #000;
}
.pick-card.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.pick-card.black .pick-rank,
.pick-card.black .pick-suit {
  color: #e2e8f0;
}
.pick-card.red .pick-rank,
.pick-card.red .pick-suit {
  color: var(--red);
}
.pick-rank {
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
}
.pick-suit {
  font-size: 11px;
  line-height: 1;
  margin-top: 1px;
}
</style>