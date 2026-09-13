<template>
  <el-container>
    <el-header class="topbar">
      <div class="brand" @click="$router.push('/')">📊 股票资讯AI智能分析</div>
      <el-menu mode="horizontal" :default-active="$route.path" router class="nav">
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item index="/search">搜索股票</el-menu-item>
        <el-menu-item index="/forecast">业绩预测</el-menu-item>
        <el-menu-item index="/trend">趋势股评分</el-menu-item>
      </el-menu>
    </el-header>
    <el-main><router-view /></el-main>
    <el-footer class="foot">
      © 2026 股票资讯AI智能分析 · 仅供学习研究，不构成投资建议 · 数据来源：东方财富公开接口
    </el-footer>
  </el-container>
</template>

<style>
body { margin: 0; background: #f5f6f8; font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif; }
.topbar { display: flex; align-items: center; gap: 24px; background: #fff; border-bottom: 1px solid #eee; }
.brand { font-size: 18px; font-weight: 700; color: #1f2d3d; cursor: pointer; white-space: nowrap; }
.nav { flex: 1; border-bottom: none !important; }
.foot { text-align: center; color: #999; font-size: 12px; background: #fff; }
.pct-up { color: #f56c6c; }
.pct-down { color: #67c23a; }
.card-title { font-size: 16px; font-weight: 700; border-left: 4px solid #409eff; padding-left: 8px; margin: 0 0 12px; }
</style>
