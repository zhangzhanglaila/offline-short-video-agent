import { useEffect, useState } from 'react'
import { useProductStore } from '../stores/productStore'
import { useNavigate } from 'react-router-dom'

const pink = '#FB7299'
const btn = (bg: string, color = '#fff'): React.CSSProperties => ({
  padding: '6px 16px', background: bg, color, border: 'none', borderRadius: 4, fontSize: 13, cursor: 'pointer', fontWeight: 500,
})

export default function ProductList() {
  const { products, total, loading, loadProducts, removeProduct } = useProductStore()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  useEffect(() => { loadProducts({ search, page }) }, [search, page])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#232529' }}>商品管理</h1>
        <button onClick={() => navigate('/products/new')} style={btn(pink)}>+ 录入商品</button>
      </div>

      <div style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: 20 }}>
        <div style={{ marginBottom: 16 }}>
          <input
            type="text"
            placeholder="搜索商品名称..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            style={{ width: 320, padding: '10px 12px', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 15, outline: 'none', color: '#232529' }}
          />
        </div>

        {loading ? (
          <p style={{ color: '#9499A0', padding: 40, textAlign: 'center' }}>加载中...</p>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#9499A0' }}>
            <p style={{ fontSize: 48, marginBottom: 8 }}>📦</p>
            <p>暂无商品，点击上方按钮录入</p>
          </div>
        ) : (
          <>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #E3E5E7' }}>
                  {['商品名称', '分类', '价格', '平台', '状态', '操作'].map(h => (
                    <th key={h} style={{ padding: '10px 12px', textAlign: 'left', color: '#9499A0', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id} style={{ borderBottom: '1px solid #F0F1F3' }}>
                    <td style={{ padding: '12px', fontWeight: 600, color: '#232529' }}>{p.name}</td>
                    <td style={{ padding: '12px', color: '#606773' }}>{p.category}</td>
                    <td style={{ padding: '12px', color: '#606773' }}>{p.currency} {p.price}</td>
                    <td style={{ padding: '12px', color: '#606773' }}>{p.platform}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: 3, fontSize: 11, background: p.status === 'active' ? '#E8F5E9' : '#F5F5F5', color: p.status === 'active' ? '#4CAF50' : '#999' }}>
                        {p.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button onClick={() => navigate(`/products/${p.id}`)} style={{ ...btn('#fff', pink), border: `1px solid ${pink}`, marginRight: 8 }}>编辑</button>
                      <button onClick={() => { if (confirm('确认删除?')) removeProduct(p.id) }} style={{ ...btn('#fff', '#FF5252'), border: '1px solid #FF5252', marginRight: 8 }}>删除</button>
                      <button onClick={() => navigate(`/generate?product_id=${p.id}`)} style={btn(pink)}>生成视频</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16, fontSize: 13, color: '#9499A0' }}>
              <span>共 {total} 件商品</span>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} style={{ ...btn('#fff', '#606773'), border: '1px solid #E3E5E7', opacity: page <= 1 ? 0.4 : 1 }}>上一页</button>
                <span>第 {page} 页</span>
                <button disabled={products.length < 20} onClick={() => setPage(p => p + 1)} style={{ ...btn('#fff', '#606773'), border: '1px solid #E3E5E7', opacity: products.length < 20 ? 0.4 : 1 }}>下一页</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
