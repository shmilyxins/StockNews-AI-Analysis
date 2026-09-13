<template>
  <div class="panel">
    <h3 class="card-title">趋势股评分
      <el-tag size="small" type="info">四因子模型 · 实时</el-tag>
      <el-button size="small" style="margin-left: 12px" @click="load" :loading="loading">刷新</el-button>
    </h3>
    <el-alert type="info" :closable="false" style="margin-bottom: 12px">
      <p style="margin:0">评分 = 60日动量(35%) + 主力资金净流入(25%) + 量比(20%) + 换手活跃度(20%)，按样本内分位数归一。
      样本为全市场 60 日涨幅前 200 名（剔除 ST/停牌），取综合评分 Top50。仅供学习研究，不构成投资建议。</p>
    </el-alert>

    <el-table :data="rows" v-loading="loading" size="small" style="cursor: pointer"
              @row-click="r => $router.push(`/stock/${r.code}`)">
      <el-table-column type="index" label="#" width="55" />
      <el-table-column label="股票" width="150">
        <template #default="{ row }">{{ row.name }}<div class="code">{{ row.code }}</div></template>
      </el-table-column>
      <el-table-column label="现价" width="100">
        <template #default="{ row }">
          <span class="pct-up">{{ row.price }}</span>
          <span :class="row.pct >= 0 ? 'pct-up' : 'pct-down'" style="margin-left:4px; font-size:12px">{{ row.pct }}%</span>
        </template>
      </el-table-column>
      <el-table-column sortable prop="mom60" label="60日涨幅%" width="110">
        <template #default="{ row }"><span class="pct-up">{{ row.mom60 }}%</span></template>
      </el-table-column>
      <el-table-column prop="vol_ratio" label="量比" width="80" />
      <el-table-column prop="turnover" label="换手率%" width="90" />
      <el-table-column sortable prop="flow_wan" label="主力净流入(万)" width="140">
        <template #default="{ row }">
          <span :class="row.flow_wan >= 0 ? 'pct-up' : 'pct-down'">{{ row.flow_wan >= 0 ? '+' : '' }}{{ row.flow_wan }}</span>
        </template>
      </el-table-column>
      <el-table-column label="评分" width="180">
        <template #default="{ row }">
          <el-progress :percentage="row.score" :stroke-width="10"
                       :color="row.score >= 75 ? '#f56c6c' : row.score >= 55 ? '#e6a23c' : '#909399'" />
        </template>
      </el-table-column>
      <el-table-column prop="level" label="等级" width="80">
        <template #default="{ row }">
          <el-tag :type="row.level === '高' ? 'danger' : row.level === '中' ? 'warning' : 'info'" size="small">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const rows = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const r = await api.get('/trend-score')
    rows.value = r.data
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<style scoped>
.panel { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.code { color: #999; font-size: 12px; }
</style>
