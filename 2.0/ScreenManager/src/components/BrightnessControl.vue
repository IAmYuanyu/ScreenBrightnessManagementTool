<script setup>
import { ref, reactive, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const props = defineProps({
  monitors: Array
});

const selectedMonitors = ref(new Set());
const brightness = reactive({});
const loading = ref(false);
const error = ref("");

onMounted(async () => {
  try {
    props.monitors?.forEach(m => {
      brightness[m.id] = 50;
    });
  } catch (e) {
    error.value = "初始化失败";
  }
});

const toggleMonitor = (monitorId) => {
  if (selectedMonitors.value.has(monitorId)) {
    selectedMonitors.value.delete(monitorId);
  } else {
    selectedMonitors.value.add(monitorId);
  }
};

const setBrightness = async (monitorId, value) => {
  loading.value = true;
  error.value = "";
  try {
    await invoke("set_brightness", { monitor_id: monitorId, brightness: parseInt(value) });
    brightness[monitorId] = value;
  } catch (e) {
    error.value = "设置亮度失败: " + e;
  } finally {
    loading.value = false;
  }
};

const applyToSelected = async () => {
  if (selectedMonitors.value.size === 0) {
    error.value = "请先选择显示器";
    return;
  }

  loading.value = true;
  error.value = "";
  try {
    await invoke("set_selected_monitors", { monitor_ids: Array.from(selectedMonitors.value) });
    for (const id of selectedMonitors.value) {
      await invoke("set_brightness", { monitor_id: id, brightness: parseInt(brightness[id]) });
    }
  } catch (e) {
    error.value = "应用失败: " + e;
  } finally {
    loading.value = false;
  }
};

const turnOffDisplay = async () => {
  loading.value = true;
  error.value = "";
  try {
    await invoke("turn_off_display");
  } catch (e) {
    error.value = "关闭显示器失败: " + e;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="brightness-control">
    <div v-if="error" class="error">{{ error }}</div>

    <div class="monitor-selection">
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

    <div class="brightness-settings">
      <h3>亮度调节</h3>
      <div v-for="monitor in monitors" :key="monitor.id" class="monitor-card">
        <div class="monitor-header">
          <h4>{{ monitor.name }}</h4>
          <span class="monitor-res">{{ monitor.width }}×{{ monitor.height }}</span>
        </div>

        <div class="brightness-slider">
          <label>亮度</label>
          <input
            type="range"
            min="0"
            max="100"
            :value="brightness[monitor.id] || 50"
            @input="setBrightness(monitor.id, $event.target.value)"
            :disabled="loading"
          />
          <span class="value">{{ brightness[monitor.id] || 50 }}%</span>
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="btn-apply" @click="applyToSelected" :disabled="loading">
        应用到选中显示器
      </button>
      <button class="btn-off" @click="turnOffDisplay" :disabled="loading">
        关闭显示器
      </button>
    </div>
  </div>
</template>

<style scoped>
.brightness-control {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 12px;
  font-size: 14px;
}

.monitor-selection {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.monitor-selection h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
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

.brightness-settings {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.brightness-settings h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 16px;
}

.monitor-card {
  padding: 16px;
  border: 1px solid #ecf0f1;
  border-radius: 12px;
  margin-bottom: 12px;
}

.monitor-card:last-child {
  margin-bottom: 0;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.monitor-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 14px;
}

.monitor-res {
  color: #95a5a6;
  font-size: 12px;
}

.brightness-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brightness-slider label {
  min-width: 50px;
  color: #7f8c8d;
  font-size: 14px;
}

.brightness-slider input {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(90deg, #e0e0e0 0%, #667eea 100%);
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.brightness-slider input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.brightness-slider input::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.value {
  min-width: 40px;
  text-align: right;
  color: #667eea;
  font-weight: 600;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
}

.btn-apply,
.btn-off {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-apply {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-apply:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-off {
  background: #ecf0f1;
  color: #7f8c8d;
}

.btn-off:hover:not(:disabled) {
  background: #e74c3c;
  color: white;
}

.btn-apply:disabled,
.btn-off:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

