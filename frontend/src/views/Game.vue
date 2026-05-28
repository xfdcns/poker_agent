<template>
  <div style="min-height: 100vh; display: flex; flex-direction: column;">
    <!-- 顶部 -->
    <header style="display:flex; justify-content:space-between; align-items:center; padding:10px 20px; background: var(--bg-panel); border-bottom: 1px solid var(--border);">
      <div style="display:flex; align-items:center; gap:14px;">
        <span style="color: var(--gold); font-weight:700;">♠ Poker Agent</span>
        <span style="font-size:13px;">阶段: <b style="color: var(--gold);">{{ gameStore.stageLabel }}</b></span>
        <span style="font-size:13px;">底池: <b style="color: var(--green);">{{ gameStore.potSize }}</b></span>
      </div>
      <button class="btn btn-outline" style="padding:4px 12px; font-size:12px;" @click="backToLobby">返回大厅</button>
    </header>

    <!-- 主区域 -->
    <div style="flex:1; display:flex; padding:16px; gap:16px; overflow:auto;">
      <!-- 左：牌桌 -->
      <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:12px;">

        <!-- 对手头像 -->
        <div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center;">
          <PlayerAvatar v-for="(p, i) in opponents" :key="p.position"
            :player="p" :isCurrentTurn="isOpponentTurn(p.position)"
            @click="onOpponentClick(p)" />
        </div>

        <!-- 牌桌 -->
        <div class="poker-table" style="width:460px; height:200px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px;">
          <div style="display:flex; gap:4px;">
            <div v-for="(card, i) in displayCommunityCards" :key="i" class="poker-card" :class="cardColor(card)">{{ card }}</div>
            <div v-for="i in (5 - displayCommunityCards.length)" :key="'e'+i" class="poker-card poker-card-back"></div>
          </div>
          <div style="color: var(--gold); font-weight:700; font-size:16px;">底池: {{ gameStore.potSize }}</div>
        </div>

        <!-- 自己 -->
        <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
          <PlayerAvatar :player="gameStore.myPlayer || {}" :isCurrentTurn="isMyTurn" />
          <!-- 手牌显示 -->
          <div style="display:flex; gap:4px;">
            <div v-for="(card, i) in displayHoleCards" :key="i" class="poker-card" :class="cardColor(card)">{{ card }}</div>
            <template v-if="!gameStore.myPlayer?.holeCards">
              <div class="poker-card poker-card-back"></div>
              <div class="poker-card poker-card-back"></div>
            </template>
          </div>
          <!-- 胜率快显 -->
          <div v-if="gameStore.analysis && !gameStore.showAgentDetail" style="font-size:13px; color: var(--text-dim);">
            胜率: <b :style="{ color: winRateColor }">{{ gameStore.analysis.win_rate }}%</b>
          </div>
        </div>

        <!-- 操作区 -->
        <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:center; align-items:center;">
          <!-- setup阶段 -->
          <template v-if="gameStore.stage === 'setup'">
            <button class="btn btn-primary" @click="startHand">开始对局</button>
            <button class="btn btn-outline" @click="showHolePicker = !showHolePicker">
              {{ showHolePicker ? '收起选牌' : '选择手牌' }}
            </button>
          </template>

          <!-- 自己回合 -->
          <template v-else-if="isMyTurn">
            <button class="btn btn-blue" @click="selfAction('fold')">弃牌</button>
            <button class="btn btn-outline" @click="selfAction('check')" :disabled="mustCall">过牌</button>
            <button class="btn btn-green" @click="selfAction('call')" :disabled="!mustCall">跟注 {{ callAmount }}</button>
            <button class="btn btn-primary" @click="openSelfRaise">加注</button>
            <button class="btn btn-red" @click="selfAction('all-in')">All In</button>
            <button class="btn btn-outline" @click="requestFullAnalysis" :disabled="gameStore.loading" style="font-size:12px;">
              <span v-if="gameStore.loading" class="loading-spinner"></span>
              <span v-else>🧠 Agent分析</span>
            </button>
          </template>

          <!-- 回合结束 -->
          <template v-else-if="gameStore.roundComplete">
            <span style="color:var(--green); font-size:13px;">本轮结束</span>
          </template>

          <!-- 等待对手 -->
          <template v-else>
            <span style="color:var(--text-dim); font-size:13px;">等待 {{ gameStore.actingPosition }} 操作...</span>
          </template>
        </div>

        <!-- 自己加注输入 -->
        <div v-if="showSelfRaise" style="display:flex; gap:8px; align-items:center;">
          <input class="input" type="number" v-model.number="selfRaiseAmount" style="width:100px;" :min="minRaise" :max="gameStore.myPlayer?.chips + gameStore.myPlayer?.currentBet" />
          <button class="btn btn-primary" style="padding:6px 12px;" @click="confirmSelfRaise">确认加注</button>
          <button class="btn btn-outline" style="padding:6px 12px;" @click="showSelfRaise = false">取消</button>
        </div>

        <!-- 选牌器 -->
        <div v-if="showHolePicker && gameStore.stage === 'setup'" style="width:100%; max-width:500px;">
          <CardPicker v-model="holeCardsTemp" label="选择手牌" :max="2" />
          <button class="btn btn-blue" style="margin-top:8px;" @click="confirmHoleCards">确认手牌</button>
        </div>
        <div v-if="showCommunityPicker" style="width:100%; max-width:500px;">
          <CardPicker v-model="newCommunityTemp" :label="communityPickerLabel" :max="communityPickerMax" />
          <button class="btn btn-blue" style="margin-top:8px;" @click="confirmCommunityCards">确认公共牌</button>
        </div>

        <!-- 阶段控制 -->
        <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-top:8px;">
          <button v-if="canNextStage" class="btn btn-primary" @click="goNextStage">
            → {{ nextStageName }}
          </button>
          <template v-if="gameStore.stage === 'river' || gameStore.stage === 'showdown'">
            <button v-if="gameStore.stage !== 'showdown'" class="btn btn-red" @click="showSettleModal = true">比牌</button>
          </template>
          <button v-if="gameStore.stage === 'showdown'" class="btn btn-outline" @click="gameStore.newHand()">新一局</button>
        </div>
      </div>

      <!-- 右：Agent面板 -->
      <div style="width:320px; display:flex; flex-direction:column; gap:10px;">
        <div v-if="gameStore.analysis && gameStore.showAgentDetail" class="analysis-panel">
          <h4 style="color: var(--gold); margin-bottom:10px;">🧠 Agent 完整分析</h4>
          <div class="metric">
            <span class="metric-label">胜率</span>
            <span class="metric-value" :style="{ color: winRateColor }">{{ gameStore.analysis.win_rate }}%</span>
          </div>
          <div class="win-rate-bar">
            <div class="win-rate-fill" :style="{ width: gameStore.analysis.win_rate + '%', background: winRateColor }"></div>
          </div>
          <div class="metric" style="margin-top:6px;">
            <span class="metric-label">和/败</span>
            <span class="metric-value" style="font-size:13px;">{{ gameStore.analysis.tie_rate }}% / {{ gameStore.analysis.loss_rate }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">牌型</span>
            <span class="metric-value">{{ gameStore.analysis.hand_name }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">建议</span>
            <span class="metric-value" style="color:var(--gold)">{{ actionLabel }} {{ gameStore.analysis.suggested_amount > 0 ? gameStore.analysis.suggested_amount : '' }}</span>
          </div>
          <div v-if="gameStore.analysis.confidence" class="metric">
            <span class="metric-label">信心度</span>
            <span class="metric-value">{{ (gameStore.analysis.confidence * 100).toFixed(0) }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">决策来源</span>
            <span class="metric-value" :style="{ color: gameStore.analysis.decision_source === 'llm' ? 'var(--green)' : 'var(--text-dim)' }">
              {{ gameStore.analysis.decision_source === 'llm' ? '🧠 LLM' : '📋 规则引擎' }}
            </span>
          </div>
          <div v-if="gameStore.analysis.reasoning" style="margin-top:8px; padding:8px; background:rgba(255,255,255,0.03); border-radius:6px;">
            <div style="color:var(--text-dim); font-size:11px; margin-bottom:3px;">分析理由</div>
            <div style="font-size:12px; line-height:1.5;">{{ gameStore.analysis.reasoning }}</div>
          </div>
          <div v-if="gameStore.analysis.opponent_range" style="margin-top:6px; padding:8px; background:rgba(255,255,255,0.03); border-radius:6px;">
            <div style="color:var(--text-dim); font-size:11px; margin-bottom:3px;">对手范围</div>
            <div style="font-size:12px; line-height:1.5;">{{ gameStore.analysis.opponent_range }}</div>
          </div>
          <div v-if="gameStore.analysis.risk_warning" style="margin-top:6px; padding:8px; background:rgba(239,68,68,0.1); border-radius:6px;">
            <div style="color:var(--red); font-size:11px; margin-bottom:3px;">⚠ 风险提示</div>
            <div style="font-size:12px; line-height:1.5; color:var(--red);">{{ gameStore.analysis.risk_warning }}</div>
          </div>
        </div>

        <!-- 结算结果 -->
        <div v-if="gameStore.handResult" class="analysis-panel">
          <h4 style="color: var(--gold); margin-bottom:8px;">🃏 对局结果</h4>
          <div style="font-size:13px;">赢家: <b style="color:var(--green)">{{ gameStore.handResult.winners.join(', ') }}</b></div>
          <div style="font-size:13px;">底池: {{ gameStore.handResult.pot }} | 每人赢: {{ gameStore.handResult.winAmount }}</div>
        </div>

        <!-- 筹码明细 -->
        <div class="analysis-panel">
          <h4 style="margin-bottom:8px;">筹码明细</h4>
          <div v-for="p in gameStore.players" :key="p.position" class="metric">
            <span class="metric-label">{{ p.position }}{{ p.isSelf ? '(我)' : '' }}</span>
            <span class="metric-value" style="font-size:13px;">💰 {{ p.chips }} <span v-if="p.totalBet > 0" style="color:var(--red)">(-{{ p.totalBet }})</span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 对手操作弹窗 -->
    <div v-if="showOpponentModal" style="position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100;">
      <div class="card" style="width:300px; text-align:center;">
        <h3 style="color:var(--gold); margin-bottom:12px;">{{ selectedOpponent.position }} 操作</h3>
        <div style="font-size:13px; color:var(--text-dim); margin-bottom:12px;">筹码: {{ selectedOpponent.chips }} | 已下注: {{ selectedOpponent.currentBet }}</div>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <button class="btn btn-blue" @click="oppAction('fold')">弃牌</button>
          <button class="btn btn-outline" @click="oppAction('check')" :disabled="oppMustCall">过牌</button>
          <button class="btn btn-green" @click="oppAction('call')" :disabled="!oppMustCall">跟注 {{ oppCallAmount }}</button>
          <button class="btn btn-primary" @click="showOppRaise = true">加注</button>
          <button class="btn btn-red" @click="oppAction('all-in')">All In ({{ selectedOpponent.chips }})</button>
        </div>
        <div v-if="showOppRaise" style="margin-top:8px; display:flex; gap:8px;">
          <input class="input" type="number" v-model.number="oppRaiseAmount" :min="minOppRaise" :max="selectedOpponent.chips + selectedOpponent.currentBet" style="flex:1;" />
          <button class="btn btn-primary" style="padding:6px 12px;" @click="oppConfirmRaise">确认</button>
        </div>
        <button class="btn btn-outline" style="margin-top:10px; width:100%;" @click="showOpponentModal = false">取消</button>
      </div>
    </div>

    <!-- 比牌弹窗 -->
    <div v-if="showSettleModal" style="position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100;">
      <div class="card" style="width:320px; text-align:center;">
        <h3 style="color:var(--gold); margin-bottom:12px;">选择赢家</h3>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <label v-for="p in activePlayers" :key="p.position" style="display:flex; align-items:center; gap:8px; padding:6px 10px; background:var(--bg-panel); border-radius:6px; cursor:pointer;">
            <input type="checkbox" :value="p.position" v-model="selectedWinners" />
            <span>{{ p.position }}{{ p.isSelf ? '(我)' : '' }}</span>
            <span style="margin-left:auto; font-size:12px; color:var(--gold);">💰 {{ p.chips }}</span>
          </label>
        </div>
        <button class="btn btn-primary" style="width:100%; margin-top:12px;" @click="confirmSettle" :disabled="selectedWinners.length === 0">确认结果</button>
        <button class="btn btn-outline" style="width:100%; margin-top:8px;" @click="showSettleModal = false">取消</button>
      </div>
    </div>

    <!-- 设置筹码弹窗 -->
    <div v-if="showChipsModal" style="position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100;">
      <div class="card" style="width:280px; text-align:center;">
        <h3 style="color:var(--gold); margin-bottom:12px;">设置 {{ editingPlayer?.position }} 筹码</h3>
        <input class="input" type="number" v-model.number="editChips" min="0" style="margin-bottom:12px;" />
        <div style="display:flex; gap:8px;">
          <button class="btn btn-primary" style="flex:1;" @click="confirmChips">确认</button>
          <button class="btn btn-outline" style="flex:1;" @click="showChipsModal = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import PlayerAvatar from '../components/PlayerAvatar.vue'
import CardPicker from '../components/CardPicker.vue'

const router = useRouter()
const gameStore = useGameStore()
const pickerForStage = ref('')

// 对手弹窗
const showOpponentModal = ref(false)
const selectedOpponent = ref(null)
const showOppRaise = ref(false)
const oppRaiseAmount = ref(0)

// 自己加注
const showSelfRaise = ref(false)
const selfRaiseAmount = ref(0)

// 选牌
const showHolePicker = ref(false)
const holeCardsTemp = ref('')
const showCommunityPicker = ref(false)
const newCommunityTemp = ref('')

// 比牌
const showSettleModal = ref(false)
const selectedWinners = ref([])

// 设置筹码
const showChipsModal = ref(false)
const editingPlayer = ref(null)
const editChips = ref(0)

const opponents = computed(() => gameStore.players.filter(p => !p.isSelf))
const activePlayers = computed(() => gameStore.players.filter(p => p.status !== 'fold'))

const isMyTurn = computed(() => {
  if (!gameStore.actingPosition || !gameStore.myPlayer) return false
  return gameStore.actingPosition === gameStore.myPlayer.position && gameStore.myPlayer.status === 'active'
})

function isOpponentTurn(pos) {
  return gameStore.actingPosition === pos && !gameStore.players.find(p => p.position === pos)?.isSelf
}

const maxBet = computed(() => Math.max(...gameStore.players.map(p => p.currentBet), 0))
const callAmount = computed(() => Math.max(0, maxBet.value - (gameStore.myPlayer?.currentBet || 0)))
const mustCall = computed(() => callAmount.value > 0)
const minRaise = computed(() => maxBet.value + gameStore.bigBlind)

const oppCallAmount = computed(() => {
  if (!selectedOpponent.value) return 0
  return Math.max(0, maxBet.value - selectedOpponent.value.currentBet)
})
const oppMustCall = computed(() => oppCallAmount.value > 0)
const minOppRaise = computed(() => maxBet.value + gameStore.bigBlind)

const winRateColor = computed(() => {
  const wr = gameStore.analysis?.win_rate || 0
  if (wr >= 60) return 'var(--green)'
  if (wr >= 40) return 'var(--gold)'
  return 'var(--red)'
})

const actionLabel = computed(() => {
  const map = { fold: '弃牌', check: '过牌', call: '跟注', raise: '加注' }
  return map[gameStore.analysis?.suggested_action] || '-'
})

const displayCommunityCards = computed(() => {
  if (!gameStore.communityCards) return []
  return gameStore.communityCards.split(' ').filter(c => c)
})

const displayHoleCards = computed(() => {
  const p = gameStore.players[gameStore.myIndex]
  if (!p?.holeCards) return []
  return p.holeCards.split(' ').filter(c => c)
})

const canNextStage = computed(() => {
  if (!gameStore.roundComplete) return false
  if (gameStore.stage === 'river') return false
  return ['preflop', 'flop', 'turn'].includes(gameStore.stage)
})

const nextStageName = computed(() => {
  const map = { preflop: '翻牌', flop: '转牌', turn: '河牌' }
  return map[gameStore.stage] || '下一轮'
})

const communityPickerLabel = computed(() => {
  if (gameStore.stage === 'preflop') return '选择翻牌(3张)'
  if (gameStore.stage === 'flop') return '选择转牌(1张)'
  return '选择河牌(1张)'
})

const communityPickerMax = computed(() => {
  return pickerForStage.value === 'preflop' ? 3 : 1
})

function cardColor(card) {
  if (!card) return ''
  const s = card.slice(-1).toLowerCase()
  return ['h', 'd'].includes(s) ? 'red' : 'black'
}

// 点击对手
function onOpponentClick(player) {
  if (gameStore.stage === 'setup') {
    editingPlayer.value = player
    editChips.value = player.chips
    showChipsModal.value = true
    return
  }
  if (gameStore.actingPosition !== player.position) return
  if (player.status !== 'active') return
  selectedOpponent.value = player
  showOppRaise.value = false
  showOpponentModal.value = true
}

// 对手操作
function oppAction(action) {
  if (!selectedOpponent.value) return
  const amount = action === 'call' ? maxBet.value : 0
  gameStore.setOpponentAction(selectedOpponent.value.position, action, amount)
  showOpponentModal.value = false
  showOppRaise.value = false
  autoAdvanceIfMyTurn()
}

function oppConfirmRaise() {
  if (!selectedOpponent.value || oppRaiseAmount.value <= 0) return
  gameStore.setOpponentAction(selectedOpponent.value.position, 'raise', oppRaiseAmount.value)
  showOpponentModal.value = false
  showOppRaise.value = false
  oppRaiseAmount.value = 0
  autoAdvanceIfMyTurn()
}

// 自己操作
function selfAction(action) {
  const amount = action === 'call' ? maxBet.value : 0
  gameStore.setSelfAction(action, amount)
  showSelfRaise.value = false
}

function openSelfRaise() {
  selfRaiseAmount.value = minRaise.value
  showSelfRaise.value = true
}

function confirmSelfRaise() {
  if (selfRaiseAmount.value <= 0) return
  gameStore.setSelfAction('raise', selfRaiseAmount.value)
  showSelfRaise.value = false
}

// 轮到自己时自动计算胜率
function autoAdvanceIfMyTurn() {
  if (isMyTurn.value && gameStore.myPlayer?.status === 'active' && gameStore.myPlayer?.holeCards) {
    gameStore.autoCalcWinRate()
  }
}

// 自己回合到来时自动算胜率
watch(() => gameStore.actingPosition, (pos) => {
  if (pos && isMyTurn.value && gameStore.myPlayer?.holeCards) {
    gameStore.autoCalcWinRate()
  }
})

// 请求完整Agent分析
async function requestFullAnalysis() {
  await gameStore.requestAnalysis()
}

// 手牌确认
function confirmHoleCards() {
  if (holeCardsTemp.value) {
    const idx = gameStore.myIndex
    if (idx >= 0) {
      gameStore.players[idx].holeCards = holeCardsTemp.value
    }
    showHolePicker.value = false
  }
}

// 公共牌确认
function confirmCommunityCards() {
  if (!newCommunityTemp.value) return
  if (pickerForStage.value === 'preflop') {
    gameStore.communityCards = newCommunityTemp.value
  } else {
    gameStore.communityCards = (gameStore.communityCards + ' ' + newCommunityTemp.value).trim()
  }
  newCommunityTemp.value = ''
  showCommunityPicker.value = false
  // 确认牌后才推进阶段
  gameStore.nextStage()
}

// 开始对局
function startHand() {
  const p = gameStore.players[gameStore.myIndex]
  if (!p?.holeCards) {
    alert('请先选择手牌')
    return
  }
  gameStore.startHand()
  showHolePicker.value = false
  if (isMyTurn.value) {
    gameStore.autoCalcWinRate()
  }
}

// 下一阶段
function goNextStage() {
  pickerForStage.value = gameStore.stage
  showCommunityPicker.value = true
  newCommunityTemp.value = ''
}

// 比牌
function confirmSettle() {
  if (selectedWinners.value.length === 0) return
  gameStore.settle(selectedWinners.value)
  showSettleModal.value = false
  selectedWinners.value = []
}

// 设置筹码
function confirmChips() {
  if (editingPlayer.value) {
    const idx = gameStore.players.findIndex(p => p.position === editingPlayer.value.position)
    gameStore.setPlayerChips(idx, editChips.value)
  }
  showChipsModal.value = false
}

function backToLobby() {
  router.push('/')
}
</script>