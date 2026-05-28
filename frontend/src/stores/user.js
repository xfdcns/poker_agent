import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('poker_token') || '')
  const userId = ref(localStorage.getItem('poker_user_id') || '')
  const username = ref(localStorage.getItem('poker_username') || '')

  function setLogin(data) {
    token.value = data.token
    userId.value = data.user_id
    username.value = data.username
    localStorage.setItem('poker_token', data.token)
    localStorage.setItem('poker_user_id', data.user_id)
    localStorage.setItem('poker_username', data.username)
  }

  function logout() {
    token.value = ''
    userId.value = ''
    username.value = ''
    localStorage.removeItem('poker_token')
    localStorage.removeItem('poker_user_id')
    localStorage.removeItem('poker_username')
  }

  return { token, userId, username, setLogin, logout }
})