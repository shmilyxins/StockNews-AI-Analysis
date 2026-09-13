<template>
  <div class="panel">
    <h3 class="card-title">搜索股票</h3>
    <el-input v-model="kw" placeholder="输入股票代码或名称，如 600519 / 茅台" size="large" @keyup.enter="doSearch" clearable>
      <template #append><el-button @click="doSearch">搜索</el-button></template>
    </el-input>
    <el-table :data="results" v-loading="searching" style="margin-top: 16px; cursor: pointer"
              @row-click="r => $router.push(`/stock/${r.code}`)">
      <el-table-column prop="code" label="代码" width="120" />
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="market" label="市场" />
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'

const kw = ref('')
const results = ref([])
const searching = ref(false)

async function doSearch() {
  if (!kw.value.trim()) return
  searching.value = true
  try {
    const r = await api.get('/stock/search', { params: { keyword: kw.value.trim() } })
    results.value = r.data
  } finally {
    searching.value = false
  }
}
</script>

<style scoped>
.panel { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
</style>
