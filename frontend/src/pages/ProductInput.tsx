import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { createProduct, fetchProduct, updateProduct, fetchProductCategories } from '../api/ecom'

const pink = '#FB7299'
const inputStyle: React.CSSProperties = { width: '100%', padding: '10px 12px', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 15, outline: 'none', boxSizing: 'border-box', color: '#232529' }
const labelStyle: React.CSSProperties = { display: 'block', fontSize: 14, fontWeight: 500, color: '#232529', marginBottom: 6 }

export default function ProductInput() {
  const navigate = useNavigate()
  const { id } = useParams()
  const isEdit = !!id

  const [name, setName] = useState('')
  const [category, setCategory] = useState('')
  const [categoryOptions, setCategoryOptions] = useState<string[]>([])
  const [isCustomCategory, setIsCustomCategory] = useState(false)
  const [price, setPrice] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [description, setDescription] = useState('')
  const [sellingPoints, setSellingPoints] = useState('')
  const [platform, setPlatform] = useState('TikTok Shop')
  const [sourceUrl, setSourceUrl] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchProductCategories().then(res => setCategoryOptions(res.categories || [])).catch(() => {})
    if (isEdit) {
      fetchProduct(Number(id)).then(p => {
        setName(p.name)
        const cat = p.category || ''
        setCategory(cat)
        setPrice(String(p.price || ''))
        setCurrency(p.currency || 'USD')
        setDescription(p.description || '')
        setSellingPoints(Array.isArray(p.selling_points) ? p.selling_points.join('\n') : '')
        setPlatform(p.platform || '')
        setSourceUrl(p.source_url || '')
        // 分类不在已有列表中则切到自定义模式
        fetchProductCategories().then(res => {
          const cats = res.categories || []
          if (cat && !cats.includes(cat)) setIsCustomCategory(true)
        }).catch(() => {})
      })
    }
  }, [id])

  const validate = (): string | null => {
    if (!name.trim()) return '商品名称不能为空'
    if (!sellingPoints.trim()) return '请至少填写一个核心卖点'
    const points = sellingPoints.split('\n').map(s => s.trim()).filter(Boolean)
    if (points.length === 0) return '请至少填写一个核心卖点'
    if (points.length > 20) return '卖点最多 20 个'
    if (price && isNaN(parseFloat(price))) return '价格格式不正确'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err = validate()
    if (err) { setError(err); return }
    setSaving(true)
    setError('')

    const data = {
      name: name.trim(),
      category: category.trim(),
      price: parseFloat(price) || 0,
      currency,
      description: description.trim(),
      selling_points: sellingPoints.split('\n').map(s => s.trim()).filter(Boolean),
      platform,
      source_url: sourceUrl.trim(),
    }

    try {
      if (isEdit) {
        await updateProduct(Number(id), data)
      } else {
        await createProduct(data)
      }
      navigate('/products')
    } catch (e) {
      setError(String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, color: '#232529', marginBottom: 24 }}>{isEdit ? '编辑商品' : '录入商品'}</h1>

      <form onSubmit={handleSubmit} style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: 24, maxWidth: 640 }}>
        {error && <div style={{ padding: '10px 14px', background: '#FFF3F0', border: '1px solid #FFCCC7', borderRadius: 4, color: '#FF4D4F', fontSize: 13, marginBottom: 16 }}>{error}</div>}

        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>商品名称 *</label>
          <input value={name} onChange={e => setName(e.target.value)} style={inputStyle} placeholder="例: 无线蓝牙耳机" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div>
            <label style={labelStyle}>分类</label>
            <select
              value={isCustomCategory ? '__custom__' : category}
              onChange={e => {
                if (e.target.value === '__custom__') {
                  setIsCustomCategory(true)
                  setCategory('')
                } else {
                  setIsCustomCategory(false)
                  setCategory(e.target.value)
                }
              }}
              style={inputStyle}
            >
              <option value="">-- 选择分类 --</option>
              {categoryOptions.map(c => <option key={c} value={c}>{c}</option>)}
              <option value="__custom__">自定义...</option>
            </select>
            {isCustomCategory && (
              <input
                value={category}
                onChange={e => setCategory(e.target.value)}
                style={{ ...inputStyle, marginTop: 8 }}
                placeholder="输入自定义分类"
                autoFocus
              />
            )}
          </div>
          <div>
            <label style={labelStyle}>平台</label>
            <select value={platform} onChange={e => setPlatform(e.target.value)} style={inputStyle}>
              <option>TikTok Shop</option>
              <option>Shopee</option>
              <option>AliExpress</option>
              <option>Amazon</option>
              <option>其他</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div>
            <label style={labelStyle}>价格</label>
            <input type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>货币</label>
            <select value={currency} onChange={e => setCurrency(e.target.value)} style={inputStyle}>
              <option>USD</option>
              <option>CNY</option>
              <option>EUR</option>
              <option>GBP</option>
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>商品描述</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3} style={{ ...inputStyle, resize: 'vertical' }} placeholder="简要描述商品功能和特点..." />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>核心卖点（每行一个，必填） *</label>
          <textarea value={sellingPoints} onChange={e => setSellingPoints(e.target.value)} rows={4} style={{ ...inputStyle, resize: 'vertical' }} placeholder={"降噪续航40小时\n蓝牙5.3低延迟\nIPX5防水"} />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>商品链接（可选）</label>
          <input value={sourceUrl} onChange={e => setSourceUrl(e.target.value)} style={inputStyle} placeholder="https://..." />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" disabled={saving} style={{ padding: '10px 24px', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, cursor: 'pointer', fontWeight: 500, opacity: saving ? 0.6 : 1 }}>
            {saving ? '保存中...' : isEdit ? '保存修改' : '录入商品'}
          </button>
          <button type="button" onClick={() => navigate('/products')} style={{ padding: '10px 24px', background: '#fff', color: '#606773', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 14, cursor: 'pointer' }}>
            取消
          </button>
        </div>
      </form>
    </div>
  )
}
