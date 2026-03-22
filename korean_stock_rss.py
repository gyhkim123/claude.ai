"""
한국경제 증권 RSS 파서
한국경제신문(hankyung.com) 증권 섹션 RSS 피드를 파싱합니다.
표준 라이브러리만 사용 (외부 패키지 불필요).
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional


RSS_URL = "https://www.hankyung.com/feed/finance"


@dataclass
class StockNewsItem:
    title: str
    link: str
    published: str
    summary: str
    author: Optional[str] = None


def fetch_rss(url: str) -> ET.Element:
    """URL에서 RSS XML을 가져와 파싱합니다."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        xml_data = response.read()
    return ET.fromstring(xml_data)


def format_date(date_str: str) -> str:
    """RFC 2822 날짜 문자열을 'YYYY-MM-DD HH:MM:SS' 형식으로 변환합니다."""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return date_str


def parse_items(root: ET.Element) -> list[StockNewsItem]:
    """RSS XML 루트에서 뉴스 항목을 추출합니다."""
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS 채널을 찾을 수 없습니다.")

    items = []
    for item in channel.findall("item"):
        def text(tag: str) -> str:
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        # <dc:creator> 지원
        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        author_el = item.find("dc:creator", ns)
        author = (author_el.text or "").strip() if author_el is not None else None

        published_raw = text("pubDate")
        published = format_date(published_raw) if published_raw else ""

        # <description> 태그에서 HTML 태그 제거
        description = text("description")
        import re
        description = re.sub(r"<[^>]+>", "", description).strip()

        items.append(
            StockNewsItem(
                title=text("title"),
                link=text("link"),
                published=published,
                summary=description,
                author=author or None,
            )
        )

    return items


def display_news(items: list[StockNewsItem], limit: int = 10) -> None:
    """뉴스 항목을 콘솔에 출력합니다."""
    print(f"{'=' * 62}")
    print(f"  한국경제 증권 뉴스  (총 {len(items)}건, 최근 {limit}건 표시)")
    print(f"{'=' * 62}\n")

    for i, item in enumerate(items[:limit], start=1):
        print(f"[{i}] {item.title}")
        print(f"    시간 : {item.published}")
        if item.author:
            print(f"    기자 : {item.author}")
        print(f"    URL  : {item.link}")
        if item.summary:
            snippet = item.summary[:120] + "..." if len(item.summary) > 120 else item.summary
            print(f"    요약 : {snippet}")
        print()


def save_to_json(items: list[StockNewsItem], filename: str = "stock_news.json") -> None:
    """뉴스 항목을 JSON 파일로 저장합니다."""
    data = {
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": RSS_URL,
        "total": len(items),
        "items": [asdict(item) for item in items],
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON 저장 완료 → {filename}")


def main():
    print(f"RSS 피드 수신 중: {RSS_URL}\n")
    try:
        root = fetch_rss(RSS_URL)
        items = parse_items(root)
        display_news(items)
        save_to_json(items)
    except urllib.error.URLError as e:
        print(f"네트워크 오류: {e}")
    except ValueError as e:
        print(f"파싱 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()
