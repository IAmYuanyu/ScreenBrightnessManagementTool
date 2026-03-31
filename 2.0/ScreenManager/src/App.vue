<script setup>
import { ref, reactive, onMounted } from "vue";

const activeTab = ref("mask");
const monitors = ref([]);
const selectedMonitors = ref(new Set());
const error = ref("");
const success = ref("");
const loading = ref(false);

const maskSettings = reactive({
  alpha: 50,
  color: "#000000"
});

const API_URL = "http://127.0.0.1:5000/api";

onMounted(async () => {
  await fetchMonitors();
});

const fetchMonitors = async () => {
  try {
    const res = await fetch(`${API_URL}/monitors`);
    monitors.value = await res.json();
  } catch (e) {
    error.value = "获取显示器失败: " + e;
  }
};

const toggleMonitor = (id) => {
  if (selectedMonitors.value.has(id)) {
    selectedMonitors.value.delete(id);
  } else {
    selectedMonitors.value.add(id);
  }
};

const createMask = async () => {
  if (selectedMonitors.value.size === 0) {
    error.value = "请至少选择一个显示器";
    return;
  }

  loading.value = true;
  error.value = "";
  try {
    const res = await fetch(`${API_URL}/mask/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ monitor_ids: Array.from(selectedMonitors.value) })
    });
    const data = await res.json();
    if (data.success) {
      success.value = `已为 ${data.count} 个显示器生成遮罩`;
      setTimeout(() => (success.value = ""), 2000);
    } else {
      error.value = data.error;
    }
  } catch (e) {
    error.value = "生成遮罩失败: " + e;
  } finally {
    loading.value = false;
  }
};

const closeMask = async () => {
  loading.value = true;
  error.value = "";
  try {
    const res = await fetch(`${API_URL}/mask/close`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      success.value = "遮罩已关闭";
      setTimeout(() => (success.value = ""), 2000);
    } else {
      error.value = data.error;
    }
  } catch (e) {
    error.value = "关闭遮罩失败: " + e;
  } finally {
    loading.value = false;
  }
};

const updateMask = async () => {
  try {
    const res = await fetch(`${API_URL}/mask/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        alpha: parseInt(maskSettings.alpha),
        color: maskSettings.color
      })
    });
    const data = await res.json();
    if (!data.success) {
      error.value = data.error;
    }
  } catch (e) {
    error.value = "更新遮罩失败: " + e;
  }
};
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>屏幕遮罩工具</h1>
      <p class="subtitle">简洁高效的屏幕亮度管理工具</p>
    </header>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="success" class="success">{{ success }}</div>

    <main class="content">
      <div class="settings-card">
        <h3>遮罩设置</h3>

        <div class="setting-item">
          <label>颜色</label>
          <div class="color-input">
            <input type="color" v-model="maskSettings.color" @change="updateMask" />
            <span>{{ maskSettings.color }}</span>
          </div>
        </div>

        <div class="setting-item">
          <label>不透明度</label>
          <div class="alpha-control">
            <input
              type="range"
              min="0"
              max="100"
              v-model="maskSettings.alpha"
              @input="updateMask"
              :disabled="loading"
            />
            <span>{{ maskSettings.alpha }}%</span>
          </div>
        </div>
      </div>

      <div class="settings-card">
        <h3>选择显示器</h3>
        <div class="monitor-list">
          <label v-for="monitor in monitors" :key="monitor.id" class="monitor-item">
            <input
              type="checkbox"
              :checked="selectedMonitors.has(monitor.id)"
              @change="toggleMonitor(monitor.id)"
            />
            <span>{{ monitor.name }} ({{ monitor.width }}×{{ monitor.height }})</span>
          </label>
        </div>
      </div>

      <div class="button-group">
        <button class="btn-primary" @click="createMask" :disabled="loading">
          生成遮罩
        </button>
        <button class="btn-secondary" @click="closeMask" :disabled="loading">
          关闭遮罩
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
  color: #2c3e50;
}

.header h1 {
  font-size: 32px;
  margin: 0;
  font-weight: 600;
}

.subtitle {
  margin: 8px 0 0 0;
  color: #7f8c8d;
  font-size: 14px;
}

.content {
  max-width: 600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error {
  background: #fee;
  color: #c33;
  padding: 12px 16px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 16px;
}

.success {
  background: #efe;
  color: #3c3;
  padding: 12px 16px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 16px;
}

.settings-card {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.settings-card h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-item label {
  min-width: 80px;
  color: #2c3e50;
  font-weight: 500;
  font-size: 14px;
}

.color-input {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.color-input input {
  width: 50px;
  height: 40px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.color-input span {
  color: #7f8c8d;
  font-size: 14px;
  font-family: monospace;
}

.alpha-control {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.alpha-control input {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(90deg, #e0e0e0 0%, #667eea 100%);
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.alpha-control input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.alpha-control input::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.alpha-control span {
  min-width: 40px;
  text-align: right;
  color: #667eea;
  font-weight: 600;
  font-size: 14px;
}

.monitor-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.monitor-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.3s;
}

.monitor-item:hover {
  background: #f5f7fa;
}

.monitor-item input {
  cursor: pointer;
}

.button-group {
  display: flex;
  gap: 12px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #ecf0f1;
  color: #7f8c8d;
}

.btn-secondary:hover:not(:disabled) {
  background: #bdc3c7;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
