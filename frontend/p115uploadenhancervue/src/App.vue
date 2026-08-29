<template>
  <v-app>
    <div class="plugin-app">
      <component :is="currentComponent" :api="api" :initial-config="config" @switch="switchComponent" @config="showConfig" @save="saveConfig" />
    </div>
  </v-app>
</template>

<script setup>
import { onMounted, onBeforeUnmount, onErrorCaptured, reactive, ref, shallowRef } from 'vue'
import Page from './components/Page.vue'
import Config from './components/Config.vue'

const api = ref(null)
const currentComponent = shallowRef(Page)
const config = reactive({ enabled: false, cookie: '' })
const switchComponent = () => {
  currentComponent.value = currentComponent.value === Page ? Config : Page
}
const showConfig = () => {
  currentComponent.value = Config
}

const handleMessage = (event) => {
  if (event.data?.type === 'api') api.value = event.data.data
  if (event.data?.type === 'config' && event.data.data) Object.assign(config, event.data.data)
  if (event.data?.type === 'showConfig') currentComponent.value = Config
}
const saveConfig = (data) => {
  Object.assign(config, data)
  window.parent?.postMessage({ type: 'save', data }, '*')
  currentComponent.value = Page
}
onMounted(() => {
  window.addEventListener('message', handleMessage)
  window.parent?.postMessage({ type: 'ready' }, '*')
})
onBeforeUnmount(() => window.removeEventListener('message', handleMessage))
onErrorCaptured((error, instance, info) => {
  console.error('[P115UploadEnhancerVUE] 组件运行时异常', { error, instance, info })
  return true
})
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
.plugin-app { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.v-window, .v-window-item { min-height: 0; height: 100%; }
.page-scroll { height: 100%; overflow-y: auto; padding: 16px; }
</style>
