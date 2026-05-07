"""AI 处理模块 - 调用 DeepSeek API 进行内容筛选与摘要生成"""
import json
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.config import config
from src.scraper import NewsArticle


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self):
        self.api_key = config.deepseek_api_key
        self.api_base = config.deepseek_api_base
        self.model = config.deepseek_model
        self.client = httpx.Client(timeout=60.0)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> Optional[str]:
        """调用 DeepSeek Chat API"""
        if not self.api_key or self.api_key == "your_deepseek_api_key_here":
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        try:
            response = self.client.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [错误] DeepSeek API 调用失败: {e}")
            return None

    def close(self):
        self.client.close()


class AINewsProcessor:
    """AI 新闻处理器 - 筛选和摘要生成"""

    def __init__(self):
        self.client = DeepSeekClient()

    def filter_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """使用 AI 筛选新闻：按质量去重、排序"""
        if not self.client.api_key or self.client.api_key == "your_deepseek_api_key_here":
            print("  [跳过] 未配置 DeepSeek API Key，跳过 AI 筛选")
            return self._basic_filter(articles)

        articles_text = []
        for i, article in enumerate(articles):
            articles_text.append(f"[{i+1}] 标题: {article.title}\n   摘要: {article.summary}")

        prompt = f"""你是一个专业的新闻编辑。请从以下新闻列表中筛选出最有价值的新闻，要求：

1. 去除重复或高度相似的新闻
2. 去除低质量、标题党的新闻
3. 保留有深度、有信息量的新闻
4. 按重要性从高到低排序
5. 最多保留 {config.max_articles} 条

请直接返回 JSON 格式的序号列表，例如：["1", "3", "5", ...]

新闻列表：
{chr(10).join(articles_text)}"""

        messages = [
            {"role": "system", "content": "你是专业的新闻编辑，擅长筛选高质量新闻。请严格按照要求的格式输出 JSON。"},
            {"role": "user", "content": prompt},
        ]

        result = self.client.chat(messages)
        if result:
            try:
                # 尝试解析 JSON
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[1].rsplit("\n", 1)[0]
                indices = json.loads(result)
                selected = []
                for idx_str in indices:
                    try:
                        idx = int(idx_str) - 1
                        if 0 <= idx < len(articles):
                            selected.append(articles[idx])
                    except ValueError:
                        continue
                if selected:
                    print(f"  [AI筛选] AI 从 {len(articles)} 篇中精选了 {len(selected)} 篇")
                    return selected
            except (json.JSONDecodeError, Exception) as e:
                print(f"  [警告] AI 筛选结果解析失败: {e}，使用基础筛选")

        return self._basic_filter(articles)

    def _basic_filter(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """基础筛选：关键词过滤 + 去重"""
        exclude_keywords = config.get_exclude_keywords()
        priority_keywords = config.get_priority_keywords()

        # 去重
        seen_titles = set()
        unique = []
        for article in articles:
            if article.title not in seen_titles:
                seen_titles.add(article.title)
                unique.append(article)

        # 过滤排除关键词
        filtered = []
        for article in unique:
            if any(kw in article.title for kw in exclude_keywords):
                continue
            filtered.append(article)

        # 按优先级排序
        def priority_score(article: NewsArticle) -> int:
            score = 0
            for i, kw in enumerate(priority_keywords):
                if kw in article.title:
                    score += len(priority_keywords) - i
            return score

        filtered.sort(key=priority_score, reverse=True)

        # 限制数量
        max_count = config.max_articles
        result = filtered[:max_count]

        print(f"  [基础筛选] 从 {len(articles)} 篇中筛选了 {len(result)} 篇")
        return result

    def generate_summaries(self, articles: List[NewsArticle]) -> str:
        """使用 AI 生成简报摘要"""
        if not self.client.api_key or self.client.api_key == "your_deepseek_api_key_here":
            print("  [跳过] 未配置 DeepSeek API Key，使用原文摘要")
            return self._basic_summary(articles)

        articles_text = []
        for i, article in enumerate(articles):
            articles_text.append(
                f"[{i+1}] {article.title}\n"
                f"    链接: {article.url}\n"
                f"    来源: {article.source}\n"
                f"    摘要: {article.summary or '暂无摘要'}"
            )

        today = datetime.now().strftime("%Y年%m月%d日")

        prompt = f"""你是一个专业的新闻简报编辑。请为以下 {len(articles)} 篇新闻生成一份简明扼要的每日简报。

简报要求：
1. 先写一段简短的开场概述（2-3句话）
2. 每篇新闻用 1-2 句话概括核心要点
3. 语言简洁、客观、专业
4. 按重要性排序
5. 格式：使用 Markdown，每篇新闻前加上序号和标题

日期：{today}

新闻素材：
{chr(10).join(articles_text)}"""

        messages = [
            {"role": "system", "content": "你是专业的新闻简报编辑，擅长提炼要点，输出高质量的中文新闻摘要。"},
            {"role": "user", "content": prompt},
        ]

        result = self.client.chat(messages, temperature=0.5)
        if result:
            print(f"  [AI摘要] AI 生成了 {len(articles)} 篇新闻的摘要简报")
            return result

        return self._basic_summary(articles)

    def _basic_summary(self, articles: List[NewsArticle]) -> str:
        """基础摘要：拼接原文标题和摘要"""
        today = datetime.now().strftime("%Y年%m月%d日")
        lines = [f"# ? 每日国际新闻简报 - {today}", ""]

        for i, article in enumerate(articles, 1):
            lines.append(f"## {i}. {article.title}")
            lines.append(f"? 来源: {article.source}")
            if article.summary:
                lines.append(f"? {article.summary}")
            if config.include_source_link:
                lines.append(f"? [阅读原文]({article.url})")
            lines.append("")

        return "\n".join(lines)

    def process_articles(self, articles: List[NewsArticle]) -> str:
        """完整处理流程：筛选 → 摘要生成"""
        print(f"\n{'='*50}")
        print(f"开始 AI 处理...")
        print(f"{'='*50}")

        # 1. 筛选
        print("\n--- 筛选阶段 ---")
        filtered = self.filter_articles(articles)
        if not filtered:
            print("[警告] 筛选后没有文章，将使用所有文章")
            filtered = articles[:config.max_articles]

        # 2. 生成摘要
        print("\n--- 摘要生成阶段 ---")
        briefing = self.generate_summaries(filtered)

        print(f"\n{'='*50}")
        print(f"AI 处理完成！简报共 {len(filtered)} 篇新闻")
        print(f"{'='*50}")

        return briefing

    def close(self):
        self.client.close()