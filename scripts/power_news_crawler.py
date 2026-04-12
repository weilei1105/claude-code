#!/usr/bin/env python3
"""
电力行业新闻并发抓取脚本
支持：并行抓取、断点续抓、边抓边写、进度显示
"""

import asyncio
import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# 添加scrapling路径
sys.path.insert(0, r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\Lib\site-packages")

from scrapling.fetchers import FetcherSession, StealthySession


class PowerNewsCrawler:
    def __init__(
        self,
        cache_dir: str = "news_cache",
        output_file: str = "电力行业政策动态报告.md",
        max_concurrent: int = 5,
        timeout: int = 30000,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.output_file = output_file
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.results = []
        self.errors = []
        self.fetched_count = 0
        self.skipped_count = 0

        # 新闻来源配置
        self.sources = {
            "国家能源局首页": {
                "url": "https://www.nea.gov.cn/",
                "selector": "a[href*='/xwzx/'], a[href*='/policy/']",
                "use_stealthy": True,
            },
            "能源要闻": {
                "url": "https://www.nea.gov.cn/xwzx/nyyw.htm",
                "selector": "a[href*='.html']",
                "use_stealthy": True,
            },
            "政策通知": {
                "url": "https://www.nea.gov.cn/policy/tz.htm",
                "selector": "a[href*='.html']",
                "use_stealthy": True,
            },
            "新闻发布": {
                "url": "https://www.nea.gov.cn/xwzx/index.htm",
                "selector": "a[href*='.html']",
                "use_stealthy": True,
            },
        }

        # 具体文章URL（一个月内的重要新闻）
        self.article_urls = [
            # 4月份新闻
            ("2026年能源监管例会", "https://www.nea.gov.cn/20260408/de79c1606947448cb4fca23f83f4f471/c.html", "stealthy"),
            ("全球海拔最高槽式光热电站开工", "https://www.nea.gov.cn/20260410/0846a0b0290e4026a614c8afea5c0fae/c.html", "stealthy"),
            ("水深最深海上风电并网", "https://www.nea.gov.cn/20260410/6a7a68a611744276a7773980ee975897/c.html", "stealthy"),
            ("新型储能规模超3.7亿千瓦", "https://www.nea.gov.cn/20260410/fe421f319b644ac8aaad55422907bf6a/c.html", "stealthy"),
            ("全景式碳排放核算系统发布", "https://www.nea.gov.cn/20260410/d5a2ddf7e0df4d628be6cdb7c514eb31/c.html", "stealthy"),
            ("会见联合国气候特使", "https://www.nea.gov.cn/20260410/f53da24dc1eb4587b2fedb33ea5c51cf/c.html", "stealthy"),
            # 3月份新闻
            ("2026年水电站安全工作会议", "https://www.nea.gov.cn/20260328/a79a3d004b1445c58c658843cae9ca3b/c.html", "stealthy"),
            ("全国水电站安全工作会议", "https://www.nea.gov.cn/20260328/a79a3d004b1445c58c658843cae9ca3b/c.html", "stealthy"),
            ("APEC能源工作组会议", "https://www.nea.gov.cn/20260319/5ff8ca4eb23f4c9c9e62349a46cf8c10/c.html", "stealthy"),
            ("能源行业标准立项指南", "https://www.nea.gov.cn/20260324/a3810b8d733c4972a67ef5891a17b8ea/c.html", "stealthy"),
            ("电力市场交易增长25.5%", "https://www.nea.gov.cn/20260327/74f32da0f435467498a4ac106e3607ca/c.html", "stealthy"),
            ("抽蓄投资310亿元", "https://www.nea.gov.cn/20260327/a3d77c7487cc4f51ab37de2a8f80d491/c.html", "stealthy"),
            ("新型储能平台投用", "https://www.nea.gov.cn/20260327/1855d41b37874c86972081c7548af181/c.html", "stealthy"),
            ("李强总理四川调研", "https://www.nea.gov.cn/20260403/a09f0b3e529e4ccda30a81d4bde0b460/c.html", "stealthy"),
            ("抽水蓄能投产高峰", "https://www.nea.gov.cn/20260403/30865dc8fd3d4f33a83e3c7202ddfbd9/c.html", "stealthy"),
            ("电力重大事故隐患判定标准", "https://www.nea.gov.cn/20260409/f20a03a64bea4a4791c1db72cbdccd28/c.html", "stealthy"),
            ("会见新加坡贸工部副常秘", "https://www.nea.gov.cn/20260319/619a2f4bff89401998e68179ddbe8e26/c.html", "stealthy"),
            ("IRENA合作公告", "https://www.nea.gov.cn/20260331/9009ea617d3e4154828582274cd8c635/c.html", "stealthy"),
            ("新型电力系统试点", "https://www.nea.gov.cn/20260226/1f4744c9c2b44eb493f82a17f4603290/c.html", "stealthy"),
            ("电力业务资质管理会议", "https://www.nea.gov.cn/20260403/b91a092f4aee4034b0d5cd54be3380ca/c.html", "stealthy"),
            ("可再生能源调度会", "https://www.nea.gov.cn/20260408/8a4f53eb155346eb962d19392ab27894/c.html", "stealthy"),
            ("电动汽车充电设施数据", "https://www.nea.gov.cn/20260321/aa361196749245dd8c6abd15a01f59e3/c.html", "stealthy"),
            ("能源行业标准立项", "https://www.nea.gov.cn/20260324/a3810b8d733c4972a67ef5891a17b8ea/c.html", "stealthy"),
            ("电力市场统计数据", "https://www.nea.gov.cn/20260325/a1515f414588445bbc6cc8c65ba6293e/c.html", "stealthy"),
            ("六郎洞水电站注销", "https://www.nea.gov.cn/20260327/2a148a9117a9471a8a15a2474ad08ca8/c.html", "stealthy"),
            ("防汛抗旱通知", "https://www.nea.gov.cn/20260312/dd031108771444f39f2e8f5a06006cba/c.html", "stealthy"),
            ("煤矿智能化升级试点", "https://www.nea.gov.cn/20260209/ea5b9bede4764590bff3c62244f6f57c/c.html", "stealthy"),
            ("首台套技术装备申报", "https://www.nea.gov.cn/20260209/852658bf1dab460bacbedb630493bc9c/c.html", "stealthy"),
            ("电力安全标准化委员会成立", "https://www.nea.gov.cn/20260127/7b8226e44d1a41e2915a8d36ef800491/c.html", "stealthy"),
            ("生物液体燃料标委会调整", "https://www.nea.gov.cn/20260225/978be2b6fe0c46ee95b6e54caecda389/c.html", "stealthy"),
        ]

    def get_cache_path(self, url: str) -> Path:
        """获取URL对应的缓存文件路径"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.html"

    def is_cache_valid(self, url: str, max_age_hours: int = 6) -> bool:
        """检查缓存是否有效"""
        cache_path = self.get_cache_path(url)
        if not cache_path.exists():
            return False
        # 检查修改时间
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=max_age_hours)

    def save_to_cache(self, url: str, content: str) -> None:
        """保存到缓存"""
        cache_path = self.get_cache_path(url)
        cache_path.write_text(content, encoding="utf-8")

    def load_from_cache(self, url: str) -> Optional[str]:
        """从缓存加载"""
        cache_path = self.get_cache_path(url)
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
        return None

    async def fetch_url(
        self,
        session: FetcherSession,
        url: str,
        title: str,
        use_stealthy: bool = False,
    ) -> tuple[bool, str, str]:
        """抓取单个URL"""
        # 检查缓存
        if self.is_cache_valid(url):
            self.skipped_count += 1
            cached = self.load_from_cache(url)
            return True, title, cached or ""

        try:
            if use_stealthy:
                page = await asyncio.to_thread(
                    lambda: StealthySession().fetch(url)
                )
            else:
                page = await asyncio.to_thread(
                    lambda: FetcherSession().get(url, stealthy_headers=True)
                )

            # 提取正文内容
            content = page.css("body").css("::text").getall()
            text = "\n".join([t.strip() for t in content if t.strip()])

            # 提取标题
            title_text = page.css("h1", "h2", "title").css("::text").get()
            if title_text:
                title = title_text.strip()

            # 提取日期
            date_elem = page.css('[class*="time"]', '[class*="date"]', 'time').css("::text").get()
            if date_elem:
                pub_date = date_elem.strip()
            else:
                pub_date = "未知日期"

            # 保存缓存
            full_content = f"## {title}\n\n发布日期: {pub_date}\n\n{text}"
            self.save_to_cache(url, full_content)

            self.fetched_count += 1
            return True, title, full_content

        except Exception as e:
            self.errors.append((title, url, str(e)))
            return False, title, ""

    async def fetch_all_concurrent(self) -> list[tuple[str, str]]:
        """并发抓取所有文章"""
        print(f"\n开始并发抓取，共 {len(self.article_urls)} 篇文章")
        print(f"并发数: {self.max_concurrent}, 缓存有效期: 6小时\n")

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(title: str, url: str, use_stealthy: bool):
            async with semaphore:
                # 使用同步方式在线程中运行（scrapling fetcher是同步的）
                def do_fetch():
                    if use_stealthy == "stealthy":
                        from scrapling.fetchers import StealthyFetcher
                        page = StealthyFetcher.fetch(url)
                    else:
                        page = FetcherSession().get(url, stealthy_headers=True)
                    return page

                page = await asyncio.to_thread(do_fetch)

                # 提取正文
                content = page.css("body").getall()
                text = "".join(content)

                # 提取标题
                title_elem = page.css("h1", "h2").css("::text").get()
                actual_title = title_elem.strip() if title_elem else title

                # 提取日期
                date_elem = page.css('[class*="time"]', 'time').css("::text").get()
                pub_date = date_elem.strip() if date_elem else "未知日期"

                # 保存缓存
                full_content = f"## {actual_title}\n\n发布日期: {pub_date}\n\n{text}"
                self.save_to_cache(url, full_content)

                self.fetched_count += 1
                print(f"  [已抓取] {actual_title}")

                return actual_title, full_content

        tasks = [
            fetch_with_semaphore(title, url, use_stealthy)
            for title, url, use_stealthy in self.article_urls
        ]

        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await coro
                results.append(result)
                print(f"进度: {i+1}/{len(tasks)}")
            except Exception as e:
                print(f"  [错误] {str(e)}")
                self.errors.append(("未知", "", str(e)))

        return results

    def generate_report(self, results: list[tuple[str, str]]) -> None:
        """生成Markdown报告"""
        print(f"\n正在生成报告: {self.output_file}")

        today = datetime.now().strftime("%Y年%m月%d日")
        report = f"""# 电力行业政策动态报告

**报告周期**：{today}
**数据来源**：国家能源局等官方渠道
**抓取数量**：{len(results)} 篇
**抓取时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 一、本月要闻

"""

        # 按时间排序（最近的在前）
        results.sort(key=lambda x: x[0], reverse=True)

        for title, content in results:
            if content:
                report += f"{content}\n\n---\n\n"

        # 错误统计
        if self.errors:
            report += f"""## 抓取异常

| 文章 | URL | 错误 |
|------|-----|------|
"""
            for title, url, error in self.errors:
                short_url = url[:50] + "..." if len(url) > 50 else url
                report += f"| {title} | {short_url} | {error} |\n"

        # 统计信息
        report += f"""
## 统计信息

- 成功抓取: {self.fetched_count} 篇
- 缓存命中: {self.skipped_count} 篇
- 抓取失败: {len(self.errors)} 篇
- 总计处理: {self.fetched_count + self.skipped_count} 篇

---

*报告由PowerNewsCrawler自动生成*
"""

        # 写入文件
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"报告已生成: {self.output_file}")
        print(f"文件大小: {os.path.getsize(self.output_file) / 1024:.1f} KB")

    def run(self) -> None:
        """运行抓取"""
        start_time = time.time()

        print("=" * 60)
        print("电力行业新闻并发抓取工具")
        print("=" * 60)

        # 清理旧缓存（可选）
        if "--clear-cache" in sys.argv:
            print("\n清理缓存...")
            for f in self.cache_dir.glob("*.html"):
                f.unlink()
            print("缓存已清理")

        # 并发抓取
        results = asyncio.run(self.fetch_all_concurrent())

        # 生成报告
        self.generate_report(results)

        # 打印统计
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("抓取完成!")
        print(f"总耗时: {elapsed:.1f} 秒")
        print(f"成功: {self.fetched_count} 篇")
        print(f"缓存: {self.skipped_count} 篇")
        print(f"失败: {len(self.errors)} 篇")
        print("=" * 60)


if __name__ == "__main__":
    # 可以通过参数调整
    crawler = PowerNewsCrawler(
        cache_dir="power_news_cache",      # 缓存目录
        output_file="电力行业政策动态报告_并发版.md",  # 输出文件
        max_concurrent=8,                 # 并发数（根据网络调整，建议5-10）
        timeout=30000,                   # 超时毫秒
    )
    crawler.run()
