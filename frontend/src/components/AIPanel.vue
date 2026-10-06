<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">AI 辅助</div>
      <span class="hint">材料完整性检查 · 汇报书草稿 · 内容摘要</span>
    </div>

    <el-tabs v-model="active">
      <!-- 材料完整性检查 -->
      <el-tab-pane label="材料完整性检查" name="check">
        <div class="form-row">
          <el-select v-model="checkForm.stage_id" clearable placeholder="阶段(空=全部)" style="width:180px">
            <el-option v-for="s in stages" :key="s.stage_id" :label="s.name" :value="s.stage_id" />
          </el-select>
          <el-select v-model="checkForm.team_id" clearable filterable placeholder="团队(空=全部)" style="width:180px">
            <el-option v-for="t in teams" :key="t.team_id" :label="t.name" :value="t.team_id" />
          </el-select>
          <el-button type="primary" :loading="checkLoading" @click="runCheck">开始检查</el-button>
        </div>
        <div v-loading="checkLoading" class="result">
          <template v-if="checkResult">
            <template v-if="checkResult.result && typeof checkResult.result === 'object'">
              <div v-if="checkResult.result.overall" class="overall">{{ checkResult.result.overall }}</div>
              <div v-for="(t, i) in (checkResult.result.teams || [])" :key="i" class="team-block">
                <div class="team-name">{{ t.team_name || t.team_id }}</div>
                <div v-if="t.missing && t.missing.length" class="line missing">
                  <span class="lbl">缺失:</span>{{ t.missing.join('、') }}
                </div>
                <div v-if="t.irregular && t.irregular.length" class="line irregular">
                  <span class="lbl">不规范:</span>{{ t.irregular.join('、') }}
                </div>
                <div v-if="t.suggestions" class="line">{{ t.suggestions }}</div>
              </div>
            </template>
            <pre v-else>{{ checkResult.raw }}</pre>
          </template>
          <el-empty v-else-if="!checkLoading" description="选择范围后点击「开始检查」" :image-size="50" />
        </div>
      </el-tab-pane>

      <!-- 汇报书草稿生成 -->
      <el-tab-pane label="汇报书草稿生成" name="draft">
        <div class="form-row">
          <el-select v-model="draftForm.stage_id" clearable placeholder="阶段" style="width:180px">
            <el-option v-for="s in stages" :key="s.stage_id" :label="s.name" :value="s.stage_id" />
          </el-select>
          <el-select v-model="draftForm.team_id" clearable filterable placeholder="团队(可选)" style="width:180px">
            <el-option v-for="t in teams" :key="t.team_id" :label="t.name" :value="t.team_id" />
          </el-select>
          <el-select v-model="draftForm.type" clearable placeholder="类型(自动推断)" style="width:160px">
            <el-option label="申报" value="申报" />
            <el-option label="中期" value="中期" />
            <el-option label="结题" value="结题" />
          </el-select>
          <el-button type="primary" :loading="draftLoading" @click="runDraft">生成草稿</el-button>
        </div>
        <div v-loading="draftLoading" class="result">
          <pre v-if="draftResult" class="draft-pre">{{ draftResult.draft }}</pre>
          <el-empty v-else-if="!draftLoading" description="选择阶段后点击「生成草稿」" :image-size="50" />
        </div>
      </el-tab-pane>

      <!-- 材料内容摘要 -->
      <el-tab-pane label="材料内容摘要" name="summarize">
        <div class="form-row">
          <el-select v-model="sumForm.task_id" filterable placeholder="选择任务" style="width:340px">
            <el-option-group v-for="s in stages" :key="s.stage_id" :label="s.name">
              <el-option
                v-for="t in tasksByStage(s.stage_id)"
                :key="t.task_id"
                :label="`${t.team_name} - ${t.material}${t.file_name ? ' (' + t.file_name + ')' : ' (未交)'}`"
                :value="t.task_id"
              />
            </el-option-group>
          </el-select>
          <el-button type="primary" :loading="sumLoading" :disabled="!sumForm.task_id" @click="runSummarize">生成摘要</el-button>
        </div>
        <div v-loading="sumLoading" class="result">
          <template v-if="sumResult">
            <el-alert v-if="sumResult.note" :title="sumResult.note" type="info" :closable="false" show-icon class="note-alert" />
            <pre>{{ sumResult.summary }}</pre>
          </template>
          <el-empty v-else-if="!sumLoading" description="选择已上传材料的任务后点击「生成摘要」" :image-size="50" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import * as aiApi from '@/api/ai'
import * as teamsApi from '@/api/teams'
import * as tasksApi from '@/api/tasks'

const props = defineProps({
  pid: { type: String, default: '' },
  stages: { type: Array, default: () => [] },
})

const active = ref('check')
const teams = ref([])
const tasks = ref([])

const checkForm = reactive({ stage_id: '', team_id: '' })
const draftForm = reactive({ stage_id: '', team_id: '', type: '' })
const sumForm = reactive({ task_id: '' })

const checkLoading = ref(false)
const draftLoading = ref(false)
const sumLoading = ref(false)

const checkResult = ref(null)
const draftResult = ref(null)
const sumResult = ref(null)

function tasksByStage(sid) {
  return tasks.value.filter((t) => t.stage_id === sid)
}

async function loadMeta() {
  if (!props.pid) return
  try {
    const [ts, tks] = await Promise.all([teamsApi.listTeams(props.pid), tasksApi.listTasks(props.pid)])
    teams.value = ts
    tasks.value = tks
  } catch (e) {
    // 错误已由 axios 拦截器提示
  }
}

async function runCheck() {
  checkLoading.value = true
  checkResult.value = null
  try {
    checkResult.value = await aiApi.checkCompleteness(props.pid, {
      stage_id: checkForm.stage_id,
      team_id: checkForm.team_id,
    })
  } catch (e) {
    // 已提示
  } finally {
    checkLoading.value = false
  }
}

async function runDraft() {
  draftLoading.value = true
  draftResult.value = null
  try {
    draftResult.value = await aiApi.generateDraft(props.pid, {
      stage_id: draftForm.stage_id,
      team_id: draftForm.team_id,
      type: draftForm.type,
    })
  } catch (e) {
    // 已提示
  } finally {
    draftLoading.value = false
  }
}

async function runSummarize() {
  sumLoading.value = true
  sumResult.value = null
  try {
    sumResult.value = await aiApi.summarizeMaterial(props.pid, { task_id: sumForm.task_id })
  } catch (e) {
    // 已提示
  } finally {
    sumLoading.value = false
  }
}

watch(() => props.pid, () => loadMeta())
onMounted(() => loadMeta())
</script>

<style scoped>
.panel {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.hint {
  font-size: 12px;
  color: #c7ccd6;
}
.form-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.result {
  min-height: 60px;
}
.result pre {
  background: #f6f8fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  max-height: 420px;
  overflow: auto;
}
.draft-pre {
  max-height: 520px;
}
.team-block {
  padding: 10px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 8px;
}
.team-name {
  font-weight: 600;
  margin-bottom: 6px;
  color: #0c0d0e;
}
.line {
  font-size: 13px;
  line-height: 1.6;
  color: #4b5563;
  margin: 2px 0;
}
.line .lbl {
  font-weight: 600;
  margin-right: 4px;
}
.line.missing {
  color: #f56c6c;
}
.line.irregular {
  color: #e6a23c;
}
.overall {
  padding: 8px 10px;
  background: #ecf5ff;
  border-radius: 4px;
  font-size: 13px;
  margin-bottom: 10px;
  color: #1664ff;
}
.note-alert {
  margin-bottom: 8px;
}
</style>
