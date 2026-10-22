export function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(price)
}

export function shortDescription(description: string): string {
  const trimmed = description.trim()
  const firstSentence = trimmed.split(/(?<=\.)\s/)[0] ?? trimmed
  if (firstSentence.length <= 140) {
    return firstSentence
  }
  return `${firstSentence.slice(0, 137).trimEnd()}…`
}
