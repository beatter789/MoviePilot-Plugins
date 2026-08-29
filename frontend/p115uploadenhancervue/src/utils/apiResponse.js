const hasOwn = (value, key) => Object.prototype.hasOwnProperty.call(value, key)

/**
 * MoviePilot V3 plugin APIs may return either a bare payload or the explicit
 * { success, message, data } envelope. Only the latter is unwrapped.
 */
export const isStrictApiEnvelope = (value) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  return ['success', 'message', 'data'].every((key) => hasOwn(value, key))
}

export const normalizeApiResponse = (response) => {
  const envelope = isStrictApiEnvelope(response)
  if (envelope) {
    return {
      envelope: true,
      payload: response.data,
      success: response.success !== false,
      message: response.message || '',
      raw: response,
    }
  }

  return {
    envelope: false,
    payload: response,
    success: !(response && typeof response === 'object' && response.success === false),
    message: response?.msg || response?.message || '',
    raw: response,
  }
}

export const responseMessage = (normalized, fallback) =>
  normalized.message || normalized.raw?.msg || normalized.raw?.message || fallback
