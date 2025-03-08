import json
from typing import Any

from httpx import AsyncClient
from bs4 import BeautifulSoup, ResultSet, NavigableString

from loguru import logger

from core.prot_corruption_shabunin import consts


class AntacNewsData:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def fetch_links(self, url: str) -> list[str] | None:
        if not (response := await self.client.get(url)):
            response.raise_for_status()
            return
        return response.text

    async def get_first_page_links(self, url: str) -> list[str] | None:
        if not (response := await self.fetch_links(url)):
            logger.error('Cannot parse a link.')
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        article_links: list[str] = []
        article_items: ResultSet = soup.find_all('article')
        for article in article_items:
            link_tag: Any = article.find('a', href=True)
            if link_tag:
                article_links.append(link_tag['href'])
        return article_links

    @staticmethod
    async def get_last_page_number(soup: BeautifulSoup) -> int:
        pagination: BeautifulSoup | NavigableString | None = soup.find('div', class_='pagination')
        if pagination:
            last_page_link = pagination.find_all('a', class_='page-numbers')[-2]
            last_page_url = last_page_link.get('href')
            try:
                last_page_number = int(last_page_url.split('/')[-2])
                logger.info(f'Last page number: {last_page_number}')
                return last_page_number
            except (IndexError, ValueError) as e:
                logger.error(f'Error parsing last page number from URL: {last_page_url}, error: {e}')
                return 1
        else:
            logger.warning("Pagination structure not found or malformed.")
            return 1

    async def get_all_links(self) -> list[list[str]] | None:
        if not (response := await self.fetch_links(consts.URL)):
            logger.warning("Error retrieving the first page.")
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        last_page_number: int = await self.get_last_page_number(soup)
        return [
            await self.get_first_page_links(consts.URL_PAGINATION.format(page_num=page_num))
            for page_num in range(1, last_page_number + 1)
        ]

    @staticmethod
    async def extract_title(soup: BeautifulSoup) -> str | None:
        if not (title_tag := soup.find('h1', class_='heading-section__title')):
            return
        return title_tag.get_text(strip=True) if title_tag else 'No Title'

    @staticmethod
    async def extract_date(soup: BeautifulSoup) -> str | None:
        date_tag: BeautifulSoup = soup.find('time', class_='single-post-heading__date')
        if date_tag:
            return date_tag.get_text(strip=True) if date_tag else 'No Date'

    @staticmethod
    async def extract_text(soup: BeautifulSoup) -> str | None:
        paragraphs = soup.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text(strip=True) for p in paragraphs[:3]]) if paragraphs else 'No Text'

    @staticmethod
    async def extract_author(soup: BeautifulSoup) -> str | None:
        author_tag: BeautifulSoup = soup.find('span', class_='author')
        if author_tag:
            return author_tag.get_text(strip=True) if author_tag else 'No Author'

    async def extract_article_data(self, article_url: list[str]) -> dict | None:
        if not (response := await self.fetch_links(article_url)):
            logger.warning(f'Error fetching article {article_url}')
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        return {
            'date': await self.extract_date(soup=soup),
            'link': article_url,
            'title': await self.extract_title(soup=soup),
            'author': await self.extract_author(soup=soup),
            'short_text': await self.extract_text(soup=soup)
        }

    @staticmethod
    async def save_to_json(data: list) -> None:
        try:
            with open(consts.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f'Data successfully saved to {consts.SAVE_FILE}')
        except Exception as e:
            logger.error(f'Error saving data to JSON file: {e}')

    async def sort_data(self):
        all_links: list[list[str]] = await self.get_all_links()
        all_articles_data: list[dict[str, str]] = []
        for link in all_links:
            article_data = await self.extract_article_data(link)
            if article_data:
                all_articles_data.append(article_data)
        logger.info(f'Collected data for {len(all_articles_data)} articles.')
        await self.save_to_json(all_articles_data)
        return all_articles_data
