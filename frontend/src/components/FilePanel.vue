<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">团队材料文件</div>
      <div class="actions">
        <el-select v-model="teamId" placeholder="选择团队(留空=整包识别)" clearable size="small" style="width:220px" @change="onTeamChange">
          <el-option v-for="t in teams" :key="t.team_id" :label="t.name" :value="t.team_id" />
        </el-select>
        <el-button :icon="Refresh" @click="loadTeams">刷新</el-button>
      </div>
    </div>

    <div
      class="dropzone"
      :class="{ dragging, busy: uploading }"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <el-icon :size="30" class="dz-icon"><UploadFilled /></el-icon>
      <p v-if="teamId" class="dz-main">拖入文件/文件夹 → 上传到「{{ teamName }}」</p>
      <p v-else class="dz-main">拖入<strong>整个文件夹</strong>,按子文件夹名自动识别团队</p>
      <p class="dz-hint">或 <el-button link type="primary" @click="$refs.folderInput.click()">点击选择文件夹</el-button></p>
      <input ref="folderInput" type="file" webkitdirectory directory multiple style="display:none" @change="onFolderPick" />
    </div>

    <el-alert v-if="lastResult" :title="lastResult" type="success" :closable="false" class="result" />
    <el-alert v-if="uploading" title="上传中..." type="info" :closable="false" class="result" />

    <div v-if="teamId" class="file-section">
      <div class="file-head">{{ teamName }} 的文件({{ files.length }})</div>
      <el-table :data="files" v-loading="loadingFiles" size="small" stripe border>
        <el-table-column prop="filename" label="文件名" min-width="180" />
        <el-table-column label="大小" width="90">
          <template #default="{ row }">{{ fmtSize(row.size) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button link type="primary" @click="download(row)">下载</el-button>
            <el-button v-if="!isOfficer" link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { UploadFilled, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as filesApi from '@/api/files'
import * as teamsApi from '@/api/teams'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ pid: { type: String, default: '' } })
const auth = useAuthStore()
const teams = ref([])
const teamId = ref('')
const files = ref([])
const loadingFiles = ref(false)
const dragging = ref(false)
const lastResult = ref('')
const uploading = ref(false)

const isOfficer = computed(() => auth.role === '干事')
const teamName = computed(() => teams.value.find((t) => t.team_id === teamId.value)?.name || '')

async function loadTeams() {
  if (!props.pid) return
  teams.value = await teamsApi.listTeams(props.pid)
}

async function onTeamChange() {
  lastResult.value = ''
  if (teamId.value) await loadFiles()
  else files.value = []
}

async function loadFiles() {
  if (!props.pid || !teamId.value) return
  loadingFiles.value = true
  try {
    files.value = await filesApi.listTeamFiles(props.pid, teamId.value)
  } finally {
    loadingFiles.value = false
  }
}

function fmtSize(b) {
  if (!b) return '0'
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  return (b / 1024 / 1024).toFixed(1) + ' MB'
}

function download(row) {
  window.open(filesApi.fileDownloadUrl(props.pid, teamId.value, row.filename))
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除文件「${row.filename}」?`, '提示', { type: 'warning' })
  await filesApi.deleteFile(props.pid, teamId.value, row.filename)
  ElMessage.success('已删除')
  await loadFiles()
}

// 递归读取拖入的目录 entry,收集 {file, path}
function walkEntry(entry, prefix, out) {
  return new Promise((resolve) => {
    if (entry.isFile) {
      entry.file(
        (f) => {
          out.push({ file: f, path: prefix + f.name })
          resolve()
        },
        () => resolve()
      )
    } else if (entry.isDirectory) {
      const dirName = prefix + entry.name + '/'
      const reader = entry.createReader()
      const readBatch = () => {
        reader.readEntries(async (results) => {
          if (!results.length) {
            resolve()
            return
          }
          for (const r of results) await walkEntry(r, dirName, out)
          readBatch()
        }, () => resolve())
      }
      readBatch()
    } else {
      resolve()
    }
  })
}

async function onDrop(e) {
  dragging.value = false
  if (uploading.value) return
  const items = e.dataTransfer.items
  const collected = []
  if (items && items.length && items[0].webkitGetAsEntry) {
    const entries = []
    for (let i = 0; i < items.length; i++) {
      const en = items[i].webkitGetAsEntry()
      if (en) entries.push(en)
    }
    for (const en of entries) await walkEntry(en, '', collected)
  } else {
    for (const f of e.dataTransfer.files) collected.push({ file: f, path: f.name })
  }
  await processFiles(collected)
}

function onFolderPick(e) {
  const fls = e.target.files
  const collected = []
  for (const f of fls) collected.push({ file: f, path: f.webkitRelativePath || f.name })
  processFiles(collected)
  e.target.value = ''
}

// 路径中哪一段等于某团队名,就归属该团队
function detectTeam(path) {
  const parts = String(path).split('/').filter(Boolean)
  for (const p of parts) {
    const team = teams.value.find((t) => t.name === p)
    if (team) return team
  }
  return null
}

async function processFiles(collected) {
  if (!collected.length) return
  uploading.value = true
  lastResult.value = ''
  try {
    if (teamId.value) {
      // 模式1:上传到选中团队
      const fd = new FormData()
      collected.forEach((c) => fd.append('files', c.file, c.file.name))
      const r = await filesApi.uploadFiles(props.pid, teamId.value, fd)
      lastResult.value = `已上传 ${r.total} 个文件到「${teamName.value}」${r.archived ? `(归档 ${r.archived} 个旧版)` : ''}`
      await loadFiles()
    } else {
      // 模式2:按路径匹配团队
      const groups = {}
      let unmatched = 0
      for (const c of collected) {
        const team = detectTeam(c.path)
        if (team) {
          if (!groups[team.team_id]) groups[team.team_id] = { name: team.name, files: [] }
          groups[team.team_id].files.push(c.file)
        } else {
          unmatched += 1
        }
      }
      let total = 0
      const matchedNames = []
      for (const [tid, g] of Object.entries(groups)) {
        const fd = new FormData()
        g.files.forEach((f) => fd.append('files', f, f.name))
        const r = await filesApi.uploadFiles(props.pid, tid, fd)
        total += r.total
        matchedNames.push(g.name)
      }
      lastResult.value =
        `整包上传完成:共 ${total} 个文件,匹配团队 ${matchedNames.length} 个(${matchedNames.join('、')})` +
        (unmatched ? `;未匹配 ${unmatched} 个文件(团队名对不上)` : '')
    }
  } catch (e) {
    // 已提示
  } finally {
    uploading.value = false
  }
}

watch(() => props.pid, () => {
  loadTeams()
  files.value = []
  teamId.value = ''
})
onMounted(loadTeams)
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
}
.actions {
  display: flex;
  gap: 8px;
}
.dropzone {
  border: 2px dashed #c0c4cc;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  transition: all 0.2s;
  background: #fafafa;
}
.dropzone.dragging {
  border-color: #409eff;
  background: #ecf5ff;
}
.dropzone.busy {
  opacity: 0.6;
}
.dz-icon {
  color: #909399;
}
.dz-main {
  margin: 8px 0 4px;
  font-size: 14px;
}
.dz-hint {
  color: #909399;
  font-size: 12px;
  margin: 0;
}
.result {
  margin: 10px 0;
}
.file-section {
  margin-top: 12px;
}
.file-head {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}
</style>
