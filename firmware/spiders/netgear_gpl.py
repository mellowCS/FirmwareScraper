from typing import Generator, Tuple

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class NetgearGPL(Spider):
    handle_httpstatus_list = [404]
    name = 'netgear_gpl'

    allowed_domains = [
        'www.downloads.netgear.com'
    ]

    start_urls = [
        'https://www.downloads.netgear.com/files/GDC/2649_GPLv1.html',
    ]

    whitelist_enabled = True

    whitelist = ['AC1450']

    download_maxsize = 2147483648  # 2GiB

    XPATH = {
        'device_paragraph': '//div/p/strong/parent::*|//div/p/span[@style="FONT-WEIGHT: bold"]/parent::*',
        'device_name': './/strong/text()|.//span[@style="FONT-WEIGHT: bold"]/text()',
        'device_versions': './/a/text()',
        'device_links': './/a/@href'
    }

    def parse(self, response: Response, **kwargs: {}) -> Generator[Request, None, None]:
        firmware_extractor = NetgearGPL.extract_firmwares(response)
        for device, version, link in self.firmware_filter(firmware_extractor):
            yield from NetgearGPL.collect_firmware(device, version, link)

    def firmware_filter(self, extractor: Generator[Tuple[str, str, str], None, None]) -> Generator[Tuple[str, str, str], None, None]:
        if not self.whitelist_enabled:
            yield from extractor
            return

        for device, version, link in extractor:
            if any(allowed in device for allowed in self.whitelist):
                yield device, version, link

    @staticmethod
    def collect_firmware(device_name: str, version: str, link: str) -> Generator[FirmwareItem, None, None]:
        meta_data = NetgearGPL.prepare_meta_data(device_name, version, link)
        yield from NetgearGPL.prepare_item_pipeline(meta_data)

    @staticmethod
    def extract_firmwares(response: Response) -> Generator[Tuple[str, str, str], None, None]:
        for paragraph in response.xpath(NetgearGPL.XPATH['device_paragraph']):
            device_name = paragraph.xpath(NetgearGPL.XPATH['device_name']).extract()
            versions = paragraph.xpath(NetgearGPL.XPATH['device_versions']).extract()
            links = paragraph.xpath(NetgearGPL.XPATH['device_links']).extract()

            for version, link in zip(versions, links):
                yield device_name, version, link

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
            'vendor': 'Netgear',
            'device_name': device_name,
            'firmware_version': firmware_version,
            'device_class': '-',  # no information available
            'release_date': '01-01-1970',  # no information available
        }
