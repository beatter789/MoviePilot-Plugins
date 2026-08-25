<template>
  <v-dialog :model-value="modelValue" max-width="450" @update:model-value="$emit('update:modelValue', $event)">
    <v-card>
      <v-card-title class="d-flex align-center"><v-icon icon="mdi-qrcode" class="mr-2" />115网盘扫码登录</v-card-title>
      <v-card-text class="text-center">
        <v-alert v-if="qr.error" type="error" variant="tonal" density="compact" class="mb-3">{{ qr.error }}</v-alert>
        <v-progress-circular v-if="qr.loading" indeterminate color="primary" />
        <template v-else-if="qr.image">
          <v-card variant="outlined" class="pa-2 d-inline-block"><img :src="qr.image" width="240" height="240" alt="115登录二维码" /></v-card>
          <div class="mt-3">{{ qr.status }}</div>
          <v-btn class="mt-3" variant="tonal" prepend-icon="mdi-refresh" @click="$emit('refresh')">刷新二维码</v-btn>
        </template>
        <div v-else>点击刷新获取二维码</div>
      </v-card-text>
      <v-card-actions><v-spacer /><v-btn variant="text" @click="$emit('close')">关闭</v-btn></v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup>
defineProps({ modelValue: Boolean, qr: { type: Object, required: true } })
defineEmits(['update:modelValue', 'refresh', 'close'])
</script>
