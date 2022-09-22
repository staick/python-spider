import re
import json
import logging
import requests
import multiprocessing
from typing import List
from os import makedirs
from os.path import exists


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)

BASE_URL = "https://book.douban.com/tag"


def scrape_page(url: str):
    """获取给定URL的HTML代码

    :param url: 待爬取网页的URL
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }
    logging.info("scraping %s...", url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logging.error(
                "get invalid status code %s while scraping %s",
                response.status_code,
                url,
            )
    except requests.RequestException:
        logging.error("error occurred while scraping %s", url, exc_info=True)


def scrape_index(page=1):
    """获取主页的HTML代码"""
    tag = "编程"  # TODO
    index_url = f"{BASE_URL}/{tag}?start={(page - 1)*20}&type=T"
    return scrape_page(index_url)


def parse_index(html) -> List:
    """解析HTML代码获取详情页URL

    :param html: 待解析的HTML代码
    :returns: 详情页的URL
    """
    pattern = re.compile('<h2.*?class.*?href="(.*?)"', re.S)
    items = re.findall(pattern, html)
    if not items:
        return []
    for item in items:
        detail_url = item
        logging.info("get detail url %s", detail_url)
        yield detail_url


def get_page_num(html) -> int:
    """获取网页的页数

    :param html: 待解析的HTML代码
    :returns: 网页的页数
    """
    pattern = re.compile('<a.*?>(.*?)</a>\s*<span.*?class="next">')
    page_num = (
        re.search(pattern, html).group(1).strip() if re.search(pattern, html) else None
    )
    page_num = int(page_num)
    return page_num


def scrape_detail(url: str):
    """爬取书籍详情页"""
    return scrape_page(url)


def parse_detail(html):
    """解析书籍详情页"""
    # 匹配规则
    title_pattern = re.compile("<h1>\s*<span.*?>(.*?)</span>")
    sub_title_pattern = re.compile("<span.*?副标题:</span>(.*?)<br/>", re.S)
    cover_pattern = re.compile('<a\s*class="nbg"\s*href="(.*?)".*?>', re.S)
    author_pattern = re.compile("<span.*?> 作者</span>.*?<a.*?>(.*?)</a>", re.S)
    publisher_pattern = re.compile("<span.*?出版社.*?<a.*?>(.*?)</a>.*?</span>", re.S)
    publisher_year_pattern = re.compile("<span.*?出版年.*?</span>(.*?)<br/>", re.S)
    pages_pattern = re.compile("<span.*?页数.*?</span>(.*?)<br/>", re.S)
    isbn_pattern = re.compile("<span.*?>ISBN:</span>(.*?)<br/>", re.S)
    price_pattern = re.compile("<span.*?定价.*?</span>(.*?)<br/>", re.S)
    drama_pattern = re.compile('<div\s*class="intro">.*?<p>(.*?)</p></div>', re.S)
    score_pattern = re.compile("<strong.*?rating_num.*?>(.*?)</strong>")

    # 匹配
    title = (
        re.search(title_pattern, html).group(1).strip()
        if re.search(title_pattern, html)
        else None
    )
    sub_title = (
        re.search(sub_title_pattern, html).group(1).strip()
        if re.search(sub_title_pattern, html)
        else None
    )
    cover = (
        re.search(cover_pattern, html).group(1).strip()
        if re.search(cover_pattern, html)
        else None
    )
    author = (
        re.search(author_pattern, html).group(1).strip()
        if re.search(author_pattern, html)
        else None
    )
    publisher = (
        re.search(publisher_pattern, html).group(1).strip()
        if re.search(publisher_pattern, html)
        else None
    )
    publisher_year = (
        re.search(publisher_year_pattern, html).group(1).strip()
        if re.search(publisher_year_pattern, html)
        else None
    )
    pages = (
        re.search(pages_pattern, html).group(1).strip()
        if re.search(pages_pattern, html)
        else None
    )
    isbn = (
        re.search(isbn_pattern, html).group(1).strip()
        if re.search(isbn_pattern, html)
        else None
    )
    price = (
        re.search(price_pattern, html).group(1).strip()
        if re.search(price_pattern, html)
        else None
    )
    drama = (
        re.search(drama_pattern, html).group(1).strip()
        if re.findall(drama_pattern, html)
        else None
    )
    score = (
        re.search(score_pattern, html).group(1).strip()
        if re.search(score_pattern, html)
        else None
    )
    if sub_title:
        title = f"{title}:{sub_title}"

    return {
        "title": title,
        "cover": cover,
        "author": author,
        "publisher": publisher,
        "publisher_year": publisher_year,
        "pages": pages,
        "isbn": isbn,
        "price": price,
        "drama": drama,
        "score": score,
    }


# 保存数据
RESULTS_DIR = "Algorithm"
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)


def save_data(data):
    """保存数据到对应的文件"""
    name = data.get('title')
    data_path = f"{RESULTS_DIR}/{name}.json"
    json.dump(
        data, open(data_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2
    )


def main(page):
    index_html = scrape_index(page)
    detail_urls = parse_index(index_html)
    for detail_url in detail_urls:
        detail_html = scrape_detail(detail_url)
        data = parse_detail(detail_html)
        logging.info('get detail data %s', data)
        logging.info('saving data to json data')
        save_data(data)
        logging.info('data saved successfully')


if __name__ == "__main__":
    html = scrape_index()
    total_page = get_page_num(html)
    pool = multiprocessing.Pool()
    pages = range(1, total_page + 1)
    pool.map(main, pages)
    pool.close()
    pool.join()
