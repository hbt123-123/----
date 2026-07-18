<template>
  <div class="dashboard">
    <el-card
      shadow="never"
      v-motion
      :initial="{ opacity: 0, y: 20 }"
      :enter="{ opacity: 1, y: 0 }"
    >
      <div class="welcome">
        <div class="hello">你好,{{ auth.user?.name }} 👋</div>
        <div class="role">当前角色: {{ auth.role }}</div>
        <div class="desc">欢迎使用创实部信息化管理平台。左侧菜单可进入相应功能模块。</div>
      </div>
    </el-card>
    <el-card
      shadow="never"
      class="tips"
      v-motion
      :initial="{ opacity: 0, y: 20 }"
      :enter="{ opacity: 1, y: 0, transition: { delay: 120 } }"
    >
      <div class="tips-title">提示</div>
      <ul>
        <li>部长可在「成员管理」创建副部长、干事账号并批量导入。</li>
        <li>新成员首次登录时,从姓名下拉选择自己并设置密码完成激活。</li>
        <li>项目、阶段、任务管理等模块将在后续阶段开放。</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<style scoped>
.dashboard {
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.welcome .hello {
  font-size: 20px;
  font-weight: 600;
  color: #0c0d0e;
}
.welcome .role {
  color: #737a87;
  margin-top: 6px;
  font-size: 13px;
}
.welcome .desc {
  color: #42464e;
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.7;
}
.tips-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #0c0d0e;
  font-size: 14px;
}
ul {
  margin: 0;
  padding-left: 20px;
  color: #42464e;
  line-height: 2;
  font-size: 13px;
}
</style>