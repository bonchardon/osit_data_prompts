from json import dump
from httpx import AsyncClient
from bs4 import BeautifulSoup, ResultSet

from loguru import logger

from core.shemy_radio_svoboda import consts


class RadioSvobodaData:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def fetch_links(self, url: str) -> str | None:
        if not (response := await self.client.get(url)):
            response.raise_for_status()
            return
        return response.text

    async def extract_all_article_links(self, url: str) -> list[str] | None:
        if not (response := await self.fetch_links(url)):
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        article_links: list[str] = []
        for link in soup.find_all(
                name='a',
                class_='img-wrap img-wrap--t-spac img-wrap--size-3 img-wrap--float img-wrap--xs'
        ):
            href = link.get('href')
            if href:
                article_links.append(consts.PAGANATION_URL.format(href=href))
        return article_links

    @staticmethod
    async def extract_title(soup: BeautifulSoup) -> str:
        title_tag: BeautifulSoup = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)

    @staticmethod
    async def extract_date(soup: BeautifulSoup) -> str:
        date_tag: BeautifulSoup = soup.find('div', class_='published')
        if date_tag:
            time_tag: BeautifulSoup = date_tag.find('time')
            if time_tag:
                date: str = time_tag.get_text(strip=True)
                return date.replace('\xa0', '').replace('\n', '').strip()

    @staticmethod
    async def extract_text(soup: BeautifulSoup) -> str:
        paragraphs: ResultSet = soup.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text(strip=True) for p in paragraphs[:5]]) if paragraphs else "No Text"

    @staticmethod
    async def extract_author(soup: BeautifulSoup) -> str | None:
        author_tag: BeautifulSoup = soup.find('a', class_='links__item-link')
        if author_tag:
            return author_tag.get_text(strip=True)

    async def extract_article_data(self, article_url: str) -> dict[str, str] | None:
        response = await self.fetch_links(article_url)
        if not response:
            logger.warning(f"Error fetching article {article_url}")
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

    async def sort_data(self) -> list[dict[str, str]] | None:
        all_links: list[str] = await self.extract_all_article_links(consts.URL)
        all_articles_data: list[dict[str, str]] = []
        for link in all_links:
            article_data: dict[str, str] = await self.extract_article_data(link)
            if article_data:
                all_articles_data.append(article_data)
        logger.info(all_articles_data)
        try:
            with open(consts.SAVE_FILE, 'w', encoding='utf-8') as f:
                dump(all_articles_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {consts.SAVE_FILE}")
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")
        return all_articles_data
