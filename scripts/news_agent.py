#!/usr/bin/env python3
"""
智能新闻抓取报告生成智能体
功能：根据用户输入的主题，自动搜索→抓取→整理→生成报告
特点：跨平台移植、无需API密钥、基于scrapling
"""

import asyncio
import os
import re
import sys
import time
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from html.parser import HTMLParser
import urllib.parse

# ============== 配置 ==============
SCRAPLING_PATH = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\Scripts\scrapling.exe"

# ============== 数据结构 ==============
@dataclass
class Article:
    title: str
    url: str
    content: str
    source: str
    pub_date: str = ""
    summary: str = ""

@dataclass
class NewsReport:
    title: str
    topic: str
    date_range: str
    sources: list = field(default_factory=list)
    articles: list = field(default_factory=list)
    summary: str = ""

# ============== 搜索源配置 ==============
SEARCH_SOURCES = {
    # 英文搜索
    "bing": {
        "search_url": "https://www.bing.com/search?q={query}&qdr=m&count=10",
        "use_stealthy": True
    },
    "google": {
        "search_url": "https://www.google.com/search?q={query}&tbs=qdr:m&num=10",
        "use_stealthy": True
    },
    # 国内搜索
    "baidu": {
        "search_url": "https://www.baidu.com/s?wd={query}&rn=10&tn=news",
        "use_stealthy": False
    },
    "sogou": {
        "search_url": "https://www.sogou.com/web?query={query}&ie=utf8&num=10",
        "use_stealthy": False
    },
    "360": {
        "search_url": "https://www.so.com/s?q={query}&pn=1&rn=10",
        "use_stealthy": False
    },
    "zhihu": {
        "search_url": "https://www.zhihu.com/search?type=content&q={query}",
        "use_stealthy": False
    },
    "36kr": {
        "search_url": "https://www.36kr.com/search/articles/{query}",
        "use_stealthy": False
    },
    "sina": {
        "search_url": "https://search.sina.com.cn/?q={query}&c=news&from=&ie=utf-8&num=10",
        "use_stealthy": False
    },
    "ifeng": {
        "search_url": "https://search.ifeng.com/sofeng/search.aspx?q={query}&qtype=0&page=1&num=10",
        "use_stealthy": False
    },
    "people": {
        "search_url": "http://search.people.com.cn/cnpeople/collect/all.do?keyword={query}&page=1",
        "use_stealthy": False
    },
    "xinhua": {
        "search_url": "http://www.xinhuanet.com/search/search.jsp?keyword={query}&page=1&channel=1",
        "use_stealthy": False
    }
}

# 行业垂直搜索源
INDUSTRY_SOURCES = {
    "能源电力": [
        "https://www.nea.gov.cn/xwzx/nyyw.htm",
        "https://www.cec.org.cn/",
        "http://www.cpnn.com.cn/",
    ],
    "科技": [
        "https://36kr.com/",
        "https://www.ifeng.com/",
        "https://tech.sina.com.cn/",
    ],
    "财经": [
        "https://finance.sina.com.cn/",
        "https://www.yicai.com/",
        "https://www.jiemian.com/",
    ],
    "政府政策": [
        "https://www.gov.cn/",
        "https://www.ndrc.gov.cn/",
        "https://www.miit.gov.cn/",
    ]
}

# ============== 工具函数 ==============

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.skip_tags = {'script', 'style', 'nav', 'footer', 'header', 'aside'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.texts.append(text)

    def get_text(self, separator='\n'):
        return separator.join(self.texts)


def html_to_text(html: str) -> str:
    parser = HTMLTextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except:
        return html


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


def extract_urls(text: str) -> list:
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return list(set(re.findall(url_pattern, text)))


# ============== 核心抓取类 ==============

class NewsCrawlerAgent:
    def __init__(
        self,
        topic: str,
        cache_dir: str = "news_cache",
        max_concurrent: int = 5,
        max_articles: int = 20,
        timeout: int = 30000,
        search_source: str = "auto",
        industry: str = None
    ):
        self.topic = topic
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_concurrent = max_concurrent
        self.max_articles = max_articles
        self.timeout = timeout
        self.selected_source = search_source
        self.industry = industry

        self.articles = []
        self.errors = []
        self.search_results = []
        self.search_source = self._auto_select_source()

    def _auto_select_source(self) -> str:
        """自动选择搜索源"""
        if self.selected_source != "auto":
            return self.selected_source

        # 默认使用百度（国内友好）
        return "baidu"

    def _get_cache_path(self, url: str) -> Path:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def _is_cache_valid(self, url: str, max_age_hours: int = 24) -> bool:
        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=max_age_hours)

    def _load_cache(self, url: str) -> Optional[Article]:
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                return Article(**data)
            except:
                return None
        return None

    def _save_cache(self, article: Article) -> None:
        cache_path = self._get_cache_path(article.url)
        cache_path.write_text(json.dumps({
            "title": article.title,
            "url": article.url,
            "content": article.content,
            "source": article.source,
            "pub_date": article.pub_date,
            "summary": article.summary
        }, ensure_ascii=False), encoding="utf-8")

    async def search(self) -> list:
        print(f"\n[S] Searching: {self.topic}")

        urls = []

        # 如果指定了行业，先从行业垂直源获取
        if self.industry and self.industry in INDUSTRY_SOURCES:
            print(f"    [Industry] {self.industry}")
            industry_urls = await self._search_industry_sources(self.industry)
            urls.extend(industry_urls)

        # 从常规搜索源搜索
        sources_to_use = []
        if self.selected_source == "all":
            # 使用所有搜索源
            for src in SEARCH_SOURCES:
                if src not in ["google"]:  # 跳过可能不可用的
                    sources_to_use.append(src)
        else:
            sources_to_use = [self.search_source]

        for src in sources_to_use:
            if src not in SEARCH_SOURCES:
                continue
            source_config = SEARCH_SOURCES[src]
            query = urllib.parse.quote_plus(self.topic)
            search_url = source_config["search_url"].format(query=query)

            print(f"    Source: {src}")
            print(f"    URL: {search_url[:60]}...")

            try:
                cmd = f'"{SCRAPLING_PATH}" extract stealthy-fetch "{search_url}" search_result_{src}.html --timeout {self.timeout}'

                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()

                result_file = Path(f"search_result_{src}.html")
                if result_file.exists():
                    content = result_file.read_text(encoding="utf-8")
                    found_urls = extract_urls(content)

                    # 过滤掉搜索引擎自身链接
                    found_urls = [u for u in found_urls if
                                   src not in u and
                                   'baidu.com' not in u and
                                   'sogou.com' not in u and
                                   '360.cn' not in u and
                                   'so.com' not in u and
                                   'zhihu.com' not in u]
                    urls.extend(found_urls)
                    result_file.unlink()

                    print(f"    Found {len(found_urls)} links from {src}")

            except Exception as e:
                print(f"    Search error ({src}): {e}")

        # 去重
        urls = list(set(urls))
        urls = [u for u in urls if u.startswith('http')]
        urls = urls[:self.max_articles]

        print(f"    Total unique URLs: {len(urls)}")

        self.search_results = urls
        return urls

    async def _search_industry_sources(self, industry: str) -> list:
        """搜索行业垂直源"""
        urls = []
        if industry not in INDUSTRY_SOURCES:
            return urls

        print(f"    [Vertical] {industry} sources...")

        for url in INDUSTRY_SOURCES[industry]:
            try:
                cmd = f'"{SCRAPLING_PATH}" extract stealthy-fetch "{url}" industry_temp.html --timeout {self.timeout}'

                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()

                temp_file = Path("industry_temp.html")
                if temp_file.exists():
                    content = temp_file.read_text(encoding="utf-8")
                    found = extract_urls(content)
                    # 过滤只保留同源链接
                    source_domain = re.search(r'https?://([^/]+)', url)
                    if source_domain:
                        domain = source_domain.group(1)
                        filtered = [u for u in found if domain in u]
                        urls.extend(filtered)
                    temp_file.unlink()

            except Exception as e:
                print(f"    Industry source error: {e}")

        return urls

    async def fetch_article(self, url: str) -> Optional[Article]:
        if self._is_cache_valid(url):
            cached = self._load_cache(url)
            if cached:
                print(f"    [CACHE] {cached.title[:30]}...")
                return cached

        try:
            cmd = f'"{SCRAPLING_PATH}" extract stealthy-fetch "{url}" article_temp.html --timeout {self.timeout} --ai-targeted'

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            temp_file = Path("article_temp.html")
            if temp_file.exists():
                html_content = temp_file.read_text(encoding="utf-8")

                title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
                title = title_match.group(1) if title_match else url

                date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', html_content)
                pub_date = date_match.group(1) if date_match else ""

                content = self._extract_content(html_content)
                content = clean_text(content)
                summary = content[:200] + "..." if len(content) > 200 else content

                source_match = re.search(r'https?://([^/]+)', url)
                source = source_match.group(1) if source_match else "unknown"

                article = Article(
                    title=title,
                    url=url,
                    content=content,
                    source=source,
                    pub_date=pub_date,
                    summary=summary
                )

                self._save_cache(article)
                temp_file.unlink()

                print(f"    [OK] {title[:40]}...")
                return article

        except Exception as e:
            self.errors.append((url, str(e)))
            print(f"    [ERR] {url[:40]}... - {str(e)[:30]}")

        return None

    def _extract_content(self, html: str) -> str:
        noise_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<nav[^>]*>.*?</nav>',
            r'<footer[^>]*>.*?</footer>',
            r'<header[^>]*>.*?</header>',
            r'<!--.*?-->',
        ]

        for pattern in noise_patterns:
            html = re.sub(pattern, '', html, flags=re.DOTALL)

        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
        if body_match:
            html = body_match.group(1)

        text = html_to_text(html)
        text = clean_text(text)

        if len(text) > 5000:
            lines = text.split('\n')
            start = max(0, len(lines) // 2 - 50)
            end = min(len(lines), start + 200)
            text = '\n'.join(lines[start:end])

        return text

    async def fetch_all(self, urls: list) -> list:
        if not urls:
            return []

        print(f"\n[F] Fetching {len(urls)} articles...")

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_one(url: str) -> Optional[Article]:
            async with semaphore:
                return await self.fetch_article(url)

        tasks = [fetch_one(url) for url in urls]

        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await coro
                if result:
                    results.append(result)
                print(f"    Progress: {i+1}/{len(tasks)} (OK: {len(results)})")
            except Exception as e:
                print(f"    Error: {e}")

        self.articles = results
        return results

    def generate_report(self, output_file: str = None) -> str:
        if not self.articles:
            print("\n[W] No articles to generate report")
            return ""

        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sources_map = {}
        for article in self.articles:
            source = article.source
            if source not in sources_map:
                sources_map[source] = []
            sources_map[source].append(article)

        safe_topic = re.sub(r'[^\w\s-]', '', self.topic)[:20]
        if not output_file:
            output_file = f"report_{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        report = f"""# {self.topic} Related Report

## Report Info

- Topic: {self.topic}
- Generated: {today}
- Articles: {len(self.articles)}
- Sources: {', '.join(sources_map.keys())}

---

## Summary

This report contains {len(self.articles)} articles related to "{self.topic}" from {len(sources_map)} sources.

"""

        for source, articles in sources_map.items():
            report += f"""### From: {source}

"""
            for i, article in enumerate(articles, 1):
                report += f"""**{i}. {article.title}**

- Date: {article.pub_date or 'Unknown'}
- URL: {article.url}
- Summary: {article.summary}

"""

        report += f"""---

## Full Content

"""
        for i, article in enumerate(self.articles, 1):
            content = article.content[:1500] + "..." if len(article.content) > 1500 else article.content
            report += f"""### {i}. {article.title}

Source: {article.source} | Date: {article.pub_date or 'Unknown'}

{content}

---

"""

        report += f"""
## Statistics

| Metric | Value |
|--------|-------|
| Total Articles | {len(self.articles)} |
| Total Sources | {len(sources_map)} |
| Fetch Errors | {len(self.errors)} |
| Generated | {today} |

"""

        if self.errors:
            report += """## Errors

| URL | Error |
|-----|-------|
"""
            for url, error in self.errors:
                short_url = url[:60] + "..." if len(url) > 60 else url
                report += f"| {short_url} | {error} |\n"

        report += """
---
Generated by NewsCrawlerAgent (Scrapling-based)
"""

        Path(output_file).write_text(report, encoding="utf-8")
        print(f"\n[DONE] Report saved: {output_file}")

        return report

    async def run(self) -> str:
        print("=" * 60)
        print("News Crawler Agent")
        print("=" * 60)
        print(f"\nTopic: {self.topic}")
        print(f"Cache: {self.cache_dir}")
        print(f"Concurrent: {self.max_concurrent}")

        start_time = time.time()

        urls = await self.search()
        await self.fetch_all(urls)
        report = self.generate_report()

        elapsed = time.time() - start_time

        print("\n" + "=" * 60)
        print("COMPLETE!")
        print(f"Time: {elapsed:.1f}s")
        print(f"Success: {len(self.articles)}")
        print(f"Failed: {len(self.errors)}")
        print("=" * 60)

        return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python news_agent.py <search_topic> [options]")
        print("")
        print("Options:")
        print("  --cache=<dir>       Cache directory (default: news_cache)")
        print("  --concurrent=<n>   Concurrent requests (default: 5)")
        print("  --max=<n>         Max articles to fetch (default: 20)")
        print("  --source=<name>    Search source: auto/baidu/sogou/360/zhihu/36kr/sina/ifeng/people/xinhua/bing/google/all")
        print("  --industry=<name>  Industry vertical: 能源电力/科技/财经/政府政策")
        print("")
        print("Examples:")
        print('  python news_agent.py "电力行业政策"')
        print('  python news_agent.py "新能源汽车" --source=baidu --max=20')
        print('  python news_agent.py "AI技术" --source=zhihu')
        print('  python news_agent.py "能源政策" --industry=能源电力')
        print('  python news_agent.py "科技新闻" --source=all --industry=科技')
        print("")
        print("Available search sources:")
        for src in SEARCH_SOURCES:
            print(f"    - {src}")
        print("")
        print("Available industry verticals:")
        for ind in INDUSTRY_SOURCES:
            print(f"    - {ind}")
        sys.exit(1)

    topic = sys.argv[1]

    cache_dir = "news_cache"
    max_concurrent = 5
    max_articles = 20
    search_source = "auto"
    industry = None

    for arg in sys.argv[2:]:
        if arg.startswith("--cache="):
            cache_dir = arg.split("=")[1]
        elif arg.startswith("--concurrent="):
            max_concurrent = int(arg.split("=")[1])
        elif arg.startswith("--max="):
            max_articles = int(arg.split("=")[1])
        elif arg.startswith("--source="):
            search_source = arg.split("=")[1]
        elif arg.startswith("--industry="):
            industry = arg.split("=")[1]

    agent = NewsCrawlerAgent(
        topic=topic,
        cache_dir=cache_dir,
        max_concurrent=max_concurrent,
        max_articles=max_articles,
        search_source=search_source,
        industry=industry
    )

    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
