# -*- coding: utf-8 -*-
"""
RAG 知识增强引擎 — 选题研究 → 搜索 → 切块 → 向量化 → 检索 → Prompt注入
纯 Python + SQLite，零新依赖。使用 Ollama 本地 Embedding 模型。
覆盖面试模块：RAG全链路 / 检索基础设施 / 查询改写 / 混合检索
"""
import json
import math
import os
import re
import sqlite3
import time
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import config


class _TextExtractor(HTMLParser):
    """从HTML中提取纯文本。"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'footer', 'header', 'code', 'noscript'}

    def handle_data(self, data):
        self.text.append(data.strip())


def _extract_text_from_html(html: str) -> str:
    ext = _TextExtractor()
    try:
        ext.feed(html)
    except Exception:
        pass
    return ' '.join(t for t in ext.text if len(t) > 2)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RAGEngine:
    """RAG检索引擎 — 选题研究 → 多源搜索 → 文本切块 → Embedding → 向量存储 → 语义检索。

    典型用法:
        rag = RAGEngine()
        docs = rag.research_topic("武汉科技大学", "高校教育")
        context = rag.format_context(docs)
        # 注入到 LLM prompt 的【背景资料】section
    """

    def __init__(
        self,
        db_path: str = None,
        ollama_url: str = None,
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 480,
        chunk_overlap: int = 120,
    ):
        self.db_path = db_path or str(config.DATA_DIR / "rag_index.db")
        self.ollama_url = (ollama_url or config.OLLAMA_BASE_URL).rstrip('/')
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._init_db()

    # ═══════════════════════════════════════════════════════════════
    # 数据库
    # ═══════════════════════════════════════════════════════════════

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_query TEXT NOT NULL,
                source_url TEXT,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER,
                embedding BLOB,
                created_at REAL DEFAULT (julianday('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_topic ON rag_documents(topic_query)
        """)
        conn.commit()
        conn.close()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    # ═══════════════════════════════════════════════════════════════
    # Web搜索
    # ═══════════════════════════════════════════════════════════════

    def search_web(self, query: str, num_results: int = 5) -> List[dict]:
        """多源web搜索。返回 [{title, url, snippet}]。"""
        results = []

        # 1. Serper.dev (Google Search) — 免费额度50次/月
        serper_key = os.environ.get('SERPER_API_KEY', '')
        if serper_key:
            results = self._search_serper(query, num_results, serper_key)
            if results:
                return results

        # 2. Bing Search API
        bing_key = os.environ.get('BING_API_KEY', '')
        if bing_key:
            results = self._search_bing(query, num_results, bing_key)
            if results:
                return results

        # 3. DuckDuckGo HTML (no API key needed)
        results = self._search_duckduckgo(query, num_results)
        return results

    def _search_serper(self, query: str, num: int, api_key: str) -> List[dict]:
        try:
            data = json.dumps({"q": query, "num": num, "gl": "cn", "hl": "zh-CN"}).encode()
            req = urllib.request.Request(
                "https://google.serper.dev/search",
                data=data,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read().decode())
            results = []
            for item in resp.get("organic", [])[:num]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return results
        except Exception:
            return []

    def _search_bing(self, query: str, num: int, api_key: str) -> List[dict]:
        try:
            req = urllib.request.Request(
                f"https://api.bing.microsoft.com/v7.0/search?q={urllib.parse.quote(query)}"
                f"&count={num}&mkt=zh-CN",
                headers={"Ocp-Apim-Subscription-Key": api_key}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read().decode())
            results = []
            for item in resp.get("webPages", {}).get("value", [])[:num]:
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                })
            return results
        except Exception:
            return []

    def _search_duckduckgo(self, query: str, num: int) -> List[dict]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode('utf-8', errors='replace')
            # 解析结果
            results = []
            # DuckDuckGo HTML返回的链接格式: <a rel="nofollow" class="result__a" href="...">
            link_pattern = re.compile(
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                re.DOTALL
            )
            snippet_pattern = re.compile(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                re.DOTALL
            )
            links = link_pattern.findall(html)
            snippets = snippet_pattern.findall(html)
            for i in range(min(num, len(links))):
                url_str = links[i][0] if links[i][0].startswith('http') else ''
                title = re.sub(r'<[^>]+>', '', links[i][1]).strip()
                snippet = _extract_text_from_html(snippets[i]) if i < len(snippets) else ''
                if title:
                    results.append({"title": title, "url": url_str, "snippet": snippet})
            return results
        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════════
    # 网页内容抓取
    # ═══════════════════════════════════════════════════════════════

    def fetch_page_text(self, url: str, max_chars: int = 8000) -> str:
        """抓取网页正文（仅用于搜索结果的扩充阅读）。"""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                content_type = r.headers.get('Content-Type', '')
                raw = r.read()
                # 尝试解码
                for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
                    try:
                        html = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    html = raw.decode('utf-8', errors='replace')
            text = _extract_text_from_html(html)
            return text[:max_chars]
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════════════════
    # 文本切块
    # ═══════════════════════════════════════════════════════════════

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """中文感知的文本切块：优先按段落边界，超过chunk_size时按字符滑动窗口。"""
        cs = chunk_size or self.chunk_size
        ol = overlap or self.chunk_overlap
        if not text or len(text) < 20:
            return []

        # 先尝试按段落切
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if len(p.strip()) > 10]
        chunks = []
        for para in paragraphs:
            if len(para) <= cs:
                if para:
                    chunks.append(para)
            else:
                # 长段落按句子切
                sentences = re.split(r'[。！？；\n]', para)
                current = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current) + len(sent) + 1 <= cs:
                        current = (current + "。" + sent) if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
                if current:
                    chunks.append(current)

        # 去重、去太短的
        result = []
        for c in chunks:
            c = c.strip()
            if len(c) >= 20 and c not in result:
                result.append(c)
        return result

    # ═══════════════════════════════════════════════════════════════
    # Ollama Embedding
    # ═══════════════════════════════════════════════════════════════

    def embed(self, texts: List[str]) -> List[List[float]]:
        """通过Ollama获取embedding向量。自动拉取模型(首次)。"""
        embeddings = []
        for text in texts:
            try:
                payload = json.dumps({
                    "model": self.embedding_model,
                    "prompt": text[:2000],  # 截断过长文本
                }).encode()
                req = urllib.request.Request(
                    f"{self.ollama_url}/api/embeddings",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    resp = json.loads(r.read().decode())
                embeddings.append(resp.get("embedding", []))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # 模型未拉取，尝试拉取
                    self._pull_embedding_model()
                    return self.embed(texts)  # 重试
                embeddings.append([])
            except Exception:
                embeddings.append([])
        return embeddings

    def _pull_embedding_model(self):
        """拉取embedding模型(异步fire-and-forget)。"""
        try:
            payload = json.dumps({"name": self.embedding_model}).encode()
            req = urllib.request.Request(
                f"{self.ollama_url}/api/pull",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=120)
            time.sleep(2)  # 等模型就绪
        except Exception:
            pass

    def _ensure_model_available(self) -> bool:
        """检查embedding模型是否已拉取。"""
        try:
            with urllib.request.urlopen(f"{self.ollama_url}/api/tags", timeout=5) as r:
                models = json.loads(r.read().decode()).get("models", [])
            for m in models:
                if self.embedding_model in m.get("name", ""):
                    return True
            return False
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # 向量索引
    # ═══════════════════════════════════════════════════════════════

    def build_index(self, topic_query: str, chunks: List[str],
                    embeddings: List[List[float]], source_urls: List[str] = None) -> int:
        """将chunks和embeddings存入SQLite向量索引。返回存储的文档数。"""
        conn = self._conn()
        count = 0
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            if not emb:
                continue
            url = source_urls[i] if source_urls and i < len(source_urls) else ""
            conn.execute(
                "INSERT INTO rag_documents (topic_query, source_url, chunk_text, chunk_index, embedding) "
                "VALUES (?, ?, ?, ?, ?)",
                (topic_query, url, chunk, i, json.dumps(emb))
            )
            count += 1
        conn.commit()
        conn.close()
        return count

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义检索 — 返回top_k最相关的chunks。"""
        # 先获取query的embedding
        query_embs = self.embed([query])
        if not query_embs or not query_embs[0]:
            return []
        query_vec = query_embs[0]

        # 从DB加载候选chunks（同topic或全部）
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, chunk_text, source_url, embedding FROM rag_documents ORDER BY id DESC LIMIT 500"
        ).fetchall()
        conn.close()

        # 余弦相似度排序
        scored = []
        for row in rows:
            try:
                emb = json.loads(row[3])
                score = _cosine_similarity(query_vec, emb)
                scored.append((score, row[1], row[2]))
            except Exception:
                continue

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"score": round(s, 4), "text": t, "source": u}
            for s, t, u in scored[:top_k]
        ]

    # ═══════════════════════════════════════════════════════════════
    # 端到端研究流程
    # ═══════════════════════════════════════════════════════════════

    def research_topic(self, topic_title: str, category: str = "",
                       num_results: int = 5) -> List[Dict]:
        """端到端选题研究：搜索 → 抓取正文 → 切块 → 向量化 → 索引 → 检索。

        返回: [{score, text, source}]  — 按相关性排序的top知识片段。
        """
        # 1. 构建搜索查询
        search_query = topic_title
        if category:
            search_query = f"{category} {topic_title}"

        # 2. Web搜索
        search_results = self.search_web(search_query, num_results)
        if not search_results:
            return []

        # 3. 收集所有文本：snippet + 网页正文
        all_text = ""
        source_urls = []
        for sr in search_results:
            snippet = sr.get("snippet", "")
            if snippet:
                all_text += snippet + "\n\n"
                source_urls.append(sr.get("url", ""))
            # 尝试抓取正文（选一个最相关的）
            if len(source_urls) <= 2 and sr.get("url"):
                body = self.fetch_page_text(sr["url"], 4000)
                if body:
                    all_text += body + "\n\n"
                    source_urls.append(sr["url"] + "#body")

        if not all_text.strip():
            return []

        # 4. 切块
        chunks = self.chunk_text(all_text)
        if not chunks:
            return []

        # 5. 向量化
        embeddings = self.embed(chunks)
        if not embeddings or not any(embeddings):
            return []

        # 6. 存入索引
        self.build_index(topic_title, chunks, embeddings, source_urls)

        # 7. 检索最相关的片段
        return self.retrieve(topic_title, top_k=5)

    def format_context(self, docs: List[Dict], max_tokens_estimate: int = 800) -> str:
        """将检索到的文档格式化为可注入Prompt的文本块。"""
        if not docs:
            return ""
        lines = []
        char_count = 0
        for d in docs:
            text = d.get("text", "")
            source = d.get("source", "")
            # 粗略估计tokens：中文约2字/token
            est_tokens = len(text) // 2
            if char_count + est_tokens > max_tokens_estimate:
                break
            line = f"· {text}"
            if source:
                line += f" [来源: {source}]"
            lines.append(line)
            char_count += est_tokens
        if not lines:
            return ""
        return "【背景资料】以下是从互联网检索到的相关事实，请在创作脚本时参考使用：\n" + "\n".join(lines)

    def augment_prompt(self, topic: Dict, base_prompt: str) -> str:
        """在已有prompt中注入RAG检索到的背景资料。

        topic: 选题dict (含 title, category 字段)
        base_prompt: _build_script_prompt 返回的原始prompt
        返回: 增强后的prompt
        """
        title = topic.get("title", "")
        category = topic.get("category", "")
        if not title:
            return base_prompt

        docs = self.research_topic(title, category)
        context = self.format_context(docs)
        if not context:
            return base_prompt

        # 在【要求】之前插入背景资料
        augmented = base_prompt.replace("【硬性要求】", context + "\n\n【硬性要求】")
        if augmented == base_prompt:
            augmented = base_prompt.replace("【选题】", context + "\n\n【选题】")
        return augmented


# ═══════════════════════════════════════════════════════════════
# 单例
# ═══════════════════════════════════════════════════════════════

_rag_instance = None


def get_rag_engine() -> RAGEngine:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance
