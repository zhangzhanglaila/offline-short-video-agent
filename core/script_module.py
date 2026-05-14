# -*- coding: utf-8 -*-
"""
脚本&分镜生成模块 - 本地Ollama推理
输入赛道+选题，自动生成：黄金3秒钩子、15-60s口播脚本、分镜表、时长、标签
"""
import json
import time
import re
from typing import Dict, List, Optional
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

class ScriptModule:
    """脚本生成模块 - 基于Ollama本地LLM"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        """初始化脚本生成模块"""
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

    def generate_script(self, topic: Dict, platform: str = "抖音",
                       video_duration: int = 30, style: str = "爆款",
                       use_rag: bool = True, stream_callback=None) -> Dict:
        """
        生成完整口播脚本

        参数:
            topic: 选题字典，包含 title, hook, category, tags 等
            platform: 目标平台 (抖音/小红书/视频号)
            video_duration: 视频时长(秒)
            style: 风格 (爆款/温和/专业)
            use_rag: 是否启用RAG知识增强（搜索+检索事实注入Prompt）
            stream_callback: 流式回调函数 callback(chunk_text)，用于实时推送LLM输出

        返回:
            包含脚本、分镜、标题、描述、话题标签的字典
        """
        prompt = self._build_script_prompt(topic, platform, video_duration, style)

        # RAG知识增强：搜索选题相关事实，注入Prompt提升脚本质量
        if use_rag:
            try:
                from core.rag_engine import get_rag_engine
                rag = get_rag_engine()
                augmented = rag.augment_prompt(topic, prompt)
                if augmented != prompt:
                    prompt = augmented
            except Exception:
                pass  # RAG失败不影响主流程

        # 调用Ollama生成（支持流式），失败则尝试云端API
        script_content = self._call_ollama(prompt, stream_callback=stream_callback)
        if '"error"' in script_content or not script_content.strip():
            script_content = self._call_cloud_api(prompt, stream_callback=stream_callback)

        # 解析生成的内容
        result = self._parse_script_content(script_content, topic, platform)

        # 重试逻辑：如果解析出的full_script为空或明显是错误响应，再问一次
        if not result.get("full_script") and '"error"' not in script_content:
            retry_prompt = (
                f"你上次输出的内容无法解析为有效JSON。请严格只输出一个JSON对象，不要包含```json标记或其他文字。\n\n"
                f"JSON必须包含以下字段: hook, body, cta, full_script, storyboard(数组，每项含scene/subtitle/duration/bullets)。\n"
                f"选题: {topic.get('title', '')}，赛道: {topic.get('category', '')}，时长: {video_duration}秒。"
            )
            retry_content = self._call_ollama(retry_prompt, timeout=90)
            if '"error"' in retry_content or not retry_content.strip():
                retry_content = self._call_cloud_api(retry_prompt)
            if retry_content.strip() and '"error"' not in retry_content:
                retry_result = self._parse_script_content(retry_content, topic, platform)
                if retry_result.get("full_script"):
                    result = retry_result

        return result

    def _build_script_prompt(self, topic: Dict, platform: str, duration: int, style: str) -> str:
        """构建脚本生成Prompt — 简洁介绍主题"""
        title = topic.get("title", "")
        hook = topic.get("hook", "")

        hook_line = f"开头用这句话抓人：{hook}" if hook else "开头用一个有趣的悬念或数据抓住观众"

        return f"""你是短视频口播写手。请围绕「{title}」写一段{duration}秒的介绍文案。

{hook_line}

要求：
- 口语化、有感染力、内容详实丰富
- body部分至少包含3-5个要点或细节，每个要点展开说明
- 纯口播文案，禁止写拍摄指令
- 总字数不少于200字

直接输出JSON（不要markdown代码块）：
{{
  "hook": "开头文案（1-2句）",
  "body": "主体介绍（3-5个要点，每个要点2-3句话展开说明，内容丰富详实）",
  "cta": "结尾（1-2句）",
  "full_script": "完整口播文案（hook+body+cta拼接，不少于200字）"
}}"""

    def _call_ollama(self, prompt: str, timeout: int = OLLAMA_TIMEOUT, stream_callback=None) -> str:
        """调用Ollama API生成内容，支持流式输出"""
        import urllib.request
        import urllib.error

        use_stream = stream_callback is not None
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": use_stream,
            "options": {
                "temperature": 0.8,
                "top_p": 0.9,
                "num_predict": 2048,
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if use_stream:
                    # 流式读取：逐行解析JSON chunks
                    full_text = ""
                    for line in response:
                        line = line.decode("utf-8").strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                full_text += token
                                stream_callback(token)
                        except json.JSONDecodeError:
                            continue
                    return full_text
                else:
                    result = json.loads(response.read().decode("utf-8"))
                    return result.get("response", "")
        except urllib.error.URLError as e:
            return '{"error": "Ollama连接失败: ' + str(e).replace('"', "'") + '", "script": {}}'
        except json.JSONDecodeError as e:
            return '{"error": "响应解析失败", "script": {}}'

    def _call_cloud_api(self, prompt: str, stream_callback=None) -> str:
        """调用云端API（支持OpenAI格式和Anthropic格式，支持流式）"""
        import os
        try:
            import requests
            from config import get_cloud_llm_config

            cfg = get_cloud_llm_config()
            if not cfg["api_key"]:
                return '{"error": "未配置云端API密钥", "script": {}}'

            api_base = cfg["api_base"]
            headers = {'Content-Type': 'application/json'}

            # 检测Anthropic格式（api_base包含/anthropic或模型名包含claude/minimax）
            is_anthropic = '/anthropic' in api_base or 'claude' in cfg["model"].lower() or 'minimax' in cfg["model"].lower()

            use_stream = stream_callback is not None

            if is_anthropic:
                # Anthropic Messages API格式
                url = api_base.rstrip('/') + '/v1/messages'
                headers['x-api-key'] = cfg["api_key"]
                headers['anthropic-version'] = '2023-06-01'
                payload = {
                    'model': cfg["model"],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 2048,
                    'temperature': 0.8,
                    'stream': use_stream,
                }
            else:
                # OpenAI Chat Completions格式
                url = api_base.rstrip('/') + '/chat/completions'
                headers['Authorization'] = f'Bearer {cfg["api_key"]}'
                payload = {
                    'model': cfg["model"],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 2048,
                    'temperature': 0.8,
                    'stream': use_stream,
                }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120,
                proxies={'http': None, 'https': None},
                stream=use_stream,
            )

            if response.status_code != 200:
                return '{"error": "HTTP ' + str(response.status_code) + ': ' + response.text[:200].replace('"', "'") + '", "script": {}}'

            if use_stream:
                # 流式读取SSE
                full_text = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode("utf-8", errors="replace")
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if is_anthropic:
                            # Anthropic SSE: {"type":"content_block_delta","delta":{"text":"..."}}
                            if chunk.get("type") == "content_block_delta":
                                token = chunk.get("delta", {}).get("text", "")
                                if token:
                                    full_text += token
                                    stream_callback(token)
                        else:
                            # OpenAI SSE: {"choices":[{"delta":{"content":"..."}}]}
                            choices = chunk.get("choices", [])
                            if choices:
                                token = choices[0].get("delta", {}).get("content", "")
                                if token:
                                    full_text += token
                                    stream_callback(token)
                    except json.JSONDecodeError:
                        continue
                return full_text

            result = response.json()

            # 解析响应（兼容两种格式）
            if is_anthropic and 'content' in result:
                # Anthropic格式: result.content[0].text
                content_blocks = result.get('content', [])
                if content_blocks and isinstance(content_blocks, list):
                    return content_blocks[0].get('text', '')
                return '{"error": "Anthropic响应格式异常", "script": {}}'
            else:
                # OpenAI格式: result.choices[0].message.content
                return result['choices'][0]['message']['content']
        except Exception as e:
            return '{"error": "云端API调用失败: ' + str(e).replace('"', "'") + '", "script": {}}'

    def _extract_json_from_text(self, text: str) -> str:
        """从LLM响应中鲁棒提取JSON — 处理markdown代码块、贪婪匹配、多JSON块等问题。"""
        # 1. 去掉 markdown 代码块标记
        cleaned = re.sub(r'```(?:json)?\s*\n?', '', text)
        cleaned = re.sub(r'\n?```', '', cleaned)

        # 2. 平衡括号匹配 — 找到所有顶级JSON对象
        candidates = []
        depth = 0
        start = -1
        for i, ch in enumerate(cleaned):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    candidates.append(cleaned[start:i + 1])
                    start = -1

        # 3. 按长度降序尝试每个候选JSON块
        candidates.sort(key=len, reverse=True)
        for cand in candidates:
            try:
                json.loads(cand)
                return cand
            except json.JSONDecodeError:
                continue

        # 4. 回退到旧贪婪匹配（兼容无嵌套JSON的情况）
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            return json_match.group()

        return ""

    def _parse_script_content(self, content: str, topic: Dict, platform: str) -> Dict:
        """解析Ollama返回的内容"""
        json_str = self._extract_json_from_text(content)
        if json_str:
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                parsed = self._fallback_parse(content)
        else:
            parsed = self._fallback_parse(content)

        # 构建完整结果
        result = {
            "topic_id": topic.get("id"),
            "topic_title": topic.get("title"),
            "category": topic.get("category"),
            "platform": platform,
            "hook": parsed.get("hook", topic.get("hook", "")),
            "body": parsed.get("body", ""),
            "cta": parsed.get("cta", "觉得有用的话，点个赞呗！"),
            "full_script": parsed.get("full_script", ""),
            "storyboard": parsed.get("storyboard", []),
            "chart_data": parsed.get("chart_data", []),
            "diagram_layout": parsed.get("diagram_layout", ""),
            "suggested_tags": topic.get("tags", []),
            "raw_llm_response": content,
        }

        return result

    def _fallback_parse(self, content: str) -> Dict:
        """降级解析 - 当JSON解析失败时，用正则从JSON/文本中提取字段。"""
        hook = ""
        body = ""
        cta = ""
        storyboard = []

        # 策略1: 用正则从 JSON-like 内容中提取字段值（处理LLM返回的畸变JSON）
        hook_m = re.search(r'"hook"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
        body_m = re.search(r'"body"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
        cta_m = re.search(r'"cta"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
        full_m = re.search(r'"full_script"\s*:\s*"((?:[^"\\]|\\.)*)"', content)

        if hook_m:
            hook = hook_m.group(1)
        if body_m:
            body = body_m.group(1)
        if cta_m:
            cta = cta_m.group(1)

        if not body and full_m:
            body = full_m.group(1)

        # 策略2: 正则也失败时，回退到行扫描
        if not hook and not body:
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if "钩子" in line or "开头" in line:
                    hook = line.split("：")[-1].split('"')[-1].strip()
                elif "结尾" in line or "CTA" in line:
                    cta = line.split("：")[-1].split('"')[-1].strip()
                elif line and len(line) > 10 and not line.startswith('"') and not line.startswith('{') and not line.startswith('}'):
                    body += line + " "

        return {
            "hook": hook or "学会这个技能，你也可以做到！",
            "body": body.strip() or "这是一个非常实用的技巧",
            "cta": cta or "喜欢的话点个赞！",
            "full_script": f"{hook} {body} {cta}".strip(),
            "storyboard": storyboard,
            "chart_data": [],
            "diagram_layout": "",
        }

    def generate_platform_content(self, script_result: Dict, platform: str) -> Dict:
        """为指定平台生成适配的内容"""
        platform_configs = {
            "抖音": {
                "title_style": "悬念型",
                "desc_style": "引导互动型",
                "hashtag_style": "热门挑战型",
            },
            "小红书": {
                "title_style": "种草分享型",
                "desc_style": "经验分享型",
                "hashtag_style": "生活方式型",
            },
            "视频号": {
                "title_style": "新闻资讯型",
                "desc_style": "朋友圈风格",
                "hashtag_style": "正能量型",
            },
        }

        config = platform_configs.get(platform, platform_configs["抖音"])

        prompt = f"""基于以下短视频脚本，为{platform}平台生成标题和描述:

【脚本内容】
{script_result.get('full_script', '')}

【选题】
{script_result.get('topic_title', '')}

【平台特点】
- 平台: {platform}
- 标题风格: {config['title_style']}
- 描述风格: {config['desc_style']}

请生成:
1. 吸引人的标题(30字以内)
2. 引导互动的描述(200字以内)
3. 10个相关话题标签

输出JSON格式:
{{
  "platform_title": "标题",
  "platform_desc": "描述",
  "platform_hashtags": ["#标签1", "#标签2", ...]
}}

直接输出JSON:"""

        response = self._call_ollama(prompt, timeout=60)

        try:
            json_str = self._extract_json_from_text(response)
            if json_str:
                return json.loads(json_str)
        except Exception:
            pass

        # 降级返回
        return {
            "platform_title": f"必看！{script_result.get('topic_title', '')}",
            "platform_desc": f"{script_result.get('hook', '')}\n\n{script_result.get('body', '')}",
            "platform_hashtags": [f"#{tag.strip()}" for tag in script_result.get('suggested_tags', [])[:10]],
        }

    def save_script_to_db(self, script_data: Dict) -> int:
        """保存脚本到数据库"""
        from core.db_init import init_topics_db

        conn = init_topics_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scripts (topic_id, platform, script_content, storyboard, title, description, hashtags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            script_data.get("topic_id"),
            script_data.get("platform"),
            script_data.get("full_script", ""),
            json.dumps(script_data.get("storyboard", []), ensure_ascii=False),
            script_data.get("title", ""),
            script_data.get("description", ""),
            json.dumps(script_data.get("hashtags", []), ensure_ascii=False),
        ))

        script_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return script_id

    def batch_generate(self, topics: List[Dict], platform: str = "抖音",
                      duration: int = 30) -> List[Dict]:
        """批量生成脚本"""
        results = []

        for i, topic in enumerate(topics):
            print(f"  [{i+1}/{len(topics)}] 正在生成: {topic.get('title', '')[:30]}...")
            try:
                result = self.generate_script(topic, platform, duration)
                results.append(result)
                time.sleep(0.5)  # 避免请求过快
            except Exception as e:
                print(f"  生成失败: {str(e)}")
                continue

        return results


# ==================== 便捷函数 ====================
_module_instance = None

def get_script_module() -> ScriptModule:
    """获取脚本模块单例"""
    global _module_instance
    if _module_instance is None:
        _module_instance = ScriptModule()
    return _module_instance

def generate_script(topic: Dict, platform: str = "抖音",
                    duration: int = 30, stream_callback=None) -> Dict:
    """快速生成脚本"""
    return get_script_module().generate_script(topic, platform, duration, stream_callback=stream_callback)
