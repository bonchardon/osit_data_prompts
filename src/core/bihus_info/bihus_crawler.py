from json import dump
from asyncio import sleep

from bs4 import BeautifulSoup
from helium import start_chrome, find_all, click, Text, wait_until, kill_browser

from loguru import logger

from core.bihus_info import consts


class BihusNewsData:
    def __init__(self):
        self.browser = None

    async def start_browser_session(self) -> None:
        self.browser = start_chrome()

    async def close_browser_session(self) -> None:
        if self.browser:
            kill_browser()

    async def fetch_page(self, url: str) -> str:
        self.browser.get(url)
        await sleep(3)
        return self.browser.page_source

    @staticmethod
    async def get_article_links_from_page(html: str) -> list[str] | None:
        soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
        if not (article_items := soup.find_all('article')):
            return
        return [
            article.find('a', href=True)['href']
            for article in article_items
            if article.find('a', href=True)
        ]

    async def load_more_articles(self) -> set[str]:
        all_links = set()
        has_more: bool = True
        while has_more:
            response: str = await self.fetch_page(url=consts.URL)
            page_links: list[str] | None = await self.get_article_links_from_page(response)
            for link in page_links:
                all_links.add(link)
            try:
                load_more_button = find_all(Text('Більше новин')).last

                if load_more_button:
                    click(load_more_button)
                    wait_until(lambda: load_more_button.is_displayed(), timeout_secs=5)  # Wait for the page to load
                    logger.info('Clicked \'Load More\' button.')
                else:
                    logger.info("No more articles to load.")
                    has_more = False
            except Exception as e:
                logger.warning(f'Failed to find \'Load More\' button: {e}')
                has_more = False
            await sleep(3)
        logger.info(f'Total unique links collected: {len(all_links)}')
        return all_links

    @staticmethod
    async def extract_title(soup: BeautifulSoup) -> str | None:
        if not (title_tag := soup.find('h1', class_='bi-single__title')):
            return
        return title_tag.get_text(strip=True) if title_tag else 'No Title'

    @staticmethod
    async def extract_date(soup: BeautifulSoup) -> str | None:
        if not (date_tag := soup.find('time', class_='bi-intro-post__time bi-single__meta-item')):
            return
        return date_tag.get_text(strip=True) if date_tag else 'No Date'

    @staticmethod
    async def extract_text(soup: BeautifulSoup) -> str | None:
        if not (paragraphs := soup.find_all('p')):
            return
        return ' '.join([p.get_text(strip=True) for p in paragraphs[:3]]) if paragraphs else 'No Text'

    @staticmethod
    async def extract_author(soup: BeautifulSoup) -> str | None:
        if not (author_tag := soup.find('span', class_='author')):
            return
        return author_tag.get_text(strip=True) if author_tag else 'No Author'

    async def extract_article_data(self, article_url: str) -> dict[str, str] | None:
        if not (response := await self.fetch_page(article_url)):
            logger.warning(f'Error fetching article {article_url}')
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        article_data = {
            'date': await self.extract_date(soup=soup),
            'link': article_url,
            'title': await self.extract_title(soup=soup),
            'author': await self.extract_author(soup=soup),
            'short_text': await self.extract_text(soup=soup)
        }
        return article_data

    @staticmethod
    async def save_to_json(data: list) -> None:
        try:
            with open(consts.FILE_SAVED, 'w', encoding='utf-8') as f:
                dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data successfully saved to {consts.FILE_SAVED}")
        except Exception as e:
            logger.error(f"Error saving data to JSON file: {e}")

    async def sort_data(self) -> list[dict[str, str]]:
        await self.start_browser_session()
        all_links: set[str] = await self.load_more_articles()
        all_articles_data: list[dict[str, str]] = []
        for link in all_links:
            article_data = await self.extract_article_data(link)
            if article_data:
                all_articles_data.append(article_data)

        logger.info(f'Collected data for {len(all_articles_data)} articles.')

        await self.save_to_json(all_articles_data)
        await self.close_browser_session()

        return all_articles_data
