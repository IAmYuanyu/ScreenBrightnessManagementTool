<script setup>
import { ref, reactive, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const settings = reactive({
  brightnessPresets: [30, 50, 75, 100],
  method: "mask",
  autoStart: false
});

const newPreset = ref("");
const error = ref("");
const success = ref("");
const loading = ref(false);

onMounted(async () => {
  try {
    const loaded = await invoke("load_settings");
    Object.assign(settings, {
      brightnessPresets: loaded.brightness_presets,
      method: loaded.method,
      autoStart: loaded.auto_start
    });
  } catch (e) {
    console.error("加载设置失败:", e);
  }
});

const addPreset = () => {
  const val = parseInt(newPreset.value);
  if (val >= 0 && val <= 100 && !settings.brightnessPresets.includes(val)) {
    settings.brightnessPresets.push(val);
    settings.brightnessPresets.sort((a, b) => a - b);
    newPreset.value = "";
    success.value = "预设已添加";
    setTimeout(() => (success.value = ""), 2000);
  } else {
    error.value = "无效的预设值或已存在";
    setTimeout(() => (error.value = ""), 2000);
  }
};

const removePreset = (idx) => {
  settings.brightnessPresets.splice(idx, 1);
};

const saveSettings = async () => {
  loading.value = true;
  error.value = "";
  try {
    await invoke("save_settings", {
      settings: {
        brightness_presets: settings.brightnessPresets,
        method: settings.method,
        auto_start: settings.autoStart
      }
    });
    success.value = "设置已保存";
    setTimeout(() => (success.value = ""), 2000);
  } catch (e) {
    error.value = "保存设置失败: " + e;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="settings">
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="success" class="success">{{ success }}</div>

    <div class="settings-card">
      <h3>亮度预设</h3>
      <div class="presets">
        <div v-for="(preset, idx) in settings.brightnessPresets" :key="idx" class="preset-item">
          <span>{{ preset }}%</span>
          <button @click="removePreset(idx)" class="btn-remove">×</button>
        </div>
      </div>
      <div class="preset-input">
        <input
          v-model="newPreset"
          type="number"
          min="0"
          max="100"
          placeholder="输入0-100"
          @keyup.enter="addPreset"
        />
        <button @click="addPreset" class="btn-add">添加</button>
      </div>
    </div>

    <div class="settings-card">
      <h3>调节方式</h3>
      <div class="radio-group">
        <label>
          <input type="radio" v-model="settings.method" value="mask" />
          遮罩调节
        </label>
        <label>
          <input type="radio" v-model="settings.method" value="ddc" />
          DDC/CI
        </label>
        <label>
          <input type="radio" v-model="settings.method" value="wmi" />
          WMI
        </label>
      </div>
    </div>

    <div class="settings-card">
      <h3>其他选项</h3>
      <label class="checkbox">
        <input type="checkbox" v-model="settings.autoStart" />
        开机自启
      </label>
    </div>

    <button @click="saveSettings" class="btn-save" :disabled="loading">
      {{ loading ? "保存中..." : "保存设置" }}
    </button>
  </div>
</template>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 12px;
  font-size: 14px;
}

.success {
  background: #efe;
  color: #3c3;
  padding: 12px;
  border-radius: 12px;
  font-size: 14px;
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

.presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.preset-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
}

.btn-remove {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  line-height: 1;
}

.btn-remove:hover {
  opacity: 0.8;
}

.preset-input {
  display: flex;
  gap: 8px;
}

.preset-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ecf0f1;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.preset-input input:focus {
  border-color: #667eea;
}

.btn-add {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #667eea;
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-add:hover {
  background: #764ba2;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #2c3e50;
  font-size: 14px;
}

.radio-group input {
  cursor: pointer;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #2c3e50;
  font-size: 14px;
}

.checkbox input {
  cursor: pointer;
}

.btn-save {
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

