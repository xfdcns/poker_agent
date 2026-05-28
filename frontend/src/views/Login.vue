<template>
  <div class="page-center">
    <div class="form-box card">
      <h2>♠ Poker Agent</h2>
      <div class="field">
        <label>用户名</label>
        <input class="input" v-model="form.username" placeholder="输入用户名" @keyup.enter="handleLogin" />
      </div>
      <div class="field">
        <label>密码</label>
        <input class="input" type="password" v-model="form.password" placeholder="输入密码" @keyup.enter="handleLogin" />
      </div>
      <div v-if="errorMsg" style="color: var(--red); font-size: 13px; margin-bottom: 12px;">{{ errorMsg }}</div>
      <button class="btn btn-primary" style="width:100%" @click="handleLogin" :disabled="loading">
        <span v-if="loading" class="loading-spinner"></span>
        <span v-else>登录</span>
      </button>
      <div style="text-align:center; margin-top:16px; color: var(--text-dim); font-size:13px;">
        没有账号？<router-link to="/register" style="color: var(--gold);">去注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { login } from '../api'

const router = useRouter()
const userStore = useUserStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    errorMsg.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await login(form.value)
    if (res.code === 200) {
      userStore.setLogin({
        token: res.data.token,
        user_id: res.data.userInfo?.id || res.data.userInfo?.user_id || '',
        username: res.data.userInfo?.username || 'Player'
      })
      router.push('/')
    } else {
      errorMsg.value = res.message || '登录失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误'
  } finally {
    loading.value = false
  }
}
</script>