from json import JSONDecodeError, loads, load, dumps, dump
from os import environ, path, makedirs

from dotenv import load_dotenv

from loguru import logger

import openai

from docx import Document
import tiktoken

load_dotenv()


class DataCategorizer:
    openai.api_key = environ.get('OPENAI_API_KEY')

    def count_tokens(self, text, model="gpt-3.5-turbo"):
        """Estimate the number of tokens in a text using tiktoken."""
        encoding = tiktoken.get_encoding("cl100k_base")  # Encoding for GPT-3.5 turbo
        tokens = encoding.encode(text)
        return len(tokens)

    def split_text_into_chunks(self, text, max_tokens=4096):
        """Split text into chunks that fit within the token limits."""
        chunks = []
        current_chunk = []
        current_chunk_tokens = 0

        sentences = text.split('. ')

        for sentence in sentences:
            tokens = self.count_tokens(sentence)
            if current_chunk_tokens + tokens <= max_tokens:
                current_chunk.append(sentence)
                current_chunk_tokens += tokens
            else:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_chunk_tokens = tokens
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        return chunks

    async def corruption_categorizer(self, text):
        """Determine if the article is related to corruption."""
        prompt = (
            f'Ви отримаєте текст новини українською мовою: {text}. '
            'Вам потрібно визначити, чи є цей текст пов\'язаний з корупцією. '
            'Якщо текст пов\'язаний з корупцією, відповідь повинна бути "True". '
            'Якщо текст не пов\'язаний з корупцією, відповідь повинна бути "False".'
        )

        chunks = self.split_text_into_chunks(prompt)

        results = []
        for chunk in chunks:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'Ви корисний асистент, який визначає корупційний контент.'},
                    {'role': 'user', 'content': chunk},
                ],
                max_tokens=150,
                temperature=0.5,
                timeout=6000
            )
            result = response['choices'][0]['message']['content'].strip()
            results.append(result)

        return "True" if "True" in results else "False"

    async def corruption_data_only(self, text, link):
        """Extract detailed corruption-related data from the article."""
        prompt = (
            f"Ви отримаєте текст новини українською мовою: {text}. "
            "Будь ласка, екстрагуйте та надайте наступну інформацію у форматі JSON:\n"
            "1. **Індивідууми**: Перерахуйте всіх осіб, які згадуються, їхні посади та афіліації (якщо є).\n"
            "2. **Юридичні особи**: Перерахуйте всі компанії або організації в Україні (приватні або державні).\n"
            "3. **Офшори**: Якщо згадуються офшорні компанії або активи, перерахуйте їх.\n"
            "4. **Державні органи**: Перерахуйте будь-які залучені державні органи.\n\n"
            "Формат вихідних даних:\n"
            "{\n"
            "  \"individuals\": [\n"
            "    { \"name\": \"Ім'я особи\", \"position\": \"Посада\", \"affiliations\": [ \"Організація\" ] }\n"
            "  ],\n"
            "  \"legal_entities\": [\n"
            "    { \"entity\": \"Назва організації\", \"type\": \"Державна або приватна\" }\n"
            "  ],\n"
            "  \"offshore\": [ \"Офшорна компанія\" ],\n"
            "  \"government_bodies\": [ \"Державний орган\" ]\n"
            "}"
        )

        chunks = self.split_text_into_chunks(prompt)

        results: list[dict[str, str]] = []
        for chunk in chunks:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'Ви корисний асистент, який визначає корупційний контент.'},
                    {'role': 'user', 'content': chunk},
                ],
                max_tokens=500,
                temperature=0.5,
                timeout=6000
            )
            result = response['choices'][0]['message']['content'].strip()
            try:
                corruption_data = loads(result)  # Parse the response as JSON
                results.append(corruption_data)
            except JSONDecodeError:
                results.append({"message": "No corruption-related data found."})
        logger.info(results)
        return results

    async def process_json_file(self, input_file_path, output_file_path_json, output_file_path_docx):
        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = load(file)

        if isinstance(data, list) and len(data) > 0:
            results = []  # List to store processed articles' data

            doc: Document() = Document()
            doc.add_heading('Corruption Data Report', 0)

            for article in data:
                text = article.get("short_text", "")
                link = article.get("link", "Не надано")  # Extracting the link
                logger.info(f"Extracted link: {link}")  # Log the extracted link

                article_info = {
                    "date": article.get("date", "Не надано"),  # Extracting the date
                    "link": link,  # Extracting the link from the input and storing it
                    "title": article.get("title", "Не надано"),  # Extracting the title
                    "author": article.get("author", "Не надано"),  # Extracting the author
                }

                # Step 1: Check if the article is related to corruption
                is_corruption = await self.corruption_categorizer(text)

                if is_corruption.lower() == "true":
                    # Step 2: Split the article text into chunks if it's too long
                    chunks = self.split_text_into_chunks(text)

                    combined_extracted_data = []
                    for chunk in chunks:
                        # Step 2a: Extract the corruption-related data for each chunk
                        extracted_data = await self.corruption_data_only(chunk, link)  # Pass the link

                        if not extracted_data:  # If the extracted data is empty
                            combined_extracted_data.append({"message": "No corruption-related data found."})
                        else:
                            combined_extracted_data.extend(extracted_data)

                    # Combine the extracted data from all chunks
                    article_info["corruption_data"] = combined_extracted_data

                    # Step 3: Append the article info with corruption data to the results
                    results.append(article_info)

                    # Add the article data to the DOCX file
                    doc.add_heading(article_info["title"], level=1)
                    doc.add_paragraph(f"Date: {article_info['date']}")
                    doc.add_paragraph(f"Link: {article_info['link']}")
                    doc.add_paragraph(f"Author: {article_info['author']}")
                    doc.add_paragraph("Corruption Data:")

                    # Add combined corruption data to DOCX
                    corruption_data = article_info["corruption_data"]
                    for entry in corruption_data:
                        if isinstance(entry, dict):  # Format each entry as JSON-like structure
                            doc.add_paragraph(dumps(entry, ensure_ascii=False, indent=4))
                        else:
                            doc.add_paragraph(entry)

            # Ensure the output directory exists, create it if not
            output_dir_json = path.dirname(output_file_path_json)
            if not path.exists(output_dir_json):
                makedirs(output_dir_json)

            output_dir_docx = path.dirname(output_file_path_docx)
            if not path.exists(output_dir_docx):
                makedirs(output_dir_docx)

            # Step 4: Sort the results by date (assuming date format is YYYY-MM-DD)
            sorted_results = results

            # Step 5: Save the results to a JSON file
            with open(output_file_path_json, 'w', encoding='utf-8') as json_file:
                dump(sorted_results, json_file, ensure_ascii=False, indent=4)

            # Step 6: Save the DOCX document
            doc.save(output_file_path_docx)

            logger.success(f"Results saved to {output_file_path_json} and {output_file_path_docx}")
        else:
            logger.warning("No valid data found in the input JSON file.")
