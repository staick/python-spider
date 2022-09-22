# 爬取https://ssr1.scrape.center的
import requests
import logging
import re
import json
import multiprocessing
from urllib.parse import urljoin
from typing import Dict
from os import makedirs
from os.path import exists


# 定义日志的输出级别和格式
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)

BASE_URL = "https://ssr1.scrape.center"
TOTAL_PAGE = 10


def scrape_page(url: str):
    """爬取指定网页的内容

    :param url: 要爬取网页的URL
    :returns: 指定网页的HTML代码
    """
    # 开始爬取，记录日志
    logging.info("scraping %s...", url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        logging.error(
            "get invalid status code %s while scraping %s", response.status_code, url
        )
    except requests.RequestException:
        logging.error("error occurred while scraping %s", url, exc_info=True)


def scrape_index(page: int):
    """爬取指定列表页的内容

    :param page: 要爬取的列表页的页数
    :returns: 列表页的HTML代码
    """
    index_url = f"{BASE_URL}/page/{page}"
    return scrape_page(index_url)


def parse_index(html) -> str:
    """解析列表页

    :param html: 要解析的列表页HTML代码
    :returns: 详情页的URL
    """
    pattern = re.compile('<a.*?href="(.*?)".*?class="name">')
    items = re.findall(pattern, html)
    if not items:
        return []
    for item in items:
        detail_url = urljoin(BASE_URL, item)
        logging.info("get detail url %s", detail_url)
        yield detail_url


def scrape_detail(url):
    """爬取详情页
    :param url: 详情页的URL
    :returns: 详情页的HTML代码
    """
    return scrape_page(url)


def parse_detail(html) -> Dict:
    """解析详情页

    :param html: 要解析的详情页HTML代码
    :returns: 解析的的结果
    """
    # 匹配规则
    cover_pattern = re.compile(
        'class="item.*?<img.*?src="(.*?)".*?class="cover">', re.S
    )
    name_pattern = re.compile("<h2.*?>(.*?)</h2>", re.S)
    categories_pattern = re.compile(
        "<button.*?category.*?<span>(.*?)</span>.*?</button>", re.S
    )
    published_at_pattern = re.compile("(\d{4}-\d{2}-\d{2})\s?上映")
    drama_pattern = re.compile("<div.*?drama.*?>.*?<p.*?>(.*?)</p>", re.S)
    score_pattern = re.compile("<p.*?score.*?>(.*?)</p>", re.S)

    # 匹配封面
    cover = (
        re.search(cover_pattern, html).group(1).strip()
        if re.search(cover_pattern, html)
        else None
    )
    # 匹配名字
    name = (
        re.search(name_pattern, html).group(1).strip()
        if re.search(cover_pattern, html)
        else None
    )
    # 匹配类别
    categories = (
        re.findall(categories_pattern, html)
        if re.findall(categories_pattern, html)
        else []
    )
    # 匹配发行时间
    published_at = (
        re.search(published_at_pattern, html).group(1)
        if re.search(published_at_pattern, html)
        else None
    )
    # 匹配简介
    drama = (
        re.search(drama_pattern, html).group(1).strip()
        if re.search(drama_pattern, html)
        else None
    )
    # 匹配分数
    score = (
        re.search(score_pattern, html).group(1).strip()
        if re.search(score_pattern, html)
        else None
    )

    return {
        "cover": cover,
        "name": name,
        "categories": categories,
        "published_at": published_at,
        "drama": drama,
        "score": score,
    }


# 保存数据
RESULTS_DIR = "results"
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)


def save_data(data: Dict):
    """保存数据

    :param data: 要保存的数据
    """
    name = data.get('name')
    data_path = f'{RESULTS_DIR}/{name}.json'
    json.dump(data, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def main(page):
    index_html = scrape_index(page)
    detail_urls = parse_index(index_html)
    for detail_url in detail_urls:
        detail_html = scrape_detail(detail_url)
        data = parse_detail(detail_html)
        logging.info('get detail data %s', data)
        logging.info('saving data to json file')
        save_data(data)
        logging.info('data saved successfully')


if __name__ == "__main__":
    # 多进程加速
    pool = multiprocessing.Pool()
    pages = range(1, TOTAL_PAGE + 1)
    pool.map(main, pages)
    pool.close()
    pool.join()
