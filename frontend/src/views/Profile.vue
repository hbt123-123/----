<template>
  <el-card shadow="never" class="profile-card">
    <div class="title">个人中心</div>
    <el-descriptions :column="1" border style="max-width: 480px; margin: 16px 0">
      <el-descriptions-item label="姓名">{{ auth.user?.name }}</el-descriptions-item>
      <el-descriptions-item label="角色">{{ auth.role }}</el-descriptions-item>
      <el-descriptions-item label="学号">{{ auth.user?.student_id || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系方式">{{ auth.user?.contact || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider>修改密码</el-divider>
    <el-form :model="form" label-width="100px" style="max-width: 480px" @submit.prevent="onSubmit">
      <el-form-item label="原密码">
        <el-input v-model="form.oldPassword" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input
          v-model="form.newPassword"
          type="password"
          show-password
          placeholder="不少于 6 位"
        />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="form.confirm" type="password" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSubmit">提交修改</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { changePassword } from '@/api/auth'

const auth = useAuthStore()
const form = ref({ oldPassword: '', newPassword: '', confirm: '' })
const saving = ref(false)

async function onSubmit() {
  if (!form.value.oldPassword) return ElMessage.warning('请输入原密码')
  if (form.value.newPassword.length < 6) return ElMessage.warning('新密码不少于 6 位')
  if (form.value.newPassword !== form.value.confirm) return ElMessage.warning('两次新密码不一致')
  saving.value = true
  try {
    await changePassword(form.value.oldPassword, form.value.newPassword)
    ElMessage.success('密码已修改')
    form.value = { oldPassword: '', newPassword: '', confirm: '' }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-card {
  max-width: 720px;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
</style>
