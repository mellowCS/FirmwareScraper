from typing import Generator, Tuple, Union

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class TPLinkGPL(Spider):
    handle_httpstatus_list = [404]
    name = 'tplink_gpl'

    allowed_domains = [
        'static.tp-link.com',
        'www.tp-link.com'
    ]

    start_urls = [
        'https://www.tp-link.com/de/support/gpl-code/',
    ]

    whitelist_enabled = False

    whitelist = ['Archer AX20']

    download_maxsize = 2147483648  # 2GiB

    XPATH = {
        'device_names_ddl': '//div[@data-class="wi-fi-routers"]/div[@class="item-box"]//a[@class="ga-click"][contains(@href, "static")]/text()',
        'device_links_ddl': '//div[@data-class="wi-fi-routers"]/div[@class="item-box"]//a[@class="ga-click"][contains(@href, "static")]/@href',
        'device_names_multi': '//div[@data-class="wi-fi-routers"]/div[@class="item-box"]//a[@class="ga-click"][not(contains(@href, "static"))]/text()',
        'device_links_multi': '//div[@data-class="wi-fi-routers"]/div[@class="item-box"]//a[@class="ga-click"][not(contains(@href, "static"))]/@href',
        'table_device_version': '//td[@class="model"]/following-sibling::td[1]/div/text()',
        'table_device_link': '//a[@class="bold ga-click"][text()="Download"]/@href',
    }

    def parse(self, response: Response, **kwargs: {}) -> Generator[Request, None, None]:
        ddl_extractor = TPLinkGPL.extract_ddl_firmware(response)
        for device, link in self.firmware_filter(ddl_extractor):
            meta_data = TPLinkGPL.prepare_meta_data(device, None, link)
            yield from TPLinkGPL.prepare_item_pipeline(meta_data)

        multi_fw_extractor = TPLinkGPL.extract_multi_firmware(response)
        for device, link in self.firmware_filter(multi_fw_extractor):
            cb_kwargs = dict(device=device)
            yield Request(url=link, callback=TPLinkGPL.parse_multi, cb_kwargs=cb_kwargs)

    @staticmethod
    def parse_multi(response: Response, device: str) -> Generator[FirmwareItem, None, None]:
        for version, link in TPLinkGPL.extract_table(response):
            meta_data = TPLinkGPL.prepare_meta_data(device, version, link)
            yield from TPLinkGPL.prepare_item_pipeline(meta_data)

    def firmware_filter(self, extractor: Generator[Tuple[str, str], None, None]) -> Generator[Tuple[str, str], None, None]:
        if not self.whitelist_enabled:
            yield from extractor
            return

        for device, link in extractor:
            if any(allowed in device for allowed in self.whitelist):
                yield device, link

    @staticmethod
    def extract_table(response: Response) -> Generator[Tuple[str, str], None, None]:
        versions = response.xpath(TPLinkGPL.XPATH['table_device_version']).extract()
        links = response.xpath(TPLinkGPL.XPATH['table_device_link']).extract()
        for version, link in zip(versions, links):
            yield version.strip(), link.strip()

    @staticmethod
    def extract_ddl_firmware(response: Response) -> Generator[Tuple[str, str], None, None]:
        names = response.xpath(TPLinkGPL.XPATH['device_names_ddl']).extract()
        links = response.xpath(TPLinkGPL.XPATH['device_links_ddl']).extract()
        for device, link in zip(names, links):
            yield device.strip(), link.strip()

    @staticmethod
    def extract_multi_firmware(response: Response) -> Generator[Tuple[str, str], None, None]:
        names = response.xpath(TPLinkGPL.XPATH['device_names_multi']).extract()
        links = response.xpath(TPLinkGPL.XPATH['device_links_multi']).extract()
        for device, link in zip(names, links):
            yield device.strip(), f'https://www.tp-link.com/phppage/gpl-res-list.html{link.strip()}&appPath=de'

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
    def prepare_meta_data(device: str, version: Union[str, None], file_url: str) -> dict:
        return {
            'file_urls': [file_url],
            'vendor': 'TP-Link',
            'device_name': device,
            'firmware_version': version if version is not None else '0.0',
            'device_class': 'Router',
            'release_date': '01/01/1970'  # no information available
        }
