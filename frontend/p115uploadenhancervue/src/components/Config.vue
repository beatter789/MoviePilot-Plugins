<template>
  <div class="page-scroll">
    <v-card variant="outlined">
      <v-card-title>115上传增强配置</v-card-title>
      <v-card-text>
        <v-alert v-if="message" :type="messageType" variant="tonal" density="compact" class="mb-4">{{ message }}</v-alert>
        <v-switch v-model="local.enabled" label="启用插件" color="success" />
        <v-text-field v-model="local.cookie" label="115 Cookie" variant="outlined" density="comfortable" hint="可手动填写，也可以使用扫码登录" persistent-hint clearable />
        <v-row>
          <v-col cols="12" md="4"><v-btn block color="primary" prepend-icon="mdi-qrcode-scan" @click="openQr">扫码获取 Cookie</v-btn></v-col>
          <v-col cols="12" md="4"><v-btn block variant="outlined" prepend-icon="mdi-account-check" @click="checkCookie">检查 Cookie</v-btn></v-col>
          <v-col cols="12" md="4"><v-btn block variant="outlined" color="warning" prepend-icon="mdi-delete-sweep" @click="clearCache">清理缓存</v-btn></v-col>
        </v-row>
        <v-divider class="my-5" />
        <v-switch v-model="local.upload_module_enhancement" label="启用上传增强" />
        <v-row>
          <v-col cols="12" md="6"><v-text-field v-model.number="local.upload_module_wait_time" label="等待间隔（秒）" type="number" /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model.number="local.upload_module_wait_timeout" label="最长等待（秒）" type="number" /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="local.upload_module_skip_upload_wait_size" label="跳过等待大小" placeholder="800M" /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="local.upload_module_force_upload_wait_size" label="强制等待大小" placeholder="5G" /></v-col>
        </v-row>
        <v-switch v-model="local.upload_module_skip_slow_upload" label="秒传失败跳过上传" />
        <v-text-field v-if="local.upload_module_skip_slow_upload" v-model="local.upload_module_skip_slow_upload_size" label="秒传失败跳过上传大小" placeholder="5G" />
        <v-divider class="my-5" />
        <v-btn color="primary" prepend-icon="mdi-content-save" @click="$emit('save', local)">保存配置</v-btn>
      </v-card-text>
    </v-card>
    <QrCodeDialog v-model="qr.show" :qr="qr" @update:model-value="handleQrModelUpdate" @refresh="getQr" @close="closeQr" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import QrCodeDialog from './QrCodeDialog.vue'
import { normalizeApiResponse, responseMessage } from '../utils/apiResponse.js'

const props = defineProps({
  api: { type: [Object, Function], default: null },
  initialConfig: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['save'])
const local = reactive({ enabled: false, cookie: '', upload_module_enhancement: true, upload_module_wait_time: 300, upload_module_wait_timeout: 3600, upload_module_skip_upload_wait_size: '0', upload_module_force_upload_wait_size: '0', upload_module_skip_slow_upload: false, upload_module_skip_slow_upload_size: '0', ...(props.initialConfig || {}) })
const message = ref(''); const messageType = ref('info')
const qr = reactive({ show: false, loading: false, error: '', image: '', uid: '', time: '', sign: '', status: '等待扫码', timer: null, checkInFlight: false, generation: 0 })
const call = (path, options) => {
  const method = options?.method === 'post' ? 'post' : 'get'
  if (typeof props.api?.[method] !== 'function') throw new Error('宿主 API 尚未就绪')
  return props.api[method](path, options?.data)
}
const stopQrPolling = () => {
  if (qr.timer) clearInterval(qr.timer)
  qr.timer = null
  qr.checkInFlight = false
}
const openQr = () => { qr.show = true; getQr() }
const closeQr = () => { stopQrPolling(); qr.generation += 1; qr.show = false }
const handleQrModelUpdate = (value) => { if (value) qr.show = true; else closeQr() }
const getQr = async () => {
  const generation = qr.generation + 1
  qr.generation = generation
  stopQrPolling()
  Object.assign(qr, { loading: true, error: '', image: '', uid: '', time: '', sign: '', status: '等待扫码' })
  try {
    const normalized = normalizeApiResponse(await call('plugin/P115UploadEnhancerVUE/get_qrcode'))
    const data = normalized.payload
    if (!normalized.success) throw new Error(responseMessage(normalized, '获取二维码失败'))
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('二维码响应格式无效')
    for (const key of ['qrcode', 'uid', 'time', 'sign']) {
      if (!data[key]) throw new Error('二维码响应缺少必要参数')
    }
    if (generation !== qr.generation || !qr.show) return
    Object.assign(qr, { image: data.qrcode, uid: data.uid, time: data.time, sign: data.sign, status: '等待扫码' })
    qr.timer = setInterval(checkQr, 3000)
  } catch (error) { qr.error = error.message || '获取二维码失败' } finally { qr.loading = false }
}
const checkQr = async () => {
  if (!qr.uid || !qr.show || qr.checkInFlight) return
  const generation = qr.generation
  qr.checkInFlight = true
  try {
    const query = new URLSearchParams({ uid: qr.uid, time: qr.time, sign: qr.sign, client_type: 'alipaymini' })
    const normalized = normalizeApiResponse(await call(`plugin/P115UploadEnhancerVUE/check_qrcode?${query}`))
    if (generation !== qr.generation || !qr.show) return
    if (!normalized.success) throw new Error(responseMessage(normalized, '检查二维码失败'))
    const data = normalized.payload
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('二维码状态响应格式无效')
    if (data.status === 'success') {
      if (!data.cookie) { qr.status = '登录成功但未获取到 Cookie'; qr.error = qr.status; stopQrPolling(); return }
      local.cookie = data.cookie; qr.status = '登录成功'; message.value = '扫码成功，请点击保存配置'; messageType.value = 'success'; closeQr()
    } else if (data.status === 'scanned') qr.status = '已扫码，请确认登录'
    else if (data.status === 'expired' || data.status === 'error') { qr.status = data.msg || '二维码失效'; qr.error = qr.status; stopQrPolling() }
    else if (data.status !== 'waiting') { qr.status = data.msg || '二维码状态未知'; qr.error = qr.status; stopQrPolling() }
  } catch (error) { qr.error = error.message || '检查二维码失败' }
  finally { if (generation === qr.generation) qr.checkInFlight = false }
}
const checkCookie = async () => { message.value = '正在检查 Cookie...'; messageType.value = 'info'; try { const normalized = normalizeApiResponse(await call('plugin/P115UploadEnhancerVUE/refresh_account_status', { method: 'post' })); message.value = responseMessage(normalized, normalized.success ? 'Cookie 有效' : 'Cookie 无效'); messageType.value = normalized.success ? 'success' : 'warning' } catch (e) { message.value = e.message || 'Cookie 检查失败'; messageType.value = 'error' } }
const clearCache = async () => { try { const normalized = normalizeApiResponse(await call('plugin/P115UploadEnhancerVUE/clear_cache', { method: 'post' })); message.value = responseMessage(normalized, normalized.success ? '缓存清理完成' : '缓存清理失败'); messageType.value = normalized.success ? 'success' : 'error' } catch (e) { message.value = e.message || '缓存清理失败'; messageType.value = 'error' } }
onBeforeUnmount(closeQr)
</script>
