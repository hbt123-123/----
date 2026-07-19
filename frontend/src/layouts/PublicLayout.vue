<template>
  <div class="public-layout">
    <header class="public-header">
      <div class="header-inner">
        <div class="brand" @click="router.push('/public/projects')">
          <el-icon class="brand-icon"><HomeFilled /></el-icon>
          <span class="brand-title">创实部管理平台</span>
          <el-tag size="small" type="info" effect="plain" class="guest-tag">游客</el-tag>
        </div>
        <div class="header-actions">
          <el-button type="primary" plain size="small" @click="goLogin">登录</el-button>
        </div>
      </div>
    </header>
    <main class="public-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" v-if="Component" />
        </transition>
      </router-view>
    </main>
    <footer class="public-footer">
      <span>资源与环境学院 · 团委学生会创新实践部</span>
      <span class="dot">·</span>
      <span>游客仅可浏览公开项目概览</span>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
function goLogin() {
  router.push('/login')
}
</script>

<style scoped>
.public-layout {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: #f1f3f5;
}
.public-header {
  background: #0c0d0e;
  color: #ffffff;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: 100%;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}
.brand-icon {
  font-size: 20px;
  color: #1664ff;
}
.brand-title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.guest-tag {
  margin-left: 4px;
}
.public-main {
  flex: 1;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  padding: 24px 20px;
  box-sizing: border-box;
}
.public-footer {
  text-align: center;
  padding: 18px 12px;
  font-size: 12px;
  color: #737a87;
  background: #ffffff;
  border-top: 1px solid #eaedf1;
}
.public-footer .dot {
  margin: 0 6px;
}

/* 移动端 */
@media (max-width: 767px) {
  .header-inner {
    padding: 0 12px;
  }
  .brand-title {
    font-size: 14px;
  }
  .public-main {
    padding: 16px 12px;
  }
}
@media (max-width: 419px) {
  .brand-title {
    display: none;
  }
}
</style>