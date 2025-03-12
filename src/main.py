from asyncio import run

from core.nashi_groshi.nashi_groshi_crawler import NashiGroshiData
from core.prot_corruption_shabunin.prompt_corup_crawler import AntacNewsData
from core.bihus_info.bihus_crawler import BihusData, consts
from core.ukr_pravda.ukr_pravda_crawler import UkrPravdaData
from core.shemy_radio_svoboda.shemy_crawler import RadioSvobodaData

from core.ai.prompts import DataCategorizer


async def main():
    # return await BihusData().sort_data()
    return await DataCategorizer().process_json_file(
        input_file_path='data/bihus_news_data.json',
        output_file_path_json='data/updated/schemes/bihus_news_data.json',
        output_file_path_docx='data/updated/schemes/doxc_file/schemes/bihus_news_data.docx'
    )

if __name__ == '__main__':
    run(main())
