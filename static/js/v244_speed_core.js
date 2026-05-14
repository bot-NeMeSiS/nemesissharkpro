
/* V244 · Speed Core helpers */
window.NMS_SPEED_CORE_V244 = {
  realOnly: true,
  smartCache: true,
  lazyLoading: true,
  criticalDataFirst: true,
  reduceApiDuplicates: true,
  cacheIsValid: function(timestamp, ttlSeconds){
    if(!timestamp || !ttlSeconds) return false;
    return ((Date.now() - timestamp) / 1000) <= ttlSeconds;
  }
};
