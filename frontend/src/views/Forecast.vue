<template>
  <div class="panel">
    <h3 class="card-title">业绩预测 · 业绩报表
      <el-tag size="small" type="info">净利润同比 / 营收同比</el-tag>
    </h3>
    <div class="filters">
      <el-select v-model="reportDate" style="width: 170px" @change="load(1)">
        <el-option label="2026年中报" value="2026-06-30" />
        <el-option label="2026年一季报" value="2026-03-31" />
        <el-option label="2025年年报" value="2025-12-31" />
        <el-option label="2025年三季报" value="2025-09-30" />
      </el-select>
      <el-radio-group v-model="sort" @change="load(1)">
        <el-radio-button value="profit">净利润同比</el-radio-button>
        <el-radio-button value="rev">营收同比</el-radio-button>
        <el-radio-button value="date">最新公告</el-radio-button>
      </el-radio-group>
      <el-input v-model="industry" placeholder="行业筛选" clearable style="width: 160px" @input="filterLocal" />
      <span class="hint">数据来源：东方财富业绩报表（近似原站盈利预测模块）</span>
    </div>

    <el-table :data="paged" v-loading="loading" size="small" style="cursor: pointer; margin-top: 12px"
              @row-click="r => $router.push(`/stock/${r.code}`)">
      <el-table-column prop="date" label="公告日期" width="110" />
      <el-table-column label="股票" width="150">
        <template #default="{ row }">{{ row.name }}({{ row.code }})</template>
      </el-table-column>
      <el-table-column sortable :sort-by="'rev_pct'" prop="rev_pct" label="营收同比" width="120">
        <template #default="{ row }"><span :class="row.rev_pct >= 0 ? 'pct-up' : 'pct-down'">{{ row.rev_pct }}%</span></template>
      </el-table-column>
      <el-table-column sortable :sort-by="'profit_pct'" prop="profit_pct" label="净利润同比">
        <template #default="{ row }">
          <span :class="row.profit_pct >= 0 ? 'pct-up' : 'pct-down'" style="font-weight: 600">{{ row.profit_pct }}%</span>
        </template>
      </el-table-column>
      <el-table-column prop="eps" label="每股收益" width="100" />
      <el-table-column prop="industry" label="所属行业" />
    </el-table>

    <el-pagination layout="prev, pager, next, total" :total="filtered.length" :page-size="pageSize"
                   :current-page="page" @current-change="p => (page = p)" style="margin-top: 12px; justify-content: flex-end" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const loading = ref(true)
const rows = ref([])
const reportDate = ref('2026-06-30')
const sort = ref('profit')
const industry = ref('')
const page = ref(1)
const pageSize = 20

const filtered = computed(() => {
  let r = rows.value
  if (industry.value) r = r.filter(x => (x.industry || '').includes(industry.value))
  return r
})
const paged = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))

async function load(p = 1) {
  loading.value = true
  page.value = p
  try {
    const r = await api.get('/forecast', { params: { report_date: reportDate.value, sort: sort.value, size: 100 } })
    rows.value = r.data
  } finally {
    loading.value = false
  }
}
const filterLocal = () => { page.value = 1 }

onMounted(() => load())
</script>

<style scoped>
.panel { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.filters { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.hint { color: #aaa; font-size: 12px; }
</style>
