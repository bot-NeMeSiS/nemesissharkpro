
/* V228 · Performance helpers */
window.NMS_PERFORMANCE_V228 = {
  realOnly: true,
  cacheFirst: true,
  lazyLoading: true,
  fallbackMessage: "Esperando datos reales del proveedor.",
  shouldUseCache: function(ageSeconds, ttlSeconds){ return ageSeconds >= 0 && ageSeconds <= ttlSeconds; }
};
