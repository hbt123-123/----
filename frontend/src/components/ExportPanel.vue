<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">汇总表</div>
      <div class="actions">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="success" :icon="Download" :disabled="!rows.length" @click="download">下载 Excel</el-button>
      </div>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!loading && !rows.length" description="还没有团队/任务数据" :image-size="50" />
      <el-table v-else :data="rows" stripe border size="small" show-overflow-tooltip>
        <el-table-column prop="no" label="序号" width="55" fixed />
        <el-table-column prop="name" label="团队" min-width="100" fixed />
        <el-table-column prop="leader" label="队长" width="80" />
        <el-table-column prop="student_id" label="学号" width="110" />
        <el-table-column prop="contact" label="联系方式" width="110" />
        <el-table-column prop="advisor" label="指导老师" width="90" />
        <el-table-column
          v-for="(m, i) in materials"
          :key="i"
          :label="m.stage_name + '·' + m.material"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="statusType(row.statuses[i])" size="small">{{ row.statuses[i] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="审核备注" min-width="160" />
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import * as exportApi from '@/api/export'

const props = defineProps({ pid: { type: String, default: '' } })
const materials = ref([])
const rows = ref([])
const loading = ref(false)

function statusType(s) {
  return s === '已通过' ? 'success' : s === '已提交' ? 'primary' : s === '已打回' ? 'danger' : 'info'
}

async function load() {
  if (!props.pid) return
  loading.value = true
  try {
    const r = await exportApi.previewSummary(props.pid)
    materials.value = r.materials || []
    rows.value = r.rows || []
  } finally {
    loading.value = false
  }
}

function download() {
  window.open(exportApi.summaryDownloadUrl(props.pid))
}

watch(() => props.pid, load)
onMounted(load)
</script>

<style scoped>
.panel {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.actions {
  display: flex;
  gap: 8px;
}
</style>
