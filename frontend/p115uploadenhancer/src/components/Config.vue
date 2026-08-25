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
    <QrCodeDialog v-model="qr.show" :qr="qr" @refresh="getQr" @close="closeQr" />
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import QrCodeDialog from './QrCodeDialog.vue'
const props = defineProps({ api: { type: [Object, Function], default: null }, config: { type: Object, required: true } })
const emit = defineEmits(['save'])
const local = reactive({ ...props.config, upload_module_enhancement: true, upload_module_wait_time: 300, upload_module_wait_timeout: 3600, upload_module_skip_upload_wait_size: '0', upload_module_force_upload_wait_size: '0', upload_module_skip_slow_upload: false, upload_module_skip_slow_upload_size: '0' })
const message = ref(''); const messageType = ref('info')
const qr = reactive({ show: false, loading: false, error: '', image: '', uid: '', time: '', sign: '', status: '等待扫码', timer: null })
const call = (path, options) => props.api?.[options?.method === 'post' ? 'post' : 'get']?.(path, options?.data)
const openQr = () => { qr.show = true; getQr() }
const closeQr = () => { if (qr.timer) clearInterval(qr.timer); qr.timer = null; qr.show = false }
const getQr = async () => {
  qr.loading = true; qr.error = ''
  try {
    const response = await call('plugin/P115UploadEnhancer/get_qrcode')
    const data = response?.data || response
    if (response?.code !== undefined && response.code !== 0) throw new Error(response.msg || '获取二维码失败')
    Object.assign(qr, { image: data.qrcode, uid: data.uid, time: data.time, sign: data.sign, status: '等待扫码' })
    if (qr.timer) clearInterval(qr.timer)
    qr.timer = setInterval(checkQr, 3000)
  } catch (error) { qr.error = error.message || '获取二维码失败' } finally { qr.loading = false }
}
const checkQr = async () => {
  if (!qr.uid || !qr.show) return
  try {
    const query = new URLSearchParams({ uid: qr.uid, time: qr.time, sign: qr.sign, client_type: 'alipaymini' })
    const response = await call(`plugin/P115UploadEnhancer/check_qrcode?${query}`)
    const data = response?.data || response
    if (data.status === 'success') { local.cookie = data.cookie || ''; qr.status = '登录成功'; message.value = '扫码成功，请点击保存配置'; messageType.value = 'success'; closeQr() }
    else if (data.status === 'scanned') qr.status = '已扫码，请确认登录'
    else if (data.status === 'expired' || data.status === 'error') { qr.status = data.msg || '二维码失效'; qr.error = qr.status; if (qr.timer) clearInterval(qr.timer) }
  } catch (error) { qr.error = error.message || '检查二维码失败' }
}
const checkCookie = async () => { message.value = '正在检查 Cookie...'; messageType.value = 'info'; try { const r = await call('plugin/P115UploadEnhancer/refresh_account_status', { method: 'post' }); message.value = r?.msg || (r?.success ? 'Cookie 有效' : 'Cookie 无效'); messageType.value = r?.success ? 'success' : 'warning' } catch (e) { message.value = e.message; messageType.value = 'error' } }
const clearCache = async () => { try { const r = await call('plugin/P115UploadEnhancer/clear_cache', { method: 'post' }); message.value = r?.msg || '缓存清理完成'; messageType.value = 'success' } catch (e) { message.value = e.message; messageType.value = 'error' } }
</script>
