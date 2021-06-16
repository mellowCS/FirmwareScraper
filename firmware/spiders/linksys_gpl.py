from typing import Generator, Tuple

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class LinksysGPL(Spider):
    handle_httpstatus_list = [404]
    name = 'linksys_gpl'

    allowed_domains = [
        'www.linksys.com',
        'downloads.linksys.com'
    ]

    start_urls = [
        'https://www.linksys.com/de/support-article?articleNum=114663',
    ]

    whitelist_enabled = True

    whitelist = ['EA7500']

    download_maxsize = 2147483648  # 2GiB

    XPATH = {
        'table_rows': '//table/thead/tr',
        'row_columns': './/td',
    }

    def parse(self, response: Response, **kwargs: {}) -> Generator[Request, None, None]:
        firmware_extractor = LinksysGPL.extract_firmwares(response)
        for device, version, link in self.firmware_filter(firmware_extractor):
            yield from LinksysGPL.collect_firmware(device, version, link)

    def firmware_filter(self, extractor: Generator[Tuple[str, str, str], None, None]) -> Generator[Tuple[str, str, str], None, None]:
        if not self.whitelist_enabled:
            yield from extractor
            return

        for device, version, link in extractor:
            if any(allowed in device for allowed in self.whitelist):
                yield device, version, link

    @staticmethod
    def collect_firmware(device_name: str, version: str, link: str) -> Generator[FirmwareItem, None, None]:
        meta_data = LinksysGPL.prepare_meta_data(device_name, version, link)
        yield from LinksysGPL.prepare_item_pipeline(meta_data)

    @staticmethod
    def extract_firmwares(response: Response) -> Generator[Tuple[str, str, str], None, None]:
        device_names = []
        table = response.xpath(LinksysGPL.XPATH['table_rows'])[1:]
        for row in table:
            columns = row.xpath(LinksysGPL.XPATH['row_columns'])
            if len(columns) not in [2, 3]:
                continue

            offset = 0
            if len(columns) == 3:
                device_names = columns[0].xpath('.//text()').extract()
                offset = 1

            version = ''.join(columns[offset].xpath('.//text()').extract()).strip()
            link = ''.join(columns[offset + 1].xpath('.//a/@href').extract()).strip()
            for device in device_names:
                yield device.strip(), version, link

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
    def prepare_meta_data(device_name: str, firmware_version: str, file_url: str) -> dict:
        return {
            'file_urls': [file_url],
            'vendor': 'Linksys',
            'device_name': device_name,
            'firmware_version': firmware_version,
            'device_class': '-',  # no information available
            'release_date': '01-01-1970',  # no information available
        }
