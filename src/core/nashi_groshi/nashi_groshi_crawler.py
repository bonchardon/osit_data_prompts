from json import dump

from httpx import AsyncClient
from bs4 import BeautifulSoup, ResultSet, NavigableString, PageElement

from loguru import logger

from core.nashi_groshi import consts


class NashiGroshiData:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def fetch_links(self, url: str) -> str | None:
        if not (response := await self.client.get(url)):
            response.raise_for_status()
            return
        return response.text

    async def get_first_page_links(self, url: str) -> list[str] | None:
        response: str = await self.fetch_links(url)
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        ul_blocks: ResultSet = soup.find_all('ul')
        return [link.get('href') for link in ul_blocks[1].find_all('a')] if len(ul_blocks) >= 2 else []

    @staticmethod
    async def get_last_page_number(soup: BeautifulSoup) -> int:
        pagination: BeautifulSoup | NavigableString | None = soup.find('div', class_='pagination')
        last_page_link: dict[str, str] = pagination.find_all('a', class_='extra')[-1]
        last_page_url: str | None = last_page_link.get('href')

        if 'page' in last_page_url:
            try:
                last_page_number: int = int(last_page_url.split('/')[-2])
                return last_page_number
            except (IndexError, ValueError) as e:
                logger.error(f'Error parsing last page number from URL: {last_page_url}, error: {e}')
        else:
            logger.warning(f'Unexpected URL format for last page: {last_page_url}')
            return 1

    async def get_all_links(self) -> list[str] | None:
        base_url: str = consts.URL
        if not (response := await self.fetch_links(base_url)):
            logger.warning('Error retrieving the first page.')
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        last_page_number: int = await self.get_last_page_number(soup)
        if not (all_links := [
            link for page_num in range(2, last_page_number + 1) for link in
            await self.get_first_page_links(consts.URL_PAGINATION.format(page_num))
        ]):
            logger.warning('Check if all links are parserd correctly.')
            return
        return all_links

    @staticmethod
    async def parse_title(soup: BeautifulSoup) -> str | None:
        title_tag: BeautifulSoup | None = soup.find('h6', class_='title')
        if not (title := title_tag.find('strong').get_text(strip=True) if title_tag else 'No Title'):
            logger.error(' Cannot parse title. Check it out.')
            return
        return title

    @staticmethod
    async def parse_date(soup: BeautifulSoup) -> str | None:
        if not (date_tag := soup.find('span', class_='meta')):
            logger.error('Cannot parsedate.')
            return
        date: str = date_tag.get_text(strip=True).split('  //')[0]
        return date.replace('\xa0', '').replace('\n', '').strip()

    @staticmethod
    async def parse_author(soup: BeautifulSoup) -> str | None:
        if not (main_content := soup.find('div', class_='main-content')):
            return
        last_p_tag: PageElement = main_content.find_all('p')[-1]
        return last_p_tag.get_text(strip=True)

    @staticmethod
    async def parse_text(soup: BeautifulSoup) -> str | None:
        if not (paragraphs := soup.find_all('p')):
            return
        return ' '.join([p.get_text(strip=True) for p in paragraphs[:3]]) if paragraphs else 'No Text'

    async def extract_article_data(self, article_url: str) -> dict[str, str] | None:
        if not (response := await self.fetch_links(url=article_url)):
            logger.warning(f'Error fetching article {article_url}')
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        article_data = {
            'date': await self.parse_date(soup=soup),
            'link': article_url,
            'title': await self.parse_title(soup=soup),
            'author': await self.parse_author(soup=soup),
            'short_text': await self.parse_text(soup=soup)
        }

        return article_data

    async def sort_data(self):
        all_links: list[str] | None = await self.get_all_links()
        all_articles_data: list[dict[str, str]] = []

        for link in all_links:
            article_data: dict[str, str] | None = await self.extract_article_data(link)
            if article_data:
                all_articles_data.append(article_data)

        logger.info(f'Collected data for {len(all_articles_data)} articles.')
        logger.info(all_articles_data)

        try:
            with open(consts.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                dump(all_articles_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {consts.OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")
        return all_articles_data
