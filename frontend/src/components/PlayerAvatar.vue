<template>
  <div class="player-seat" :class="seatClass">
    <div class="avatar-circle" @click="$emit('click')">
      <span class="avatar-emoji">{{ player.avatar }}</span>
      <span v-if="player.status === 'fold'" class="status-badge fold-badge">FOLD</span>
      <span v-if="player.status === 'all-in'" class="status-badge allin-badge">ALL IN</span>
    </div>
    <div class="player-info">
      <div class="player-pos">{{ player.position }}{{ player.isSelf ? '(我)' : '' }}</div>
      <div class="player-chips">💰 {{ player.chips }}</div>
      <div v-if="player.currentBet > 0" class="player-bet">下注: {{ player.currentBet }}</div>
    </div>
    <div v-if="isCurrentTurn" class="turn-indicator">⬇ 轮到你了</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  player: { type: Object, required: true },
  isCurrentTurn: { type: Boolean, default: false }
})

defineEmits(['click'])

const seatClass = computed(() => ({
  'is-self': props.player.isSelf,
  'is-fold': props.player.status === 'fold',
  'is-allin': props.player.status === 'all-in',
  'is-active-turn': props.isCurrentTurn
}))
</script>

<style scoped>
.player-seat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}
.avatar-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
}
.avatar-circle:hover {
  border-color: var(--gold);
  transform: scale(1.05);
}
.is-active-turn .avatar-circle {
  border-color: var(--gold);
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.5);
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 12px rgba(245, 158, 11, 0.5); }
  50% { box-shadow: 0 0 20px rgba(245, 158, 11, 0.8); }
}
.is-self .avatar-circle {
  border-color: var(--blue);
}
.is-fold {
  opacity: 0.4;
}
.is-fold .avatar-circle {
  border-color: var(--red);
}
.is-allin .avatar-circle {
  border-color: var(--green);
}
.avatar-emoji {
  font-size: 28px;
}
.status-badge {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}
.fold-badge {
  background: var(--red);
  color: #fff;
}
.allin-badge {
  background: var(--green);
  color: #fff;
}
.player-info {
  text-align: center;
}
.player-pos {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}
.player-chips {
  font-size: 11px;
  color: var(--gold);
}
.player-bet {
  font-size: 10px;
  color: var(--green);
  background: rgba(34, 197, 94, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
  margin-top: 2px;
}
.turn-indicator {
  font-size: 10px;
  color: var(--gold);
  font-weight: 600;
  margin-top: 2px;
}
</style>