from datetime import datetime
from re import search, sub
from typing import Generator, List, Tuple

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem
from firmware.spiders.avm import AvmSpider


class AVMGPL(Spider):
    handle_httpstatus_list = [404]
    name = 'avm_gpl'

    allowed_domains = [
        'osp.avm.de',
    ]

    start_urls = [
        'https://osp.avm.de/fritzbox/',  # fritzboxes
        'https://osp.avm.de/fritzwlan/',  # wlan repeaters
        'https://osp.avm.de/fritzpowerline/',  # powerline adapters
    ]

    download_maxsize = 2147483648  # 2GiB

    XPATH = {
        'links': '//a[not(contains(@href, ".."))]/@href',
        'meta': '//a[not(contains(@href, ".."))]/following-sibling::text()',
    }

    def parse(self, response: Response, **kwargs: {}) -> Generator[Request, None, None]:
        links = AVMGPL.extract_links(response)
        infos = AVMGPL.extract_link_info(response)

        folders, gpl_archives = AVMGPL.separate_folders_from_gpl_archives(links, infos)

        for archive in gpl_archives:
            yield from AVMGPL.parse_archive(archive)

        for folder in folders:
            yield Request(url=folder[0], callback=self.parse)

    @staticmethod
    def parse_archive(archive: Tuple[str, Tuple[str, int, bool]]) -> Generator[FirmwareItem, None, None]:
        meta_data = AVMGPL.prepare_meta_data(archive)
        yield from AVMGPL.prepare_item_pipeline(meta_data)

    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> Generator[FirmwareItem, None, None]:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_urls'])
        loader.add_value('file_urls', meta_data['file_urls'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('release_date', meta_data['release_date'])
        yield loader.load_item()

    @staticmethod
    def prepare_meta_data(archive: Tuple[str, Tuple[str, int, bool]]) -> dict:
        file_url = archive[0]
        device_name = file_url.split('/')[-1]
        firmware_version = search(r'(\d{1,2}\.\d{2})', device_name)

        return {
            'file_urls': [file_url],
            'vendor': 'AVM',
            'device_name': device_name,
            'firmware_version': '0.0' if firmware_version is None else firmware_version.group(1),
            'device_class': AvmSpider.map_device_class(device_name),
            'release_date': archive[1][0],
        }

    @staticmethod
    def separate_folders_from_gpl_archives(links: List[str], infos: List[Tuple[str, int, bool]]):
        all_entries = list(zip(links, infos))

        folders = [e for e in all_entries if not e[1][2]]
        archives = [e for e in all_entries if e[1][2] and search(r'\.(tar|gz|bz2)', e[0])]

        return folders, archives

    @staticmethod
    def extract_links(response: Response) -> List[str]:
        return [response.urljoin(p) for p in response.xpath(AVMGPL.XPATH['links']).extract()]

    @staticmethod
    def extract_link_info(response: Response) -> List[Tuple[str, int, bool]]:
        infos = list()
        for meta in response.xpath(AVMGPL.XPATH['meta']).extract():
            clean = sub(r' +', ' ', meta.strip())

            the_date, _, the_size = clean.split(' ')
            try:
                the_date = datetime.strptime(the_date, '%d-%b-%Y').strftime('%d-%m-%Y')
            except ValueError:
                pass

            is_file_link = True
            try:
                the_size = int(the_size)
            except ValueError:
                the_size = -1
                is_file_link = False
            infos.append((the_date, the_size, is_file_link))
        return infos
