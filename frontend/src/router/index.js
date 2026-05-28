import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/', name: 'Lobby', component: () => import('../views/Lobby.vue'), meta: { auth: true } },
  { path: '/game', name: 'Game', component: () => import('../views/Game.vue'), meta: { auth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.auth && !userStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router