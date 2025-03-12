import json
import re


def convert_md_to_json(md_file_path):
    # Regular expression to capture the date, title, short text, and links
    regex = r"\*\*(\d{2}\.\d{2}\.\d{4})\s([^\*]+)\*\*\s*([^\[]+)(?:\[(.*?)\])?"

    # Read the contents of the markdown file
    with open(md_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        md_content = file.read()

    # Find all matches using regular expression
    matches = re.findall(regex, md_content)

    articles = []

    # Process the matches and create a list of articles
    for match in matches:
        date, title, short_text, link = match

        # If no link is provided, use a placeholder URL
        link = link if link else "URL_PLACEHOLDER"

        # Author is assumed to be "Не надано" if not mentioned in the markdown
        author = "Не надано"

        article = {
            "date": date,
            "link": link,
            "title": title.strip(),
            "author": author,
            "short_text": short_text.strip()
        }
        articles.append(article)

    # Return the result as JSON
    return json.dumps(articles, ensure_ascii=False, indent=4)


# Example usage
md_file_path = "/Users/user/Documents/coding/osint_work_2/osit_data_prompts/src/data/additional_data_2/20250303_АРМА.docx"

json_output = convert_md_to_json(md_file_path)

# Save the output as a .json file
json_file_path = "output_file.json"  # Replace with desired output path
with open(json_file_path, 'w', encoding='utf-8') as json_file:
    json_file.write(json_output)

print(f"Data successfully written to {json_file_path}")
