<template>
  <div class="container">
    <header class="header">
      <h1>📊 行业报告生成器</h1>
      <p class="subtitle">基于 Scrapling + Claude AI 的智能报告生成</p>
    </header>

    <main class="main">
      <!-- 输入区域 -->
      <section class="input-section">
        <div class="form-group">
          <label>报告主题</label>
          <input
            v-model="topic"
            type="text"
            placeholder="例如：新能源汽车2026行业趋势、人工智能技术进展..."
            class="input"
            :disabled="loading"
            @keyup.enter="startGenerate"
          />
        </div>

        <div class="btn-row">
          <button
            @click="startGenerate"
            class="btn-primary"
            :disabled="!topic || loading"
          >
            {{ loading ? '生成中...' : '生成报告' }}
          </button>
          <button
            v-if="loading"
            @click="stopGenerate"
            class="btn-stop"
          >
            停止
          </button>
        </div>
      </section>

      <!-- 进度显示 -->
      <section v-if="loading" class="progress-section">
        <div class="spinner"></div>
        <p class="progress-text">{{ statusMessage }}</p>
      </section>

      <!-- 错误提示 -->
      <section v-if="errorMessage" class="error-section">
        <p class="error-text">{{ errorMessage }}</p>
      </section>

      <!-- 报告展示 -->
      <section v-if="reportContent" class="report-section">
        <div class="report-header">
          <h2>📋 生成的报告</h2>
          <button @click="downloadReport" class="btn-download">
            📥 下载报告
          </button>
        </div>
        <div class="report-content" v-html="formatMarkdown(reportContent)"></div>
      </section>
    </main>

    <footer class="footer">
      <p>基于 <a href="https://github.com/D4Vinci/Scrapling" target="_blank">Scrapling</a> + Claude AI 构建</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

// 状态
const topic = ref('')
const loading = ref(false)
const statusMessage = ref('')
const reportContent = ref('')
const errorMessage = ref('')
const currentTaskId = ref(null)

// 开始生成
async function startGenerate() {
  if (!topic.value) return

  loading.value = true
  statusMessage.value = '正在启动报告生成...'
  reportContent.value = ''
  errorMessage.value = ''
  currentTaskId.value = null

  try {
    // 启动生成任务
    const response = await axios.post('/api/generate', {
      topic: topic.value,
      max_articles: 10
    })

    currentTaskId.value = response.data.task_id
    statusMessage.value = '正在搜索和抓取资讯...'

    // 开始轮询状态
    pollStatus(currentTaskId.value)

  } catch (error) {
    console.error('Error:', error)
    errorMessage.value = '启动失败: ' + (error.response?.data?.detail || error.message)
    loading.value = false
  }
}

// 停止生成
async function stopGenerate() {
  if (!currentTaskId.value) return

  try {
    await axios.post('/api/stop/' + currentTaskId.value)
    loading.value = false
    statusMessage.value = '已停止'
  } catch (error) {
    console.error('Stop error:', error)
    loading.value = false
  }
}

// 轮询状态
async function pollStatus(taskId) {
  try {
    const response = await axios.get('/api/status/' + taskId)
    const data = response.data

    statusMessage.value = data.status_message || '处理中...'

    if (data.status === 'completed') {
      reportContent.value = data.report_content || ''
      if (!reportContent.value) {
        errorMessage.value = '报告内容为空'
      }
      loading.value = false
    } else if (data.status === 'failed') {
      errorMessage.value = data.error || '生成失败'
      loading.value = false
    } else if (data.status === 'stopped') {
      loading.value = false
      statusMessage.value = '已停止'
    } else {
      // 继续轮询
      setTimeout(() => pollStatus(taskId), 2000)
    }
  } catch (error) {
    console.error('Poll error:', error)
    if (loading.value) {
      setTimeout(() => pollStatus(taskId), 3000)
    }
  }
}

// Markdown 格式化
function formatMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
}

// 下载报告
function downloadReport() {
  if (!reportContent.value) return

  const blob = new Blob([reportContent.value], { type: 'text/markdown' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `report_${topic.value}_${Date.now()}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white;
  padding: 2.5rem 2rem;
  text-align: center;
}

.header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  opacity: 0.85;
  font-size: 1rem;
}

.main {
  flex: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

.input-section {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #1a1a2e;
  font-size: 1.1rem;
}

.input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1.1rem;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.input:focus {
  outline: none;
  border-color: #0f3460;
  box-shadow: 0 0 0 4px rgba(15, 52, 96, 0.1);
}

.input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.btn-row {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-primary {
  flex: 1;
  max-width: 300px;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(15, 52, 96, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-stop {
  padding: 1rem 2rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-stop:hover {
  transform: translateY(-2px);
}

.progress-section {
  background: white;
  border-radius: 16px;
  padding: 3rem 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  margin-bottom: 1.5rem;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #0f3460;
  border-radius: 50%;
  margin: 0 auto 1.5rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-text {
  font-size: 1.1rem;
  color: #475569;
}

.error-section {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.error-text {
  color: #dc2626;
  margin: 0;
  font-size: 1rem;
}

.report-section {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.report-header h2 {
  font-size: 1.3rem;
  color: #1a1a2e;
}

.btn-download {
  padding: 0.6rem 1.25rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-download:hover {
  background: #059669;
}

.report-content {
  line-height: 1.8;
  color: #334155;
  font-size: 1rem;
}

.report-content :deep(h2) {
  font-size: 1.4rem;
  color: #1a1a2e;
  margin: 1.5rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #0f3460;
}

.report-content :deep(h3) {
  font-size: 1.2rem;
  color: #334155;
  margin: 1.25rem 0 0.75rem;
}

.report-content :deep(h4) {
  font-size: 1.05rem;
  color: #475569;
  margin: 1rem 0 0.5rem;
}

.report-content :deep(p) {
  margin: 0.75rem 0;
}

.report-content :deep(li) {
  margin: 0.4rem 0;
}

.report-content :deep(strong) {
  color: #1a1a2e;
}

.report-content :deep(a) {
  color: #0f3460;
  text-decoration: underline;
}

.footer {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.9rem;
}

.footer a {
  color: #0f3460;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}
</style>
