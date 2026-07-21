# 📅 动态化视频 开发阶段规划

## 原则
- **一次一个动效层**，充分测试再进下一步
- 每个阶段**独立可见效果提升**，可单独交付
- 全程**降级保底**，不破坏已完成的Phase 0-5
- 复用已有动效资产，不重造轮子

---

## 阶段总览

| 阶段 | 主题 | 解决的问题 | 预估 | 影响 |
|------|------|-----------|------|------|
| **D1** | 运动镜头+全屏 | 静态如PPT / 照片不满 | 1-2天 | ⭐⭐⭐⭐⭐ |
| **D2** | 文字/字幕入场动画 | 元素一次性铺满 | 2-3天 | ⭐⭐⭐⭐ |
| **D3** | 场景内多元素分层 | 无元素编排/交互 | 3-4天 | ⭐⭐⭐⭐ |
| **D4** | 丰富转场 | 切换单一 | 1-2天 | ⭐⭐⭐ |
| **D5** | 视频素材背景 | 背景静止 | 2-3天 | ⭐⭐⭐⭐ |
| **D6** | 节奏音乐(可选) | 无声/无节奏 | 2-3天 | ⭐⭐⭐ |

**优先级**: D1 → D2 → D3 是核心（直接回应用户反馈），D4-D6 为进阶。

---

## Phase D1: 运动镜头 + 全屏优化 【最高优先】

### 目标
让画面"动起来"，照片全屏铺满，字幕更轻盈。

### 交付物
```
core/compose/motion/
├── __init__.py
├── ken_burns.py           # zoompan参数生成器
└── animation_spec.py      # AnimationSpec模型

改造:
- ffmpeg_composer.py: _render_clip支持zoompan滤镜
- scene_image_renderer.py: 字幕条改为轻量lower-third
- video_compose_agent.py: 内容场景启用运镜

test_ken_burns.py
```

### 验收标准
- [ ] 内容场景背景有缓慢缩放/平移
- [ ] 运镜方向随场景变化（不雷同）
- [ ] 照片full-bleed铺满，无黑边
- [ ] 字幕改为轻量样式，素材可视≥90%
- [ ] zoompan失败自动降级静态
- [ ] 抽首尾帧对比确认有位移
- [ ] 单元测试通过

### 关键风险
- zoompan抖动 → 用足够帧数+平滑表达式
- 性能下降 → 控制分辨率和时长

---

## Phase D2: 文字/字幕入场动画

### 目标
文字元素动态入场，不再一次性静态显示。

### 交付物
```
core/compose/motion/
├── layer_renderer.py      # 元素层PNG渲染(带alpha)
└── text_animations.py     # 淡入/上滑/逐字/放大

改造:
- clip_builder.py(新): 用overlay+表达式合成动画元素
- video_compose_agent.py: 字幕/标题走动画

test_text_animations.py
```

### 验收标准
- [ ] 标题支持逐字/逐行/淡入放大 ≥2种
- [ ] 字幕淡入或从底部滑入
- [ ] 复用spring_easing的缓动曲线
- [ ] 动画时长与场景时长匹配
- [ ] 失败降级为静态文字
- [ ] 单元测试通过

---

## Phase D3: 场景内多元素分层与编排

### 目标
一个场景有多个元素**先后出现**，制造"编排/交互"感。

### 交付物
```
core/compose/motion/
├── element_library.py     # 图标/形状/序号/要点框
└── scene_composer.py      # 多图层时间轴编排

改造:
- Scene模型: 增加elements字段
- content_analysis_agent: prompt增强，LLM输出元素编排
- video_compose_agent: 多层时间轴合成

test_scene_composer.py
```

### 验收标准
- [ ] 场景支持≥2个独立元素图层
- [ ] 元素按时间轴先后出现
- [ ] 关键词强调（高亮/放大）
- [ ] 支持要点列表逐条出现
- [ ] LLM可产出元素编排（含规则降级）
- [ ] 单元测试通过

---

## Phase D4: 丰富转场

### 目标
场景切换多样化。

### 交付物
```
改造:
- ffmpeg_composer.py: 接入transition_effects的多种转场
- 转场智能选择(按内容/节奏)

test_transitions_integration.py
```

### 验收标准
- [ ] 支持≥4种转场（fade/slide/wipe/zoom）
- [ ] 按场景类型/节奏自动选择
- [ ] 转场失败降级硬切
- [ ] 单元测试通过

---

## Phase D5: 视频素材背景

### 目标
背景可用真实视频素材（本身就是动态的）。

### 交付物
```
改造:
- material_fetch_agent: 接入stock_video_module视频搜索
- MaterialAsset: 支持media_type=video
- clip_builder: 视频背景loop/scale/cover-fit
- video_compose_agent: 视频背景优先，静图fallback

test_video_material.py
```

### 验收标准
- [ ] 能检索Pexels/Pixabay视频素材
- [ ] 视频cover-fit全屏 + loop到场景时长
- [ ] 视频/静图混合使用
- [ ] 无视频时降级静图+Ken Burns
- [ ] 单元测试通过

---

## Phase D6: 节奏与音乐（可选增强）

### 目标
加背景音乐、节拍同步、TTS旁白。

### 交付物
```
改造:
- 新增audio编排: 复用rhythm_engine/audio_analyzer/tts_module
- video_compose_agent: 混入BGM + 节拍对齐剪辑
- narration字段接TTS

test_audio_integration.py
```

### 验收标准
- [ ] 支持BGM混入
- [ ] 场景切换可对齐节拍
- [ ] narration生成TTS旁白（可选）
- [ ] 无音频降级为无声
- [ ] 单元测试通过

---

## 每阶段工作流

1. 阅读本阶段需求(`docs/10`)和设计(`docs/11`)
2. 实现模块 + 单元测试
3. 真实端到端验证（抽帧/对比确认动态效果）
4. 更新 `devlog/daily/` 当日日志
5. git提交（安全检查.env不入库）
6. 更新阶段状态

---

## 里程碑

- **M1 (D1完成)**: 视频"动起来"，不再是静态PPT ← 直接回应用户
- **M2 (D1-D3完成)**: 元素有编排有交互，核心诉求达成
- **M3 (D4-D5完成)**: 转场丰富 + 视频背景，多样化吸睛
- **M4 (D6完成)**: 有声有节奏，成片质感

---

*最后更新: 2026-07-26*
*计划版本: 1.0*
