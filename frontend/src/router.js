import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Search from './views/Search.vue'
import Forecast from './views/Forecast.vue'
import Trend from './views/Trend.vue'
import StockDetail from './views/StockDetail.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/search', component: Search },
    { path: '/forecast', component: Forecast },
    { path: '/trend', component: Trend },
    { path: '/stock/:qid', component: StockDetail }
  ]
})
