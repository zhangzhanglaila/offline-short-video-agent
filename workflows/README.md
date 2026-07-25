# Workflows

ComfyUI 工作流模板。

## 目录
- `image/`   文生图(flux_dev.json)
- `video/`   文生视频(wan22_t2v.json)、图生视频(wan22_i2v.json)
- `tts/`     预留(TTS 不在 E5 范围)

## 占位符
`{{prompt}}` `{{width}}` `{{height}}` `{{steps}}` `{{seed}}`

由 `services/comfyui/template.py` 在调用时插值。
