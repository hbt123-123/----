<template>
  <div class="login-wrap">
    <el-card
      class="login-card"
      v-motion
      :initial="{ opacity: 0, y: 30 }"
      :enter="{ opacity: 1, y: 0, transition: { duration: 400 } }"
    >
      <div class="brand">
        <div class="brand-title">创实部信息化管理平台</div>
        <div class="brand-sub">资源与环境学院 · 团委学生会创新实践部</div>
      </div>
      <el-form :model="form" @submit.prevent="onSubmit" label-position="top">
        <el-form-item label="选择姓名">
          <el-select
            v-model="form.userId"
            filterable
            clearable
            placeholder="输入姓名搜索并选择"
            style="width: 100%"
            :loading="loadingCandidates"
            @change="onSelect"
          >
            <el-option
              v-for="c in candidates"
              :key="c.id"
              :label="displayLabel(c)"
              :value="c.id"
            >
              <span>{{ c.name }}</span>
              <span class="opt-sub" v-if="c.student_id">（{{ c.student_id }}）</span>
              <el-tag v-if="c.is_admin" size="small" type="danger" effect="plain">管理员</el-tag>
              <el-tag v-else-if="!c.activated" size="small" type="warning" effect="plain">未激活</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="pwdLabel">
          <el-input
            v-model="form.password"
            :type="showPwd ? 'text' : 'password'"
            :placeholder="pwdPlaceholder"
            autocomplete="off"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
            <template #append>
              <el-icon class="eye-btn" @click="showPwd = !showPwd">
                <View v-if="!showPwd" /><Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          :loading="submitting"
          size="large"
          style="width: 100%"
        >
          {{ isActivate ? '设置密码并登录' : '登录' }}
        </el-button>
      </el-form>
      <div class="hint" v-if="hint">{{ hint }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { candidates as fetchCandidates } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const candidates = ref([])
const loadingCandidates = ref(false)
const submitting = ref(false)
const showPwd = ref(false)
const form = ref({ userId: '', password: '' })

const selectedUser = computed(() =>
  candidates.value.find((c) => c.id === form.value.userId)
)
const isActivate = computed(() => !!selectedUser.value && !selectedUser.value.activated)

const pwdLabel = computed(() => (isActivate.value ? '设置初始密码' : '密码'))
const pwdPlaceholder = computed(() =>
  isActivate.value ? '请设置不少于 6 位的密码' : '请输入密码'
)
const hint = computed(() => {
  if (!selectedUser.value) return ''
  if (isActivate.value) return '首次登录,请设置密码完成账号激活'
  if (selectedUser.value.is_admin) return '管理员初始密码:12345678'
  return ''
})

function displayLabel(c) {
  let s = c.name
  if (c.student_id) s += `(${c.student_id})`
  return s
}

function onSelect() {
  form.value.password = ''
}

async function loadCandidates() {
  loadingCandidates.value = true
  try {
    candidates.value = await fetchCandidates()
  } finally {
    loadingCandidates.value = false
  }
}

async function onSubmit() {
  if (!form.value.userId) return ElMessage.warning('请先选择姓名')
  if (!form.value.password) return ElMessage.warning(isActivate.value ? '请设置密码' : '请输入密码')
  submitting.value = true
  try {
    const res = await auth.login(form.value.userId, form.value.password)
    if (res.activated_now) ElMessage.success('账号已激活,欢迎使用')
    router.replace(route.query.redirect || '/')
  } catch (e) {
    // 错误已由 axios 拦截器提示
  } finally {
    submitting.value = false
  }
}

onMounted(loadCandidates)
</script>

<style scoped>
.login-wrap {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #0c0d0e 0%, #1d2129 40%, #2b303a 100%);
  padding: 20px;
}
.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.04);
  border: none;
}
.brand {
  text-align: center;
  margin-bottom: 28px;
}
.brand-title {
  font-size: 18px;
  font-weight: 600;
  color: #0c0d0e;
  letter-spacing: 0.5px;
}
.brand-sub {
  font-size: 12px;
  color: #737a87;
  margin-top: 8px;
}
.eye-btn {
  cursor: pointer;
}
.opt-sub {
  color: #737a87;
  font-size: 12px;
  margin: 0 4px;
}
.hint {
  margin-top: 14px;
  font-size: 12px;
  color: #bd7e00;
  text-align: center;
}
</style>