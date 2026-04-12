<template>
  <div class="container">
    <header class="header">
      <h1>📊 智能报告生成器</h1>
      <p class="subtitle">基于 Scrapling + Claude AI 的专业报告生成</p>
    </header>

    <main class="main">
      <!-- 输入区域 -->
      <section class="input-section">
        <div class="form-group">
          <label>报告主题</label>
          <input
            v-model="topic"
            type="text"
            placeholder="例如：新能源汽车、储能行业、半导体产业..."
            class="input"
            :disabled="loading"
            @keyup.enter="startGenerate"
          />
        </div>

        <div class="form-group">
          <label>报告类型</label>
          <div class="report-types">
            <label
              v-for="(name, key) in reportTypes"
              :key="key"
              class="type-option"
              :class="{ active: reportType === key, disabled: loading }"
            >
              <input
                type="radio"
                :value="key"
                v-model="reportType"
                :disabled="loading"
              />
              <span class="type-name">{{ name }}</span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>报告深度</label>
          <div class="depth-options">
            <label
              class="type-option"
              :class="{ active: reportDepth === 'simple', disabled: loading }"
            >
              <input
                type="radio"
                value="simple"
                v-model="reportDepth"
                :disabled="loading"
              />
              <span class="type-name">简要报告</span>
              <span class="type-desc">3-4章节，3-5分钟</span>
            </label>
            <label
              class="type-option"
              :class="{ active: reportDepth === 'depth', disabled: loading }"
            >
              <input
                type="radio"
                value="depth"
                v-model="reportDepth"
                :disabled="loading"
              />
              <span class="type-name">深度报告</span>
              <span class="type-desc">6-9章节，8-15分钟</span>
            </label>
          </div>
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
        <div class="progress-info">
          <div class="spinner"></div>
          <p class="progress-text">{{ statusMessage }}</p>
          <div class="time-info">
            <span class="time-badge">
              <span class="time-label">已用时</span>
              <span class="time-value">{{ formatTime(elapsedSeconds) }}</span>
            </span>
            <span v-if="remainingSeconds > 0" class="time-badge estimate">
              <span class="time-label">预计剩余</span>
              <span class="time-value">{{ formatTime(remainingSeconds) }}</span>
            </span>
          </div>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <span class="progress-percent">{{ progressPercent }}%</span>
        </div>
      </section>

      <!-- 错误提示 -->
      <section v-if="errorMessage" class="error-section">
        <p class="error-text">{{ errorMessage }}</p>
      </section>

      <!-- 报告展示 -->
      <section v-if="reportContent" class="report-section">
        <div class="report-header">
          <div class="report-title">
            <h2>📋 生成的报告</h2>
            <span v-if="generationTime" class="gen-time-badge">
              ⏱️ 生成耗时: {{ formatTime(generationTime) }}
            </span>
          </div>
          <button @click="downloadReport" class="btn-download">
            📥 下载报告
          </button>
        </div>
        <div class="report-content markdown-body" v-html="renderedContent"></div>
      </section>
    </main>

    <footer class="footer">
      <p>基于 <a href="https://github.com/D4Vinci/Scrapling" target="_blank">Scrapling</a> + Claude AI 构建</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

// 报告类型
const reportTypes = {
  trend: '趋势分析报告',
  compare: '对比分析报告',
  comprehensive: '综合评估报告',
  policy: '政策解读报告'
}

// 状态
const topic = ref('')
const reportType = ref('trend')
const reportDepth = ref('simple')
const loading = ref(false)
const statusMessage = ref('')
const reportContent = ref('')
const errorMessage = ref('')
const progressPercent = ref(0)
const elapsedSeconds = ref(0)
const remainingSeconds = ref(0)
const generationTime = ref(0)
const currentTaskId = ref(null)

// 定时器
let elapsedTimer = null

// 计算属性：渲染后的 Markdown
const renderedContent = computed(() => {
  if (!reportContent.value) return ''
  return marked(reportContent.value)
})

// 格式化时间
function formatTime(seconds) {
  if (seconds < 60) {
    return `${seconds}秒`
  }
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}分${secs}秒`
}

// 开始生成
async function startGenerate() {
  if (!topic.value) return

  loading.value = true
  statusMessage.value = '准备生成...'
  reportContent.value = ''
  errorMessage.value = ''
  progressPercent.value = 0
  elapsedSeconds.value = 0
  remainingSeconds.value = 0
  generationTime.value = 0
  currentTaskId.value = null

  // 开始计时
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        topic: topic.value,
        report_type: reportType.value,
        report_depth: reportDepth.value,
        max_articles: 10
      })
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    // 使用 text() 流式读取 + 实时解析 SSE
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const readStream = async () => {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 处理每一行完整的 SSE 消息
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留不完整的行在 buffer 中

        for (const line of lines) {
          if (line.startsWith('event: ')) continue

          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const event = JSON.parse(data)
              if (event.status) {
                reportContent.value = event.content || ''
                if (event.elapsed) {
                  generationTime.value = event.elapsed
                  remainingSeconds.value = 0
                }
                loading.value = false
                clearInterval(elapsedTimer)
              }
            } catch {
              if (data && !data.startsWith('{')) {
                statusMessage.value = data
              }
            }
          }
        }
      }

      // 处理 buffer 中剩余的数据
      if (buffer.startsWith('data: ')) {
        const data = buffer.slice(6)
        try {
          const event = JSON.parse(data)
          if (event.status) {
            reportContent.value = event.content || ''
            if (event.elapsed) {
              generationTime.value = event.elapsed
              remainingSeconds.value = 0
            }
            loading.value = false
            clearInterval(elapsedTimer)
          }
        } catch {
          if (data && !data.startsWith('{')) {
            statusMessage.value = data
          }
        }
      }

      loading.value = false
      clearInterval(elapsedTimer)
    }

    await readStream()

  } catch (error) {
    console.error('Error:', error)
    errorMessage.value = '启动失败: ' + (error.message || '未知错误')
    loading.value = false
    clearInterval(elapsedTimer)
  }
}

// 停止生成
async function stopGenerate() {
  if (!currentTaskId.value) return

  try {
    await fetch('/api/stop/' + currentTaskId.value, { method: 'POST' })
    loading.value = false
    statusMessage.value = '已停止'
    clearInterval(elapsedTimer)
  } catch (error) {
    console.error('Stop error:', error)
    loading.value = false
    clearInterval(elapsedTimer)
  }
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

<style>
@import 'highlight.js/styles/github.css';

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
  max-width: 1000px;
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

.report-types {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.depth-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.type-option {
  display: flex;
  align-items: center;
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-option:hover:not(.disabled) {
  border-color: #c7d2fe;
  background: #f8faff;
}

.type-option.active {
  border-color: #0f3460;
  background: #f0f4ff;
}

.type-option.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.type-option input {
  display: none;
}

.type-name {
  font-size: 0.95rem;
  color: #334155;
}

.type-desc {
  font-size: 0.8rem;
  color: #64748b;
  margin-left: auto;
}

.type-option.active .type-name {
  color: #0f3460;
  font-weight: 500;
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
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  margin-bottom: 1.5rem;
}

.progress-info {
  text-align: center;
  margin-bottom: 1.5rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #0f3460;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-text {
  font-size: 1.1rem;
  color: #475569;
  margin-bottom: 1rem;
}

.time-info {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.time-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f0f4ff;
  border-radius: 20px;
  font-size: 0.9rem;
}

.time-badge.estimate {
  background: #fef3c7;
}

.time-label {
  color: #64748b;
}

.time-value {
  font-weight: 600;
  color: #1a1a2e;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-bar {
  flex: 1;
  height: 10px;
  background: #e2e8f0;
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0f3460, #1a1a2e);
  transition: width 0.3s ease;
  border-radius: 5px;
}

.progress-percent {
  font-size: 0.9rem;
  font-weight: 600;
  color: #0f3460;
  min-width: 40px;
  text-align: right;
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

.report-title {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.report-header h2 {
  font-size: 1.3rem;
  color: #1a1a2e;
  margin: 0;
}

.gen-time-badge {
  font-size: 0.85rem;
  color: #059669;
  background: #d1fae5;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-weight: 500;
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

/* Markdown 样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 15px;
  line-height: 1.8;
  color: #24292e;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: #1a1a2e;
}

.markdown-body h1 {
  font-size: 2em;
  padding-bottom: 0.3em;
  border-bottom: 2px solid #0f3460;
}

.markdown-body h2 {
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #e1e4e8;
}

.markdown-body h3 {
  font-size: 1.25em;
}

.markdown-body h4 {
  font-size: 1em;
}

.markdown-body p {
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body li {
  margin-top: 0.25em;
}

.markdown-body li + li {
  margin-top: 0.25em;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 6px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.markdown-body pre code {
  padding: 0;
  margin: 0;
  background-color: transparent;
  border: 0;
  font-size: 100%;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}

.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
  overflow: auto;
}

.markdown-body table th,
.markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body img {
  max-width: 100%;
  box-sizing: border-box;
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
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
