const json = (url) => fetch(url).then((r) => {
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
});

export const getSummary = () => json('/api/summary');
export const getAssets = () => json('/api/assets');
export const getAsset = (key) => json(`/api/assets/${encodeURIComponent(key)}`);
export const getJobs = () => json('/api/jobs?limit=20');
export const getInventory = () => json('/api/inventory?limit=10');
