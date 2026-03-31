<script setup>
import { ref, reactive, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const props = defineProps({
  monitors: Array
});

const maskState = reactive({});
const maskColor = ref("#000000");
const maskAlpha = ref(50);
const loading = ref(false);
const error = ref("");

onMounted(() => {
  props.monitors?.forEach(m => {
    maskState[m.id] = false;
  });
});

const toggleMask = async (monitorId) => {
  loading.value = true;
  error.value = "";
  try {
    if (maskState[monitorId]) {
      await invoke("close_mask", { monitor_id: monitorId });
      maskState[monitorId] = false;
    } else {
      await invoke("create_mask", {
        monitor_id: monitorId,
        color: maskColor.value,
        alpha: parseInt(maskAlpha.value)
      });
      maskState[monitorId] = true;
    }
  } catch (e) {
    error.value = "操作遮罩失败: " + e;
  } finally {
    loading.value = false;
  }
};

const updateAllMasks = async () => {
  loading.value = true;
  error.value = "";
  try {
    await invoke("update_all_masks", {
      color: maskColor.value,
      alpha: parseInt(maskAlpha.value)
    });
  } catch (e) {
    error.value = "更新遮罩失败: " + e;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="mask-control">
    <div v-if="error" class="error">{{ error }}</div>

    <div class="mask-settings">
      <div class="setting-item">
        <label>遮罩颜色</label>
        <div class="color-input">
          <input type="color" v-model="maskColor" @change="updateAllMasks" />
          <span class="color-value">{{ maskColor }}</span>
        </div>
      </div>

      <div class="setting-item">
        <label>不透明度</label>
        <div class="alpha-control">
          <input
            type="range"
            min="0"
            max="100"
            v-model="maskAlpha"
            @input="updateAllMasks"
            :disabled="loading"
          />
          <span class="alpha-value">{{ maskAlpha }}%</span>
        </div>
      </div>
    </div>

    <div class="monitors-grid">
      <div v-for="monitor in monitors" :key="monitor.id" class="monitor-card">
        <div class="monitor-info">
          <h4>{{ monitor.name }}</h4>
          <p>{{ monitor.width }}×{{ monitor.height }}</p>
        </div>
        <button
          :class="['btn-toggle', { active: maskState[monitor.id] }]"
          @click="toggleMask(monitor.id)"
          :disabled="loading"
        >
          {{ maskState[monitor.id] ? "关闭遮罩" : "启用遮罩" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask-control {
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

.mask-settings {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 12px;
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

.color-value {
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
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.4);
}

.alpha-control input::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.4);
}

.alpha-value {
  min-width: 40px;
  text-align: right;
  color: #667eea;
  font-weight: 600;
  font-size: 14px;
}

.monitors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.monitor-card {
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.monitor-info h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 14px;
}

.monitor-info p {
  margin: 4px 0 0 0;
  color: #95a5a6;
  font-size: 12px;
}

.btn-toggle {
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: #ecf0f1;
  color: #7f8c8d;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-toggle:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

.btn-toggle.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

