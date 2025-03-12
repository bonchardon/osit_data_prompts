from json import dump

from httpx import AsyncClient
from bs4 import BeautifulSoup

from loguru import logger

from core.bihus_info import consts


class BihusData:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def fetch_article_content(self, article_url: str) -> str | None:
        """Fetch content for a specific article."""
        if not (response := await self.client.get(article_url)):
            response.raise_for_status()
            return
        return response.text

    @staticmethod
    async def extract_title(soup: BeautifulSoup) -> str | None:
        if not (title_tag := soup.find('h1', class_='bi-single__title')):
            logger.error('Having issues when parsing titles.')
            return
        return title_tag.get_text(strip=True) if title_tag else 'No Title'

    @staticmethod
    async def extract_author(soup: BeautifulSoup) -> str | None:
        if not (author_tag := soup.find('a', class_='c-post-author__name')):
            logger.error('Having issues when extracting an author.')
            return
        return author_tag.get_text(strip=True) if author_tag else 'Unknown Author'

    @staticmethod
    async def extract_date(soup: BeautifulSoup) -> str | None:
        if not (date_tag := soup.find('time', class_='bi-intro-post__time bi-single__meta-item')):
            logger.error('Cannot parse date.')
            return
        return date_tag.get_text(strip=True) if date_tag else 'Unknown Date'

    @staticmethod
    async def extract_text(soup: BeautifulSoup) -> str | None:
        if not (content_div := soup.find('div', class_='bi-single-content')):
            logger.error('Cannot parse text.')
            return
        paragraphs = content_div.find_all(['h4', 'p'])
        return ' '.join([p.get_text(strip=True) for p in paragraphs[:5]]) if paragraphs else 'No Text'

    async def extract_article_data(self, article_url: str) -> dict[str, str] | None:
        """Extract the article data for a given URL."""
        response = await self.fetch_article_content(article_url)
        if not response:
            logger.warning(f"Error fetching article {article_url}")
            return

        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        article_data = {
            'date': await self.extract_date(soup=soup),
            'link': article_url,
            'title': await self.extract_title(soup=soup),
            'author': 'Not given',
            'short_text': await self.extract_text(soup=soup)
        }
        logger.info(article_data)
        return article_data

    async def sort_data(self):
        """Fetch and process articles, then save the results."""
        all_articles_data: list[dict[str, str]] = []
        for link in consts.LINKS:
            article_data = await self.extract_article_data(link)
            if article_data:
                all_articles_data.append(article_data)
        logger.info(f'Collected data for {len(all_articles_data)} articles.')

        try:
            with open(consts.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                dump(all_articles_data, f, ensure_ascii=False, indent=4)
            logger.info(f'Data saved to {consts.OUTPUT_FILE}')
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")

        return all_articles_data
