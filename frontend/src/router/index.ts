import { createRouter, createWebHistory } from 'vue-router'
import { useDateStore } from '@/stores/dateStore'

import EntranceView from '@/views/EntranceView.vue'
import ChatView from '@/views/ChatView.vue'
import RankingView from '@/views/RankingView.vue'
import CurrentView from '@/views/CurrentView.vue'
import HistoryView from '@/views/HistoryView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'entrance',
      component: EntranceView,
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
    },
    {
      path: '/ranking',
      name: 'ranking',
      component: RankingView,
    },
    {
      path: '/current',
      name: 'current',
      component: CurrentView,
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView,
    },
  ],
})

// Navigation guard to ensure user is logged in
router.beforeEach((to, from, next) => {
  const store = useDateStore()
  if (to.name !== 'entrance' && !store.name) {
    next({ name: 'entrance' })
  } else if (to.name === 'entrance' && store.name) {
    next({ name: 'chat' })
  } else {
    next()
  }
})

export default router
