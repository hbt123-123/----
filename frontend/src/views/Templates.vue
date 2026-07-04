<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">比赛模板</div>
        <div class="actions">
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <div v-loading="loading">
        <el-empty v-if="!loading && !templates.length" description="还没有模板" />

        <el-row :gutter="16">
          <el-col
            v-for="t in templates"
            :key="t.id"
            :xs="24"
            :md="12"
            class="tpl-col"
          >
            <el-card shadow="hover" class="tpl-card">
              <template #header>
                <div class="tpl-head">
                  <span class="tpl-name">{{ t.name }}</span>
                  <div class="tpl-tags">
                    <el-tag size="small" type="info">{{ t.stages.length }} 个阶段</el-tag>
                    <el-tag v-if="hasDefense(t)" size="small" type="warning">含答辩</el-tag>
                    <el-tag v-else size="small" type="success">无答辩</el-tag>
                  </div>
                </div>
              </template>

              <el-timeline class="stage-line">
                <el-timeline-item
                  v-for="(s, i) in t.stages"
                  :key="i"
                  :timestamp="s.duration_days ? `建议 ${s.duration_days} 天` : '未设时长'"
                  placement="top"
                  :type="s.need_defense ? 'warning' : 'primary'"
                  :hollow="!s.need_defense"
                >
                  <div class="stage-name">
                    <span class="stage-no">{{ s.order }}</span>
                    <span>{{ s.name }}</span>
                    <el-tag v-if="s.need_defense" size="small" type="warning" effect="plain">答辩</el-tag>
                  </div>
                  <div v-if="s.materials.length" class="materials">
                    <el-tag
                      v-for="m in s.materials"
                      :key="m"
                      size="small"
                      effect="plain"
                    >{{ m }}</el-tag>
                  </div>
                  <div v-else class="no-mat">无材料清单</div>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as templatesApi from '@/api/templates'

const templates = ref([])
const loading = ref(false)

function hasDefense(t) {
  return (t.stages || []).some((s) => s.need_defense)
}

async function load() {
  loading.value = true
  try {
    templates.value = await templatesApi.listTemplates()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
.actions {
  display: flex;
  gap: 8px;
}
.tpl-col {
  margin-bottom: 16px;
}
.tpl-card {
  height: 100%;
}
.tpl-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tpl-name {
  font-size: 15px;
  font-weight: 600;
}
.tpl-tags {
  display: flex;
  gap: 6px;
}
.stage-line {
  padding: 4px 0 0 4px;
}
.stage-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 6px;
}
.stage-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409eff;
  font-size: 12px;
}
.materials {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.no-mat {
  color: #909399;
  font-size: 12px;
}
</style>
