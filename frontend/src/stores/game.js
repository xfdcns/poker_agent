import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gameAction, gameSubmit, gameSettle } from '../api'

// 牌桌顺时针顺序（从BTN开始）
const AVATARS = ['🤵', '🧑‍💼', '👨‍💻', '👩‍🦰', '🧔', '👱‍♀️']

// 根据人数分配位置（顺时针顺序，保证BB始终存在）
const POS_MAP = {
  2: ['BTN', 'BB'],
  3: ['BTN', 'SB', 'BB'],
  4: ['BTN', 'SB', 'BB', 'UTG'],
  5: ['BTN', 'SB', 'BB', 'UTG', 'MP'],
  6: ['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO'],
}

export const useGameStore = defineStore('game', () => {
  const tableId = ref(null)
  const players = ref([])
  const myIndex = ref(-1)
  const communityCards = ref('')
  const stage = ref('setup')
  const potSize = ref(0)
  const bigBlind = ref(10)
  const smallBlind = ref(5)

  // 回合管理
  const actingPosition = ref(null)
  const roundActions = ref({})
  const roundComplete = ref(false)

  // Agent
  const analysis = ref(null)
  const loading = ref(false)
  const showAgentDetail = ref(false)

  // 结算
  const handResult = ref(null)

  const stageLabel = computed(() => {
    const map = {
      setup: '准备',
      preflop: '翻牌前',
      flop: '翻牌',
      turn: '转牌',
      river: '河牌',
      showdown: '摊牌'
    }
    return map[stage.value] || stage.value
  })

  const myPlayer = computed(() => players.value[myIndex.value])

  // 当前在局的位置列表（顺时针顺序，来自POS_MAP）
  const activePositions = computed(() => {
    return players.value.map(p => p.position)
  })

  // 当前轮的操作顺序
  // preflop: BB后一位开始，BB最后行动
  // postflop: BTN后一位开始（SB先行动），BTN最后行动
  const turnOrder = computed(() => {
    const positions = activePositions.value
    if (positions.length === 0) return []

    if (stage.value === 'preflop') {
      // preflop: 从BB后面一位开始，BB最后行动
      const bbIdx = positions.indexOf('BB')
      if (bbIdx < 0) return positions
      const start = (bbIdx + 1) % positions.length
      return positions.slice(start).concat(positions.slice(0, start))
    }

    // postflop: 从BTN后面一位开始（SB先行动），BTN最后行动
    const btnIdx = positions.indexOf('BTN')
    const start = (btnIdx + 1) % positions.length
    return positions.slice(start).concat(positions.slice(0, start))
  })

  // 还未行动的活跃玩家位置
  const pendingPositions = computed(() => {
    return turnOrder.value.filter(pos => {
      const p = players.value.find(pl => pl.position === pos)
      return p && p.status === 'active' && !roundActions.value[pos]
    })
  })

  function initPlayers(numPlayers, buyIn, myPosition, blind) {
    bigBlind.value = blind
    smallBlind.value = Math.floor(blind / 2)

    const positions = POS_MAP[numPlayers] || POS_MAP[6]
    players.value = positions.map((pos, i) => ({
      position: pos,
      chips: buyIn,
      currentBet: 0,
      totalBet: 0,
      status: 'active',
      isSelf: pos === myPosition,
      avatar: AVATARS[i] || '🃏',
      holeCards: ''
    }))

    myIndex.value = players.value.findIndex(p => p.isSelf)
    communityCards.value = ''
    stage.value = 'setup'
    potSize.value = 0
    roundActions.value = {}
    roundComplete.value = false
    analysis.value = null
    handResult.value = null
    actingPosition.value = null
    showAgentDetail.value = false
  }

  function setPlayerChips(index, chips) {
    if (index >= 0 && index < players.value.length) {
      players.value[index].chips = Math.max(0, chips)
    }
  }

  function setCommunityCards(cards) {
    communityCards.value = cards
  }

  function setHoleCards(cards) {
    if (myIndex.value >= 0) {
      players.value[myIndex.value].holeCards = cards
    }
  }

  function startHand() {
    players.value.forEach(p => {
      p.currentBet = 0
      p.totalBet = 0
      if (p.chips > 0) p.status = 'active'
      else p.status = 'fold'
    })

    // 下盲注
    // heads-up时BTN=SB
    const isHeadsUp = players.value.length === 2
    const sbPos = isHeadsUp ? 'BTN' : 'SB'
    const sb = players.value.find(p => p.position === sbPos && p.status === 'active')
    const bb = players.value.find(p => p.position === 'BB' && p.status === 'active')

    if (sb) {
      const amt = Math.min(smallBlind.value, sb.chips)
      sb.currentBet = amt; sb.totalBet = amt; sb.chips -= amt
      if (sb.chips === 0) sb.status = 'all-in'
    }
    if (bb) {
      const amt = Math.min(bigBlind.value, bb.chips)
      bb.currentBet = amt; bb.totalBet = amt; bb.chips -= amt
      if (bb.chips === 0) bb.status = 'all-in'
    }

    potSize.value = players.value.reduce((sum, p) => sum + p.currentBet, 0)
    stage.value = 'preflop'
    roundActions.value = {}
    roundComplete.value = false
    analysis.value = null
    handResult.value = null
    showAgentDetail.value = false
    startBettingRound()
  }

  function startBettingRound() {
    // 翻牌前保留盲注，其他阶段清零
    if (stage.value !== 'preflop') {
      players.value.forEach(p => { p.currentBet = 0 })
    }
    roundActions.value = {}
    roundComplete.value = false
    analysis.value = null
    showAgentDetail.value = false

    const next = pendingPositions.value[0]
    actingPosition.value = next || null
    if (!next) roundComplete.value = true
  }

  function setOpponentAction(position, action, amount = 0) {
    const player = players.value.find(p => p.position === position)
    if (!player || player.isSelf) return
    applyAction(player, action, amount)
    roundActions.value[position] = { action, amount }
    advanceTurn()
  }

  function setSelfAction(action, amount = 0) {
    const player = myPlayer.value
    if (!player) return
    applyAction(player, action, amount)
    roundActions.value[player.position] = { action, amount }
    if (tableId.value) {
      gameSubmit({
        table_id: tableId.value,
        action,
        amount: action === 'fold' || action === 'check' ? 0 : amount,
        stage: stage.value,
        pot_size: potSize.value
      }).catch(() => {})
    }
    advanceTurn()
  }

  function applyAction(player, action, amount) {
    if (action === 'fold') {
      player.status = 'fold'
    } else if (action === 'check') {
      // 无操作
    } else if (action === 'call') {
      const maxBet = Math.max(...players.value.map(p => p.currentBet), 0)
      const callAmt = Math.min(maxBet - player.currentBet, player.chips)
      player.chips -= callAmt
      player.currentBet += callAmt
      player.totalBet += callAmt
      potSize.value += callAmt
      if (player.chips === 0) player.status = 'all-in'
    } else if (action === 'raise') {
      const additional = Math.min(amount - player.currentBet, player.chips)
      player.chips -= additional
      player.currentBet += additional
      player.totalBet += additional
      potSize.value += additional
      if (player.chips === 0) player.status = 'all-in'
      // 加注后，清空其他活跃玩家的行动记录，让他们重新选择
      players.value.forEach(p => {
        if (p.position !== player.position && p.status === 'active') {
          delete roundActions.value[p.position]
        }
      })
    } else if (action === 'all-in') {
      const allAmt = player.chips
      player.currentBet += allAmt
      player.totalBet += allAmt
      potSize.value += allAmt
      player.chips = 0
      player.status = 'all-in'
      // all-in也相当于加注，清空其他人行动
      players.value.forEach(p => {
        if (p.position !== player.position && p.status === 'active') {
          delete roundActions.value[p.position]
        }
      })
    }
  }

  function advanceTurn() {
    const currentPos = actingPosition.value
    const order = turnOrder.value

    if (!currentPos) {
      const next = pendingPositions.value[0]
      actingPosition.value = next || null
      if (!next) roundComplete.value = true
      return
    }

    const currentIdx = order.indexOf(currentPos)

    // 从当前位置往后环形搜索下一个待行动玩家
    for (let i = 1; i <= order.length; i++) {
      const nextIdx = (currentIdx + i) % order.length
      const pos = order[nextIdx]
      const p = players.value.find(pl => pl.position === pos)
      if (p && p.status === 'active' && !roundActions.value[pos]) {
        actingPosition.value = pos
        return
      }
    }

    // 所有人都行动过了
    actingPosition.value = null
    roundComplete.value = true
  }

  function nextStage() {
    const order = ['preflop', 'flop', 'turn', 'river', 'showdown']
    const idx = order.indexOf(stage.value)
    if (idx < order.length - 1) {
      stage.value = order[idx + 1]
      startBettingRound()
    }
  }

  async function requestAnalysis() {
    loading.value = true
    try {
      const opponentBets = players.value
        .filter(p => !p.isSelf && p.status !== 'fold')
        .map(p => ({
          position: p.position,
          action: roundActions.value[p.position]?.action || 'call',
          amount: p.currentBet
        }))
      const res = await gameAction({
        table_id: tableId.value,
        stage: stage.value,
        community_cards: communityCards.value,
        hole_cards: myPlayer.value?.holeCards || '',
        opponent_bets: opponentBets,
        pot_size: potSize.value,
        num_opponents: players.value.filter(p => !p.isSelf && p.status !== 'fold').length
      })
      if (res.code === 200) {
        analysis.value = res.data
        showAgentDetail.value = true
      }
      return res
    } finally {
      loading.value = false
    }
  }

  async function autoCalcWinRate() {
    if (!myPlayer.value || myPlayer.value.status === 'fold') return
    if (!myPlayer.value.holeCards) return
    loading.value = true
    try {
      const res = await gameAction({
        table_id: tableId.value,
        stage: stage.value,
        community_cards: communityCards.value,
        hole_cards: myPlayer.value?.holeCards || '',
        opponent_bets: players.value
          .filter(p => !p.isSelf && p.status !== 'fold')
          .map(p => ({
            position: p.position,
            action: roundActions.value[p.position]?.action || 'call',
            amount: p.currentBet
          })),
        pot_size: potSize.value,
        num_opponents: players.value.filter(p => !p.isSelf && p.status !== 'fold').length,
        analysis_type: 'winrate'
      })
      if (res.code === 200) {
        analysis.value = res.data
        showAgentDetail.value = false
      }
    } catch (e) {
      console.error('自动胜率计算失败:', e)
    } finally {
      loading.value = false
    }
  }

  function settle(winnerPositions) {
    const totalPot = potSize.value
    const winPerPlayer = Math.floor(totalPot / winnerPositions.length)
    winnerPositions.forEach(pos => {
      const p = players.value.find(pl => pl.position === pos)
      if (p) p.chips += winPerPlayer
    })
    handResult.value = {
      winners: winnerPositions,
      pot: totalPot,
      winAmount: winPerPlayer
    }
    stage.value = 'showdown'
    actingPosition.value = null
    if (tableId.value) {
      const profit = winnerPositions.includes(myPlayer.value?.position)
        ? winPerPlayer
        : -(myPlayer.value?.totalBet || 0)
      gameSettle({
        table_id: tableId.value,
        result: winnerPositions.includes(myPlayer.value?.position) ? 'win' : 'lose',
        profit,
        opponent_hands: [],
        notes: ''
      }).catch(() => {})
    }
  }

  function newHand() {
    players.value.forEach(p => {
      p.currentBet = 0
      p.totalBet = 0
      p.holeCards = ''
      p.status = p.chips <= 0 ? 'fold' : 'active'
    })
    communityCards.value = ''
    potSize.value = 0
    stage.value = 'setup'
    roundActions.value = {}
    roundComplete.value = false
    analysis.value = null
    handResult.value = null
    actingPosition.value = null
    showAgentDetail.value = false
  }

  return {
    tableId, players, myIndex, communityCards, stage, potSize,
    bigBlind, smallBlind, actingPosition, roundActions, roundComplete,
    analysis, loading, showAgentDetail, handResult,
    stageLabel, myPlayer, turnOrder, pendingPositions,
    initPlayers, setPlayerChips, setCommunityCards, setHoleCards,
    startHand, setOpponentAction, setSelfAction, advanceTurn, nextStage,
    requestAnalysis, autoCalcWinRate, settle, newHand
  }
}, {
  persist: {
    pick: ['tableId', 'players', 'myIndex', 'communityCards', 'stage', 'potSize', 'bigBlind', 'smallBlind', 'handResult']
  }
})
