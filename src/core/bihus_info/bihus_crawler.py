from json import dump
from asyncio import sleep

from httpx import AsyncClient
from bs4 import BeautifulSoup
from helium import start_chrome, find_all, click, Text, wait_until, kill_browser

from loguru import logger

from core.bihus_info import consts


class BihusData:
    def __init__(self):
        self.client: AsyncClient = AsyncClient()

    async def fetch_links(self) -> str | None:
        if not (response := await self.client.get(consts.URL)):
            response.raise_for_status()
            return
        return response.text

    async def get_all_links(self) -> list[str] | None:
        links = ['https://bihus.info/nazk-pereviryaye-sposib-zhyttya-nardepa-gerasymova-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/na-zapysah-pro-kyyivskyj-deryban-zasvityvsya-najblyzhchyj-soratnyk-mera-kyyeva-palatnyj/',
                 'https://bihus.info/bihus-info-pokazaly-uchasnykiv-bagatorichnogo-kyyivskogo-derybanu-zemli/',
                 'https://bihus.info/otochennya-praczivnyka-sbu-i-kerivnyka-derzhliksluzhby-stvorylo-pryvatnu-laboratoriyu-yakij-derzhliksluzhba-viddaye-perevirku-likiv/',
                 'https://bihus.info/fantomni-budynky-i-shhedri-rodychi-pensionery-kogo-pislya-korupczijnogo-skandalu-v-kyyivskomu-metro-zabuly-pravoohoronczi/',
                 'https://bihus.info/policziya-pereviryaye-jmovirnu-pereplatu-za-remont-obstrilyanogo-rosiyanamy-gurtozhytku-pislya-zvernennya-yurystiv-bihus-info/',
                 'https://bihus.info/policziya-pereviryaye-tender-iz-jmovirnoyu-pidrobkoyu-dokumentiv-pislya-zvernennya-yurystiv-bihus-info/',
                 'https://bihus.info/shkola-rozsliduvan-dlya-veteraniv-ok-2-0-vid-bihus-info-gotovi-vchytys-robyty-topovi-rozsliduvannya/',
                 'https://bihus.info/nazk-pereviryaye-sposib-zhyttya-suddi-zhukova-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/pidryady-na-masshtabnu-vidbudovu-borodyanky-viddaly-kompaniyam-z-otochennya-eksmera-irpenya-ta-novogo-ochilnyka-podatkovoyi/',
                 'https://bihus.info/nachalnyk-golovnogo-servisnogo-czentru-zvilnyayetsya-razom-z-nym-ishhe-7-figurantiv-rozsliduvannya-bihus-info/',
                 'https://bihus.info/kyyivskyj-suddya-zhyve-v-mayetku-pid-kyyevom-z-vynogradnykamy-ozeramy-i-lisom-navkolo/',
                 'https://bihus.info/yahtu-figuranta-rozsliduvannya-bihus-info-za-blyzko-55-mln-yevro-areshtuvaly-v-italiyi/',
                 'https://bihus.info/sbu-zatrymala-figuranta-syuzhetu-bihus-info-pro-rozpyly-na-budivnycztvi-shkil-hersonshhyny-za-zbir-vidkativ/',
                 'https://bihus.info/gazovyky-vidpysaly-15-milyarda-baleryni-iz-istoriyi-pro-deryban-v-kyyivskomu-metro/',
                 'https://bihus.info/suddi-i-policzejski-masovo-pryvatyzuyut-sluzhbove-zhytlo-vygaduyuchy-sposoby-pryhovaty-vlasne/',
                 'https://bihus.info/ekskerivnyk-kyyivskogo-metro-viktor-braginskyj-ogoloshenyj-u-rozshuk-mvs/',
                 'https://bihus.info/nardep-kisilov-peresiv-na-nezadeklarovanyj-range-rover-za-65-mln-grn-posered-skandalu-z-jmovirnym-nezakonnym-zbagachennyam/',
                 'https://bihus.info/pidnyattya-podatkiv-zamist-borotby-z-tinnyu-yak-za-roky-getmanczeva-u-radi-najsirishi-zony-ekonomiky-shhe-bilshe-potemnily/',
                 'https://bihus.info/firmy-druzhyny-tovarysha-eksgolovy-zakarpatskoyi-oda-za-bezczin-otrymaly-zemli-v-prykordonnij-oblasti/',
                 'https://bihus.info/redakcziya-bihus-info-peremogla-u-premiyi-ukrayinskoyi-pravdy-vnominacziyi-zhurnalist-roku/',
                 'https://bihus.info/kyyivrada-rozirvala-dogovoru-orendy-z-kompaniyeyu-yakij-tayemno-viddala-zemlyu-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/nazk-pochalo-perevirku-sposobu-zhyttya-kilkoh-posadovcziv-scz-pislya-rozsliduvannya-pro-shemy-z-talonamy/',
                 'https://bihus.info/figuranta-rozsliduvan-bihus-info-suddyu-yemelyanova-vidpravyly-pid-vartu/',
                 'https://bihus.info/bihus-info-pokazalo-provalnu-robotu-i-nezadeklarovani-statky-spivrobitnykiv-servisnogo-czentru-mvs/',
                 'https://bihus.info/nabu-i-sap-rozsliduyut-jmovirne-nezakonne-zbagachennya-prokurora-guczulyaka/',
                 'https://bihus.info/grygorij-kozlovskyj-tyutyunovyj-biznes-v-tini-lyuksovyj-kurort-zamist-lisu-ta-kuplenyj-istorychnyj-czentr-lvova/',
                 'https://bihus.info/abu-rozsliduye-spravu-pro-jmovirne-nezakonne-zbagachennya-mykoly-tyshhenka-na-ponad-30-mln-grn/',
                 'https://bihus.info/pidozriyvanyy_u_miliardniy_aferi_fdmu/',
                 'https://bihus.info/eksochilnyku-kyyivskogo-metro-povidomyly-pro-pidozru-za-kolaps-na-synij-gilczi/',
                 'https://bihus.info/genprokuror-zareyestruvav-dva-kryminalnyh-provadzhennya-shhodo-narodnogo-deputata-romana-ivanisova-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/policziya-pereviryaye-jmovirnu-pereplatu-na-remonti-shkoly-pislya-zvernennya-yurystiv-bihus-info/',
                 'https://bihus.info/miljony-svoyim-zhurnalisty-doslidyly-yak-u-hersoni-protyaguyut-budivnycztva-shkil-popry-protesty-misczevyh/',
                 'https://bihus.info/pislya-syuzhetu-bihus-info-u-minoborony-povidomyly-pro-zvilnennya-lyudyny-nardepa-isayenka/',
                 'https://bihus.info/nazk-pereviryaye-sposib-zhyttya-suddi-dashutina-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/lyudyna-nardepa-vid-opzzh-naglyadatyme-za-vijskovym-budivnycztvom-v-minoborony/',
                 'https://bihus.info/pislya-rozsliduvannya-bihus-info-klychko-vidstoronyv-svogo-zastupnyka-volodymyra-prokopiva-i-zaklykav-pravoohoroncziv-pereviryty-jogo/',
                 'https://bihus.info/druzi-zastupnyka-klychka-staly-vlasnykamy-cziloyi-nyzky-obyektiv-komunalnoyi-neruhomosti-v-kyyevi/',
                 'https://bihus.info/prokuratura-vidkryla-provadzhennya-za-syuzhetom-bihus-info-pro-rozpyly-na-dytsadkah/',
                 'https://bihus.info/policziya-pereviryaye-jmovirni-pereplaty-na-kapitalnomu-remonti-oleksandrijskogo-kolegiumu-pislya-zvernennya-yurystiv-bihus-info/',
                 'https://bihus.info/rodyna-zastupnyka-klychka-za-jogo-kadencziyi-nakupyla-kvartyr-ta-ofisiv-po-vsomu-kyyevu/',
                 'https://bihus.info/u-naczpolicziyi-provodyat-sluzhbove-rozsliduvannya-shhodo-generala-policziyi-shajheta-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/general-naczpolicziyi-vykorystovuye-sluzhbove-avto-ta-operatyvni-nomery-dlya-poyizdok-u-sportzal/',
                 'https://bihus.info/yurysty-bihus-info-spilno-z-ngl-media-dotysly-rozirvannya-dogovoru-na-812-mln-grn-iz-tendernoyu-zmovnyczeyu/',
                 'https://bihus.info/suddya-verhovnogo-sudu-zasvityvsya-v-odnomu-iz-najdorozhchyh-kotedzhnyh-mistechok-kyyeva/',
                 'https://bihus.info/genprokuror-zareyestruvav-3-kryminalnyh-provadzhennya-shhodo-narodnyh-deputativ-ukrayiny-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/zhurnalisty-pokazaly-zhyttya-nardepa-dmytruka-v-londoni-jogo-spalyv-sportzal-i-dity-v-parku/',
                 'https://bihus.info/spravu-nardepa-klochka-peredaly-do-sudu-sap/',
                 'https://bihus.info/spravu-nardepa-klochka-peredaly-do-sudu-sap/',
                 'https://bihus.info/komanda-bihus-info-otrymala-mizhnarodnu-premiyu-free-media-awards-2024/',
                 'https://bihus.info/nardepy-pid-chas-povnomasshtabnoyi-vijny-prodovzhuyut-kupuvaty-lyuksovi-avtivky-i-hovaty-yih-na-rodychah/',
                 'https://bihus.info/polyanyczka-silrada-vidreaguvala-na-zapyt-zhurnalistky-pislya-skargy-yurystiv-proyektu-svoyi-lyudy-bihus-info/',
                 'https://bihus.info/palacz-na-mamu-kotedzh-vid-tata-nardepy-prodovzhuyut-obrostaty-novymy-kvadratnymy-metramy-i-zapysuvaty-yih-na-rodychiv/',
                 'https://bihus.info/rozsliduvannya-bihus-info-pro-stezhennya-z-boku-sbu-vyznaly-krashhym-na-naczionalnomu-konkursi-zhurnalistskyh-rozsliduvan/',
                 'https://bihus.info/matir-nardepa-ivanisova-podaruvala-jomu-12-mln-na-kvartyry-i-zareyestruvalasya-pidpryyemczem-v-okupovanomu-berdyansku/',
                 'https://bihus.info/rodyna-nardepa-ivanisova-za-period-jogo-deputatstva-skupyla-avto-i-neruhomosti-na-majzhe-2-miljony-dolariv/',
                 'https://bihus.info/rostyslava-shurmu-zvilnyly-z-posady-zastupnyka-kerivnyka-ofisu-prezydenta/',
                 'https://bihus.info/pershogo-zastupnyka-dyrektora-nabu-uglavu-zvilnyly-cherez-dyskredytacziyu-vykryvacha-vytoku-z-byuro/',
                 'https://bihus.info/komanda-bihus-info-otrymaye-mizhnarodnu-nagorodu-free-media-awards-2024/',
                 'https://bihus.info/na-hersonshhyni-vydilyly-desyatky-miljoniv-na-budivnycztvo-ukryttya-v-shkoli-yaku-ranishe-zamovlyaly-vzhe-z-ukryttyam/',
                 'https://bihus.info/poky-gromada-pid-kyyevom-zadorogo-kupuvala-pryvatni-dytsadky-syny-golovy-gromady-obrosly-majnom-na-desyatky-miljoniv/',
                 'https://bihus.info/pidpaly-avto-bihus-info-otrymaly-eksklyuzyvni-materialy-rozsliduvan-sbu-audio-video/',
                 'https://bihus.info/pislya-syuzhetu-bihus-info-nedoareshtovani-aktyvy-medvedchuka-v-kyyevi-taky-areshtuvaly-i-peredaly-v-arma/',
                 'https://bihus.info/otochennya-medvedchuka-zberigaye-vplyv-i-posady-v-systemi-ukrayinskoyi-advokatury/',
                 'https://bihus.info/nabu-pereviryaye-informacziyu-pro-regulyarni-poyizdky-v-london-slugy-zhupanyna/',
                 'https://bihus.info/yurysty-proyektu-svoyi-lyudy-bihus-info-dopomogly-ruhu-chesno-vygraty-apelyacziyu-u-dubinskogo/',
                 'https://bihus.info/sluga-narodu-zhupanyn-propustyv-zasidannya-rady-cherez-navchannya-u-londoni/',
                 'https://bihus.info/bilshe-nizh-yunarmiia-novyj-vseohopnyj-ruh-zasmoktuye-ditej-v-okupacziyi/',
                 'https://bihus.info/nardep-kisilov-zbagatyvsya-na-ponad-70-miljoniv-nazk-pidtverdylo-porushennya-z-rozsliduvannya-bihus-info/',
                 'https://bihus.info/v-noyabre-zaberesh-dengy-v-telefoni-ideologa-velykogo-budivnycztva-znajshlasya-perepyska-z-pidryadnykom-yakyj-natenderyv-na-4-milyardy/',
                 'https://bihus.info/nabu-povidomylo-pro-pidozru-pasynku-golovnogo-sudovogo-eksperta-ruvina-za-rishalovo-na-mytnyczi/',
                 'https://bihus.info/nazk-pereviryaye-sposib-zhyttya-vyhivskoho/',
                 'https://bihus.info/sotni-miljoniv-na-vidbudovu-hersonshhyny-viddaly-kompaniyi-povyazanij-z-misczevoyu-vladoyu-policzejskymy-i-velykym-budivnycztvom/',
                 'https://bihus.info/rodyna-eksposadovczya-ukrzaliznyczi-pislya-jogo-zvilnennya-obrosla-majnom-na-300-000/',
                 'https://bihus.info/slidstvo-u-spravi-nardepa-klochka-zaversheno-nabu-i-sap/',
                 'https://bihus.info/u-verhovnij-radi-vidreaguvaly-na-rozsliduvannya-bihus-info-pro-zlyvy-z-nabu-antykorupczijnyj-komitet-provede-publichne-zasidannya/',
                 'https://bihus.info/spravu-gladkovskogo-bukina-z-czyklu-rozsliduvan-pro-oboronku-skeruvaly-do-sudu/',
                 'https://bihus.info/rodynnyj-biznes-ochilnyka-naczpolu-torguvav-iz-firmamy-diyalnist-yakyh-rozsliduvav-jogo-naczpol/',
                 'https://bihus.info/prokuratura-pereviryaye-jmovirnyj-rozpyl-3-mln-na-remonti-shkoly-u-chernivczyah-pislya-zvernennya-yurystiv-bihus-info/',
                 'https://bihus.info/pislya-pryhodu-rezhysera-slugy-narodu-v-elektrobiznes-kompaniya-pidpysalasya-na-miljony-byudzhetnyh-groshej/',
                 'https://bihus.info/rodych-nardepa-tyshhenka-zasvityvsya-u-kryminalnij-spravi-na-140-miljoniv-po-budivnycztvu-metro-na-vynogradar/',
                 'https://bihus.info/nazk-pereviryaye-sposib-zhyttya-suddi-olega-hrypuna-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/nabu-provelo-obshuky-u-spravi-firm-brata-zastupnyka-glavy-op-shurmy/',
                 'https://bihus.info/nardep-klochko-otrymav-pidozru-u-nezakonnomu-zbagachenni-za-materialamy-z-rozsliduvannya-bihus-info/',
                 'https://bihus.info/bihus-info-u-spysku-nominantiv-mizhnarodnoyi-premiyi-free-media-pioneer-award-2024/',
                 'https://bihus.info/ivahiv-ne-hodyt-u-radu-bo-jomu-cze-ne-do-dushi-a-palyczya-propustyv-ponad-rik-zasidan-cherez-opzzh/',
                 'https://bihus.info/nazk-pereviryaye-sposib-zhyttya-prokurora-guczulyaka-pislya-syuzhetu-bihus-info/',
                 'https://bihus.info/ochilnyk-kyyivskogo-sudu-periodychno-buvaye-v-dorogomu-zamiskomu-mayetku-ale-ne-deklaruye-jogo/',
                 'https://bihus.info/identyfikovana-chastyna-rosijskyh-suden-i-zernotrejderiv-shho-vyvozyly-ukrayinske-zerno-cherez-okupovanyj-port-mariupolya/',
                 'https://bihus.info/policziya-pereviryaye-jmovirni-pereplaty-na-remonti-sportyvnoyi-shkoly-pislya-zvernennya-yurystiv-bihus-info/',
                 'https://bihus.info/60-dniv-pid-vartoyu-chy-30-miljoniv-zastavy-vaks-obrav-zapobizhnyj-zahid-artemu-shylu/',
                 'https://bihus.info/bihus-info-pokazaly-yak-rosiyany-znyshhuyut-sela-navkolo-avdiyivky-pislya-yiyi-zahoplennya/',
                 'https://bihus.info/kolyshnomu-sbushnyku-i-figurantu-rozsliduvannya-bihus-info-artemu-shylu-povidomyly-pro-pidozru/',
                 'https://bihus.info/nardep-kisilov-pidtverdyv-shho-zhyve-v-kvartyri-teshhi-za-kilka-miljoniv-dolariv/',
                 'https://bihus.info/zhurnalisty-bihus-info-finalno-vygraly-sud-u-gladkovskogo-u-spravi-rozsliduvannya-pro-oboronku/']
        return links

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
        if not (response := await self.fetch_links()):
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

    async def sort_data(self):
        all_links: list[str] | None = await self.get_all_links()
        all_articles_data: list[dict[str, str]] = []
        for link in all_links:
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


