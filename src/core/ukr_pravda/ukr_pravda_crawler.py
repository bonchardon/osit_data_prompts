from json import dump

from httpx import AsyncClient
from bs4 import BeautifulSoup, ResultSet

from loguru import logger

from core.nashi_groshi import consts


class UkrPravdaData:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def fetch_links(self, url: str) -> str | None:
        try:
            response = await self.client.get(url)
            response.raise_for_status()  # Raise error for bad HTTP response codes
            return response.text
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")

    async def get_first_page_links(self, url: str) -> list[str]:
        """Get links to articles from the first page of news."""
        response = await self.fetch_links(url)
        if not response:
            return []

        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
        article_blocks: ResulSet = soup.find_all('div', class_='article_news_list')  # Adjust according to actual class
        links = []

        for article in article_blocks:
            article_header = article.find('a')
            if article_header and article_header.get('href'):
                href = article_header.get('href')
                if href.startswith('/'):  # Ensure it's a relative URL
                    full_url = 'https://www.pravda.com.ua' + href
                else:
                    full_url = href
                links.append(full_url)
        logger.info(f'Found {len(links)} article links.')
        return links

    async def extract_article_data(self, article_url: str) -> dict[str, str] | None:
        if not (response := await self.fetch_links(article_url)):
            logger.warning(f"Error fetching article {article_url}")
            return
        soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')

        # 1. Extract title (assuming it's in an <h1> tag or similar)
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # 2. Extract time or publication date (you can adjust the date format as needed)
        time_tag = soup.find('span', class_='time')  # You may need to check the correct class for time
        time = time_tag.get_text(strip=True) if time_tag else "No Time"

        # Format date to "dd.mm.yyyy" as required
        try:
            date_parts = time.split(" ")  # Assume date and time are separated by a space
            date = date_parts[0]  # Date is in the first part, e.g., "09.09.2022"
        except Exception:
            date = "Unknown Date"

        # 3. Extract author and date from the <div class="post_time">
        post_time_tag = soup.find('div', class_='post_time')
        if post_time_tag:
            author_tag = post_time_tag.find('span', class_='post_author')
            author = author_tag.get_text(strip=True).replace(" —", "") if author_tag else "Unknown Author"
            post_date = post_time_tag.get_text(strip=True).split('—')[-1].strip() if post_time_tag else "Unknown Date"
        else:
            author = "Unknown Author"
            post_date = "Unknown Date"

        # 4. Extract short text from <div class="post_text">
        post_text_tag = soup.find('div', class_='post_text')
        short_text = post_text_tag.get_text(strip=True) if post_text_tag else "No Short Text"

        article_data = {
            'date': post_date,
            'link': article_url,
            'title': title,
            'author': author,
            'short_text': short_text
        }

        return article_data

    async def sort_data(self):
        """Go through all collected links and extract article data."""
        base_url = "https://www.pravda.com.ua"  # Base URL for Ukrainian Pravda
        first_page_url = "https://www.pravda.com.ua/news/date_22022025/"  # Adjust to the correct page
        all_links = await self.get_first_page_links(first_page_url)
        all_articles_data = []

        for link in all_links:
            article_data = await self.extract_article_data(link)
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
