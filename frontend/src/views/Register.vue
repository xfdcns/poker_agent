<template>
  <div class="page-center">
    <div class="form-box card">
      <h2>♠ 注册账号</h2>
      <div class="field">
        <label>用户名</label>
        <input class="input" v-model="form.username" placeholder="3-20个字符" />
      </div>
      <div class="field">
        <label>密码</label>
        <input class="input" type="password" v-model="form.password" placeholder="至少6位" />
      </div>
      <div class="field">
        <label>确认密码</label>
        <input class="input" type="password" v-model="form.confirmPwd" placeholder="再次输入密码" @keyup.enter="handleRegister" />
      </div>
      <div v-if="errorMsg" style="color: var(--red); font-size: 13px; margin-bottom: 12px;">{{ errorMsg }}</div>
      <button class="btn btn-primary" style="width:100%" @click="handleRegister" :disabled="loading">
        <span v-if="loading" class="loading-spinner"></span>
        <span v-else>注册</span>
      </button>
      <div style="text-align:center; margin-top:16px; color: var(--text-dim); font-size:13px;">
        已有账号？<router-link to="/login" style="color: var(--gold);">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api'

const router = useRouter()
const form = ref({ username: '', password: '', confirmPwd: '' })
const loading = ref(false)
const errorMsg = ref('')

async function handleRegister() {
  if (!form.value.username || !form.value.password) {
    errorMsg.value = '请填写用户名和密码'
    return
  }
  if (form.value.password !== form.value.confirmPwd) {
    errorMsg.value = '两次密码不一致'
    return
  }
  if (form.value.password.length < 6) {
    errorMsg.value = '密码至少6位'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await register({ username: form.value.username, password: form.value.password })
    if (res.code === 200) {
      alert('注册成功，请登录')
      router.push('/login')
    } else {
      errorMsg.value = res.message || '注册失败'
    }
  } catch (e) {
    errorMsg.value = '网络错误'
  } finally {
    loading.value = false
  }
}
</script>