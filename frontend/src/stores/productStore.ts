import { create } from 'zustand'
import { type Product, fetchProducts, createProduct, updateProduct, deleteProduct } from '../api/ecom'

interface ProductState {
  products: Product[]
  total: number
  page: number
  loading: boolean
  error: string
  loadProducts: (params?: Record<string, string | number>) => Promise<void>
  addProduct: (data: Partial<Product>) => Promise<number>
  editProduct: (id: number, data: Partial<Product>) => Promise<void>
  removeProduct: (id: number) => Promise<void>
}

export const useProductStore = create<ProductState>((set, get) => ({
  products: [],
  total: 0,
  page: 1,
  loading: false,
  error: '',

  loadProducts: async (params = {}) => {
    set({ loading: true, error: '' })
    try {
      const res = await fetchProducts(params as Record<string, string>)
      set({ products: res.items, total: res.total, page: res.page, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  addProduct: async (data) => {
    const res = await createProduct(data)
    if (res.success) {
      await get().loadProducts()
      return res.id
    }
    throw new Error('创建失败')
  },

  editProduct: async (id, data) => {
    await updateProduct(id, data)
    await get().loadProducts()
  },

  removeProduct: async (id) => {
    await deleteProduct(id)
    await get().loadProducts()
  },
}))
