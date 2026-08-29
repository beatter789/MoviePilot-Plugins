<template>
  <div class="page-scroll">
    <v-card variant="outlined">
      <v-card-title class="d-flex align-center"><v-icon icon="mdi-account-box" class="mr-2" />115账户信息</v-card-title>
      <v-card-text>
        <div v-if="show_switch" class="d-flex justify-end mb-3">
          <v-btn variant="outlined" prepend-icon="mdi-cog" @click="openConfig">打开配置</v-btn>
        </div>
        <v-alert v-if="loading" type="info" variant="tonal" density="compact">正在检查账户状态...</v-alert>
        <v-alert v-else-if="!status.success" type="warning" variant="tonal">{{ status.error_message || '请在配置页面中设置有效的115网盘Cookie' }}</v-alert>
        <template v-else>
          <v-list lines="one" density="compact">
            <v-list-item title="Cookie" :subtitle="status.cookie_valid ? '有效' : '无效'" />
            <v-divider />
            <v-list-item title="用户名" :subtitle="status.user_info?.name || '未知'" />
            <v-divider />
            <v-list-item title="VIP" :subtitle="vipText" />
            <v-divider />
            <v-list-item title="VIP到期" :subtitle="status.user_info?.vip_expire_date || '无'" />
            <v-divider />
            <v-list-item title="总空间" :subtitle="status.storage_info?.total || '未知'" />
            <v-divider />
            <v-list-item title="已用空间" :subtitle="status.storage_info?.used || '未知'" />
            <v-divider />
            <v-list-item title="剩余空间" :subtitle="status.storage_info?.remaining || '未知'" />
          </v-list>
        </template>
        <v-btn class="mt-4" color="primary" prepend-icon="mdi-refresh" :loading="loading" @click="refresh">刷新账户信息</v-btn>
      </v-card-text>
    </v-card>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { normalizeApiResponse, responseMessage } from '../utils/apiResponse.js'

const props = defineProps({
  api: { type: [Object, Function], default: null },
  initialConfig: { type: Object, default: () => ({}) },
  // 快捷入口的只读详情会传 false，避免显示没有宿主监听器的配置按钮。
  show_switch: { type: Boolean, default: true },
})
const show_switch = props.show_switch
const emit = defineEmits(['switch', 'config'])
// MoviePilot 新版宿主使用 switch；兼容仍使用 config 事件的旧版宿主。
const openConfig = () => {
  emit('switch')
  emit('config')
}
const loading = ref(false)
const status = ref({ success: false, error_message: '请在配置页面中设置有效的115网盘Cookie' })
const vipText = computed(() => {
  const user = status.value.user_info || {}
  return user.is_forever_vip ? '永久VIP' : user.is_vip ? 'VIP' : '非VIP'
})
const refresh = async () => {
  if (typeof props.api?.get !== 'function') {
    status.value = { success: false, error_message: '宿主 API 尚未就绪' }
    return
  }
  loading.value = true
  try {
    const normalized = normalizeApiResponse(
      await props.api.get('plugin/P115UploadEnhancerVUE/account_status'),
    )
    const payload = normalized.payload
    if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
      status.value = {
        ...payload,
        success: payload.success ?? normalized.success,
        error_message:
          payload.error_message ||
          (!normalized.success ? responseMessage(normalized, '账户状态获取失败') : undefined),
      }
    } else {
      status.value = {
        success: normalized.success,
        error_message: normalized.success
          ? undefined
          : responseMessage(normalized, '账户状态获取失败'),
      }
    }
  } catch (error) {
    status.value = { success: false, error_message: error.message || '账户状态获取失败' }
  } finally {
    loading.value = false
  }
}
onMounted(refresh)
</script>
