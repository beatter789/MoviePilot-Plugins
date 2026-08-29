<template>
  <v-dialog :model-value="modelValue" max-width="500" @update:model-value="$emit('update:modelValue', $event)">
    <v-card>
      <v-card-title class="d-flex align-center"><v-icon icon="mdi-qrcode" class="mr-2" />115网盘扫码登录</v-card-title>
      <v-card-text class="text-center">
        <v-alert v-if="qr.error" type="error" variant="tonal" density="compact" class="mb-3">{{ qr.error }}</v-alert>
        <v-progress-circular v-if="qr.loading" indeterminate color="primary" />
        <template v-else-if="qr.image">
          <div class="text-body-2 font-weight-medium mb-2">请选择扫码方式</div>
          <v-chip-group
            :model-value="qr.clientType"
            mandatory
            selected-class="text-primary"
            class="mb-3"
            @update:model-value="$emit('client-type-change', $event)"
          >
            <v-chip v-for="type in clientTypes" :key="type.value" :value="type.value" color="primary" variant="outlined" size="small">
              {{ type.label }}
            </v-chip>
          </v-chip-group>
          <div class="qr-frame"><img :src="qr.image" width="240" height="240" alt="115登录二维码" /></div>
          <div class="text-body-2 text-medium-emphasis mt-3">{{ qr.tips }}</div>
          <div class="text-subtitle-2 text-primary mt-1">{{ qr.status }}</div>
          <v-btn class="mt-3" variant="tonal" prepend-icon="mdi-refresh" @click="$emit('refresh')">刷新二维码</v-btn>
        </template>
        <div v-else>点击刷新获取二维码</div>
      </v-card-text>
      <v-card-actions><v-spacer /><v-btn variant="text" prepend-icon="mdi-close" @click="$emit('close')">关闭</v-btn></v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup>
defineProps({ modelValue: Boolean, qr: { type: Object, required: true }, clientTypes: { type: Array, required: true } })
defineEmits(['update:modelValue', 'client-type-change', 'refresh', 'close'])
</script>

<style scoped>
.qr-frame {
  display: inline-flex;
  padding: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
}
</style>
