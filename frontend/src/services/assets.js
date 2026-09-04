const assetUrls = import.meta.glob('../assets/*.{png,jpg,jpeg,webp,svg}', {
  eager: true,
  query: '?url',
  import: 'default',
})

export function resolveAsset(value) {
  if (!value) return ''
  if (/^https?:\/\//i.test(value) || value.startsWith('data:')) return value

  const fileName = value.split('/').pop()
  const match = Object.entries(assetUrls).find(([key]) => key.endsWith(`/${fileName}`))
  return match?.[1] || value
}
