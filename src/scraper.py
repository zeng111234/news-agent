"""网页抓取服务 - 抓取央视网国际新闻"""
import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.config import config


class NewsArticle:
    """新闻文章数据模型"""
    def __init__(
        self,
        title: str,
        url: str,
        summary: str = "",
        content: str = "",
        publish_time: Optional[str] = None,
        source: str = "央视网",
        category: str = "国际",
    ):
        self.title = title.strip()
        self.url = url.strip()
        self.summary = summary.strip()
        self.content = content.strip()
        self.publish_time = publish_time or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.source = source
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "content": self.content,
            "publish_time": self.publish_time,
            "source": self.source,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsArticle":
        return cls(**data)


class Scraper:
    """网页抓取器，支持多种网站类型"""

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )

    def fetch_page(self, url: str) -> Optional[str]:
        """获取页面 HTML 内容"""
        try:
            response = self.client.get(url)
            response.encoding = "utf-8"
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  [错误] 抓取失败: {url} - {e}")
            return None

    def scrape_cctv_news(self, url: str) -> List[NewsArticle]:
        """抓取央视网新闻列表"""
        print(f"  [抓取] 正在抓取: {url}")
        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        # 尝试多种可能的选择器来匹配央视网的结构
        # 方法1: 查找所有链接中的新闻标题
        news_items = []

        # 查找常见的新闻列表结构
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # 过滤出有意义的新闻链接
            if len(text) < 10:
                continue

            # 忽略导航/页脚等非新闻链接
            if any(skip in text for skip in ["首页", "登录", "注册", "关于", "联系", "央视"]):
                continue

            # 完整 URL
            full_url = href
            if href.startswith("/"):
                full_url = "https://news.cctv.com" + href
            elif href.startswith("//"):
                full_url = "https:" + href
            elif not href.startswith("http"):
                full_url = "https://news.cctv.com/" + href

            news_items.append({"title": text, "url": full_url})

        # 去重（按标题）
        seen_titles = set()
        unique_items = []
        for item in news_items:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                unique_items.append(item)

        # 取前 30 条
        for item in unique_items[:30]:
            summary = self._extract_summary_from_page(item["url"])
            article = NewsArticle(
                title=item["title"],
                url=item["url"],
                summary=summary,
                source="央视网",
                category="国际",
            )
            articles.append(article)

        print(f"  [完成] 共抓取到 {len(articles)} 篇新闻")
        return articles

    def _extract_summary_from_page(self, url: str) -> str:
        """从文章详情页提取摘要/导语"""
        html = self.fetch_page(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")

        # 尝试提取摘要：常见的摘要/导语选择器
        summary_selectors = [
            "meta[name='description']",
            ".brief",
            ".summary",
            ".lead",
            ".article-description",
            ".content_desc",
            "p.short",
        ]

        for selector in summary_selectors:
            if selector.startswith("meta"):
                meta = soup.find("meta", attrs={"name": "description"})
                if meta and meta.get("content"):
                    return meta["content"].strip()
            else:
                el = soup.select_one(selector)
                if el:
                    return el.get_text(strip=True)

        # 取正文第一段作为摘要
        content_div = soup.select_one(
            ".content_area, .article-content, .cnt_bd, .text_area, article"
        )
        if content_div:
            first_p = content_div.find("p")
            if first_p:
                text = first_p.get_text(strip=True)
                if len(text) > 20:
                    return text[:200]

        return ""

    def scrape_source(self, name: str, source_config: dict) -> List[NewsArticle]:
        """根据配置抓取指定源"""
        source_type = source_config.get("type", "general")
        url = source_config.get("url", "")

        if not url:
            print(f"  [跳过] {name}: 未配置 URL")
            return []

        if source_type == "cctv":
            return self.scrape_cctv_news(url)
        else:
            # 通用抓取（解析页面中所有链接）
            return self.scrape_general(url, name)

    def scrape_general(self, url: str, source_name: str) -> List[NewsArticle]:
        """通用网页抓取"""
        print(f"  [抓取] 正在抓取: {url}")
        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link.get("href", "")

            if len(text) < 10:
                continue

            full_url = href
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif href.startswith("//"):
                full_url = "https:" + href
            elif not href.startswith("http"):
                from urllib.parse import urljoin
                full_url = urljoin(url, href)

            articles.append(NewsArticle(
                title=text,
                url=full_url,
                source=source_name,
            ))

        # 去重
        seen = set()
        unique = []
        for a in articles:
            if a.title not in seen:
                seen.add(a.title)
                unique.append(a)

        print(f"  [完成] 共抓取到 {len(unique)} 篇文章")
        return unique[:20]

    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()


def scrape_all_sources() -> List[NewsArticle]:
    """抓取所有启用的源"""
    scraper = Scraper()
    all_articles = []

    try:
        sources = config.get_enabled_sources()
        if not sources:
            print("[警告] 没有配置任何启用的抓取源")
            return []

        print(f"\n{'='*50}")
        print(f"开始抓取 {len(sources)} 个新闻源...")
        print(f"{'='*50}")

        for name, source_config in sources.items():
            print(f"\n--- {name} ---")
            articles = scraper.scrape_source(name, source_config)
            all_articles.extend(articles)

        print(f"\n{'='*50}")
        print(f"抓取完成！共获取 {len(all_articles)} 篇新闻")
        print(f"{'='*50}")

    finally:
        scraper.close()

    return all_articles