<template>
  <div v-loading="loading">
    <div class="panel" v-if="profile">
      <h3 class="card-title">
        {{ profile.name }}({{ profile.code }})
        <span :class="(profile.pct || 0) >= 0 ? 'pct-up' : 'pct-down'" style="font-size: 22px; margin-left: 12px">
          {{ profile.price }} ({{ profile.pct }}%)
        </span>
      </h3>
      <el-descriptions :column="4" size="small">
        <el-descriptions-item label="今开">{{ profile.open }}</el-descriptions-item>
        <el-descriptions-item label="最高">{{ profile.high }}</el-descriptions-item>
        <el-descriptions-item label="最低">{{ profile.low }}</el-descriptions-item>
        <el-descriptions-item label="换手率">{{ profile.turnover }}%</el-descriptions-item>
        <el-descriptions-item label="市盈率">{{ profile.pe }}</el-descriptions-item>
        <el-descriptions-item label="市净率">{{ profile.pb }}</el-descriptions-item>
        <el-descriptions-item label="总市值">{{ formatCap(profile.mktcap) }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="panel">
      <h3 class="card-title">日K线</h3>
      <div v-if="klineError" class="kline-err">K线数据加载失败（数据源限流），请稍后刷新重试</div>
      <div v-show="!klineError" ref="klineEl" style="height: 420px"></div>
    </div>

    <div class="panel">
      <h3 class="card-title">AI 智能分析
        <el-tag size="small" :type="ai.mode === 'llm' ? 'success' : 'info'">{{ ai.mode === 'llm' ? 'LLM 分析' : '规则分析' }}</el-tag>
      </h3>
      <pre class="ai-content">{{ ai.content || '加载中…' }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '../api'

const route = useRoute()
const loading = ref(true)
const profile = ref(null)
const ai = ref({})
const klineEl = ref()
const klineError = ref(false)

const formatCap = v => v ? (v > 1e8 ? (v / 1e8).toFixed(0) + '亿' : v) : '-'

onMounted(async () => {
  const qid = route.params.qid
  const isQid = /^\d+\./.test(qid)
  const secid = isQid ? qid : (/^[69]/.test(qid) ? `1.${qid}` : `0.${qid}`)
  try {
    const [p, k, a] = await Promise.all([
      api.get(`/stock/${secid}/profile`).catch(() => null),
      api.get(`/stock/${secid}/kline`, { params: { days: 120 } })
        .then(r => r.data)
        .catch(() => { klineError.value = true; return null }),
      api.get(`/stock/${secid}/ai-analysis`)
    ])
    profile.value = p ? p.data : null
    ai.value = a.data
    if (k) {
      await nextTick()
      renderKline(k.klines)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function renderKline(klines) {
  const chart = echarts.init(klineEl.value)
  const dates = klines.map(k => k.date)
  const ohlc = klines.map(k => [k.open, k.close, k.low, k.high])
  const vols = klines.map(k => k.volume)
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: 60, right: 20, top: 10, height: '58%' }, { left: 60, right: 20, top: '72%', height: '20%' }],
    xAxis: [
      { type: 'category', data: dates },
      { type: 'category', gridIndex: 1, data: dates, axisLabel: { show: false } }
    ],
    yAxis: [{ scale: true }, { gridIndex: 1, axisLabel: { show: false } }],
    dataZoom: [{ type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 }],
    series: [
      { type: 'candlestick', data: ohlc,
        itemStyle: { color: '#f56c6c', color0: '#67c23a', borderColor: '#f56c6c', borderColor0: '#67c23a' } },
      { type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: vols, itemStyle: { color: '#8fb7f5' } }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
}
</script>

<style scoped>
.panel { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.ai-content { white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.8; margin: 0; }
</style>
