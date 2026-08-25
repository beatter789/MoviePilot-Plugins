<template>
  <v-app>
    <div class="plugin-app">
      <v-tabs v-model="tab" color="primary" density="compact">
        <v-tab value="page">账户信息</v-tab>
        <v-tab value="config">配置</v-tab>
      </v-tabs>
      <v-window v-model="tab" class="flex-grow-1">
        <v-window-item value="page"><Page :api="api" :config="config" /></v-window-item>
        <v-window-item value="config"><Config :api="api" :config="config" @save="saveConfig" /></v-window-item>
      </v-window>
    </div>
  </v-app>
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref } from 'vue'
import Page from './components/Page.vue'
import Config from './components/Config.vue'

const api = ref(null)
const tab = ref('page')
const config = reactive({ enabled: false, cookie: '' })

const handleMessage = (event) => {
  if (event.data?.type === 'api') api.value = event.data.data
  if (event.data?.type === 'config' && event.data.data) Object.assign(config, event.data.data)
  if (event.data?.type === 'showConfig') tab.value = 'config'
}
const saveConfig = (data) => {
  Object.assign(config, data)
  window.parent?.postMessage({ type: 'save', data }, '*')
  tab.value = 'page'
}
onMounted(() => {
  window.addEventListener('message', handleMessage)
  window.parent?.postMessage({ type: 'ready' }, '*')
})
onBeforeUnmount(() => window.removeEventListener('message', handleMessage))
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
.plugin-app { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.v-window, .v-window-item { min-height: 0; height: 100%; }
.page-scroll { height: 100%; overflow-y: auto; padding: 16px; }
</style>
