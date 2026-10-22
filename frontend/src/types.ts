export type Product = {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  price: number
}

export type ChatProductCard = {
  product_id: string
  name: string
  garment_type: string
  price: number
  description: string
  image_file_path: string
  sizes: { size: string; quantity: number }[]
}

export type ProductMatch = {
  product_id: string
  name: string
  garment_type: string
  price: number
  short_description: string
  image_file_path: string
}

export type ChatReply = {
  reply: string
  products: ChatProductCard[]
  matches: ProductMatch[]
}

export type Shopper = {
  id: number
  name: string
  email: string
  first_name: string
  last_name: string
  preferred_size?: string
}

export type ShopOrder = {
  id: number
  product_id: string
  product_name: string
  size: string
  color: string
  status: string
  remaining: number
}

export type SizeStock = {
  size: string
  quantity: number
}

export type ProductDetail = Product & {
  sizes: SizeStock[]
}
