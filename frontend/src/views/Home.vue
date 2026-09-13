<template>
  <div v-loading="loading">
    <!-- 市场概览 -->
    <div class="panel">
      <h3 class="card-title">市场概览</h3>
      <div class="idx-row">
        <div v-for="i in indices" :key="i.code" class="idx-card" :class="i.pct >= 0 ? 'up' : 'down'">
          <div class="idx-name">{{ i.name }}</div>
          <div class="idx-price">{{ i.price }}</div>
          <div>{{ i.chg }} ({{ i.pct }}%)</div>
        </div>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 市场资讯 -->
      <el-col :span="10">
        <div class="panel">
          <h3 class="card-title">市场资讯 <el-tag size="small" type="info">7×24 快讯</el-tag></h3>
          <div v-for="n in news.slice(0, 12)" :key="n.time + n.title" class="news-item news-click"
               @click="openNews(n)">
            <div class="news-title">{{ n.important ? '🔴 ' : '' }}{{ n.title }}</div>
            <div class="news-summary">{{ n.summary }}</div>
            <div class="news-time">{{ n.time }}<span v-if="n.url" class="news-link"> 查看原文 ↗</span></div>
            <el-divider style="margin: 8px 0" />
          </div>
        </div>
      </el-col>

      <el-col :span="14">
        <!-- 长线风口龙头 -->
        <div class="panel">
          <h3 class="card-title">长线风口龙头</h3>
          <el-row :gutter="12">
            <el-col :span="6" v-for="b in leaders" :key="b.board_code" style="margin-bottom: 12px">
              <el-card shadow="hover" class="leader-card" @click="goStock(b.leader_code)">
                <div class="lc-board">{{ b.board }} <span :class="b.pct >= 0 ? 'pct-up' : 'pct-down'">{{ b.pct }}%</span></div>
                <div class="lc-leader">{{ b.leader }} <span class="lc-code">{{ b.leader_code }}</span></div>
                <div :class="b.leader_pct >= 0 ? 'pct-up' : 'pct-down'">领涨 {{ b.leader_pct }}%</div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 机构调研推荐热门股 -->
        <div class="panel">
          <h3 class="card-title">机构调研推荐热门股 <el-tag size="small">简化评分模型</el-tag></h3>
          <el-table :data="hotBurst" size="small" @row-click="r => goStock(r.code)" style="cursor: pointer">
            <el-table-column label="行情" width="120">
              <template #default="{ row }">
                <span class="pct-up">{{ row.price }}</span>
                <span :class="row.pct >= 0 ? 'pct-up' : 'pct-down'" style="margin-left: 6px">{{ row.pct }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="股票" width="110">
              <template #default="{ row }">{{ row.name }}<div class="lc-code">{{ row.code }}</div></template>
            </el-table-column>
            <el-table-column prop="level" label="等级" width="70">
              <template #default="{ row }">
                <el-tag :type="row.level === '高' ? 'danger' : row.level === '中' ? 'warning' : 'info'" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="keyword" label="关键词" />
            <el-table-column prop="score" label="得分" width="70" sortable />
            <el-table-column prop="board" label="板块" />
          </el-table>
        </div>

        <!-- 盈利预测更新榜 -->
        <div class="panel">
          <h3 class="card-title">盈利预测更新榜（业绩报表·净利润同比）</h3>
          <el-table :data="forecast" size="small" height="360" @row-click="r => goStock(r.code)" style="cursor: pointer">
            <el-table-column prop="date" label="更新时间" width="110" />
            <el-table-column label="股票" width="160">
              <template #default="{ row }">{{ row.name }}({{ row.code }})</template>
            </el-table-column>
            <el-table-column label="营收同比" width="110">
              <template #default="{ row }"><span :class="row.rev_pct >= 0 ? 'pct-up' : 'pct-down'">{{ row.rev_pct }}%</span></template>
            </el-table-column>
            <el-table-column label="净利润同比">
              <template #default="{ row }"><span :class="row.profit_pct >= 0 ? 'pct-up' : 'pct-down'">{{ row.profit_pct }}%</span></template>
            </el-table-column>
            <el-table-column prop="industry" label="板块" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const loading = ref(true)
const indices = ref([])
const news = ref([])
const leaders = ref([])
const hotBurst = ref([])
const forecast = ref([])

const goStock = code => code && router.push(`/stock/${code}`)
const openNews = n => n.url && window.open(n.url, '_blank')

onMounted(async () => {
  try {
    const [i, n, l, h, f] = await Promise.all([
      api.get('/indices'), api.get('/news?size=20'), api.get('/hot-leaders'),
      api.get('/hot-burst'), api.get('/forecast?size=30')
    ])
    indices.value = i.data; news.value = n.data; leaders.value = l.data
    hotBurst.value = h.data; forecast.value = f.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.panel { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.idx-row { display: flex; gap: 12px; flex-wrap: wrap; }
.idx-card { flex: 1; min-width: 140px; background: #fafafa; border-radius: 8px; padding: 10px 14px; }
.idx-card.up { border-top: 3px solid #f56c6c; }
.idx-card.down { border-top: 3px solid #67c23a; }
.idx-name { font-weight: 600; }
.idx-price { font-size: 22px; font-weight: 700; margin: 2px 0; }
.idx-card.up .idx-price { color: #f56c6c; }
.idx-card.down .idx-price { color: #67c23a; }
.news-title { font-weight: 600; font-size: 14px; }
.news-summary { color: #666; font-size: 13px; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.news-time { color: #aaa; font-size: 12px; margin-top: 2px; }
.news-click { cursor: pointer; border-radius: 6px; padding: 4px 6px; margin: 0 -6px; transition: background .15s; }
.news-click:hover { background: #f0f7ff; }
.news-click:hover .news-title { color: #409eff; }
.news-link { color: #409eff; margin-left: 8px; }
.leader-card { cursor: pointer; }
.lc-board { font-weight: 700; font-size: 13px; }
.lc-leader { margin: 6px 0; font-size: 15px; }
.lc-code { color: #999; font-size: 12px; }
</style>
