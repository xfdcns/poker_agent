<template>
  <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
      <h2 style="color: var(--gold);">♠ Poker Agent</h2>
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="color: var(--text-dim);">{{ userStore.username }}</span>
        <button class="btn btn-outline" style="padding:6px 14px; font-size:13px;" @click="handleLogout">退出</button>
      </div>
    </div>
    <div class="card" style="margin-bottom:20px;">
      <h3 style="margin-bottom:16px;">创建牌桌</h3>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
        <div class="field">
          <label>我的位置</label>
          <select class="input" v-model="tableForm.position">
            <option value="UTG">UTG</option>
            <option value="MP">MP</option>
            <option value="CO">CO</option>
            <option value="BTN">BTN</option>
            <option value="SB">SB</option>
            <option value="BB">BB</option>
          </select>
        </div>
        <div class="field">
          <label>玩家人数</label>
          <select class="input" v-model.number="tableForm.numPlayers">
            <option :value="2">2人</option>
            <option :value="3">3人</option>
            <option :value="4">4人</option>
            <option :value="5">5人</option>
            <option :value="6">6人</option>
          </select>
        </div>
        <div class="field">
          <label>初始筹码</label>
          <input class="input" type="number" v-model.number="tableForm.buyIn" />
        </div>
        <div class="field">
          <label>大盲注</label>
          <input class="input" type="number" v-model.number="tableForm.blind" min="1" />
        </div>
      </div>
      <button class="btn btn-primary" style="margin-top:16px;" @click="handleCreate" :disabled="loading">
        <span v-if="loading" class="loading-spinner"></span>
        <span v-else>创建并进入</span>
      </button>
    </div>
    <div class="card">
      <h3 style="margin-bottom:12px;">项目架构</h3>
      <div style="color: var(--text-dim); font-size: 13px; line-height: 1.8;">
        <p>🎯 胜率引擎：蒙特卡洛模拟 10000次</p>
        <p>🧠 LLM决策：Qwen3.7-Max + RAG策略知识库</p>
        <p>📚 知识库：ChromaDB + 13篇专业策略</p>
        <p>🔄 降级兜底：LLM失败→规则引擎</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useGameStore } from '../stores/game'
import { createTable } from '../api'

const router = useRouter()
const userStore = useUserStore()
const gameStore = useGameStore()

const tableForm = ref({
  position: 'BTN',
  numPlayers: 6,
  buyIn: 1000,
  blind: 20
})
const loading = ref(false)

async function handleCreate() {
  loading.value = true
  try {
    const res = await createTable({
      my_position: tableForm.value.position,
      num_players: tableForm.value.numPlayers,
      my_hole_cards: "Ah Kh",
      buy_in: tableForm.value.buyIn,
      small_blind: tableForm.value.blind / 2,
      big_blind: tableForm.value.blind
    })
    if (res.code === 200) {
      gameStore.tableId = res.data.table_id || res.data.id
      gameStore.initPlayers(
        tableForm.value.numPlayers,
        tableForm.value.buyIn,
        tableForm.value.position,
        tableForm.value.blind
      )
      router.push('/game')
    } else {
      alert(res.message || '创建失败')
    }
  } catch (e) {
    alert('网络错误')
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>