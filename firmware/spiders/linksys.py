import re
from datetime import datetime
from typing import Generator

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class ClassIdentifier:
    def __init__(self, shortcuts):
        self.shortcuts = shortcuts


class UnknownDeviceClassException(Exception):
    pass


class LinksysSpider(Spider):
    PRODUCT_DICTIONARIES = list()
    handle_httpstatus_list = [404]
    name = 'linksys'

    device_classes = {
        ClassIdentifier(['AM']): 'Modem',
        ClassIdentifier(['CIT']): 'Internet Telephone',
        ClassIdentifier(['EF', 'EP', 'PPS', 'PSU', 'WPS']): 'Print Server',
        ClassIdentifier(['DMP', 'DMC', 'DMR', 'DMS', 'KWH', 'MCC']): 'Wireless Home Audio',
        ClassIdentifier(['DMA']): 'Media Center Extender',
        ClassIdentifier(['LACP']): 'Injector',
        ClassIdentifier(['LACX', 'LACG']): 'Transceiver',
        ClassIdentifier(['LAPN', 'LAPAC']): 'Business Access Point',
        ClassIdentifier(['LCA']): 'Business Camera',
        ClassIdentifier(['LMR', 'LNR']): 'Business Video Recorder',
        ClassIdentifier(['LNE', 'EG', 'WMP']): 'PCI Network Adapter',
        ClassIdentifier(['LRT']): 'VPN Router',
        ClassIdentifier(['LGS']): 'Business Switch',
        ClassIdentifier(['MR', 'EA', 'WRT', 'E', 'BEF', 'WKU', 'WRK']): 'Router',
        ClassIdentifier(['M10', 'M20']): 'Hotspot',
        ClassIdentifier(['NMH']): 'Media Hub',
        ClassIdentifier(['NSL']): 'Network Storage Link',
        ClassIdentifier(['PCM']): 'CardBus PC Card',
        ClassIdentifier(['PL']): 'PLC Adapter',
        ClassIdentifier(['RE', 'WRE']): 'Repeater',
        ClassIdentifier(['SE', 'EZX']): 'Home Switch',
        ClassIdentifier(['WAP']): 'Home Access Point',
        ClassIdentifier(['WET', 'WUM', 'WES']): 'Bridge',
        ClassIdentifier(['WGA', 'WMA', 'WPC']): 'Wireless Adapter',
        ClassIdentifier(['WHW', 'VLP', 'MX']): 'Wifi Mesh System',
        ClassIdentifier(['WMC', 'WVC']): 'Home Camera',
        ClassIdentifier(['WML']): 'Music System',
        ClassIdentifier(['WUSB', 'USB', 'AE']): 'Wifi USB Adapter',
        ClassIdentifier(['X', 'AG', 'WAG']): 'Modem Router'
    }

    x_path = {
        'product_urls': '//div[@class="item"]//@href',
        'device_names': '//div[@class="item"]//a/text()',
        'software_exists': '//div[@class="support-downloads col-sm-6"]//a[@title="Download Software"]/@href',
        # german text: Software herunterladen
        'firmware': '//div[@id="support-article-downloads"]/div[@class="article-accordian-content collapse-me"]',
    }

    start_urls = ['https://www.linksys.com/us/support/sitemap/']

    def parse(self, response: Response) -> Generator[Request, None, None]:
        for product_url, device_name in list(zip(response.xpath(self.x_path['product_urls']).extract(),
                                                 response.xpath(self.x_path['device_names']).extract())):
            yield Request(url=response.urljoin(product_url), callback=self.parse_product,
                          cb_kwargs=dict(device_name=device_name))

    def parse_product(self, response: Response, device_name: str) -> Generator[Request, None, None]:
        software_page = response.xpath(self.x_path['software_exists']).get()
        if software_page:
            yield Request(url=response.urljoin(software_page), callback=self.parse_versions,
                          cb_kwargs=dict(device_name=device_name))

    def parse_versions(self, response: Response, device_name: str) -> Generator[FirmwareItem, None, None]:
        for version in response.xpath(self.x_path['firmware']).extract():
            yield from self.parse_urls(device_name=device_name, version=version)

    def parse_urls(self, device_name: str, version: str) -> Generator[FirmwareItem, None, None]:
        self.PRODUCT_DICTIONARIES = list()
        for firmware in re.findall(r'Ver.+href=\".+(?:bin|img)\"', version):
            if re.search(r'(\.img|\.bin)', firmware):
                yield from self.parse_firmware(
                    meta_data=self.prepare_meta_data(firmware=firmware, device_name=device_name,
                                                     device_class=self.map_device_class(device_name)))

    def parse_firmware(self, meta_data: dict) -> Generator[FirmwareItem, None, None]:
        if meta_data not in self.PRODUCT_DICTIONARIES:
            self.PRODUCT_DICTIONARIES.append(meta_data)
            yield from self.prepare_item_pipeline(meta_data=meta_data)

    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> Generator[FirmwareItem, None, None]:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_urls'])
        loader.add_value('file_urls', meta_data['file_urls'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('release_date', meta_data['release_date'])

        yield loader.load_item()

    @staticmethod
    def prepare_meta_data(firmware: str, device_name: str, device_class: str) -> dict:
        match = re.search(r'href="(.*\.bin|.*\.img)"', firmware)
        file_urls = match.group(1) if match else 'N/A'

        match = re.search(r'(?:Ver|Version)\.([^<([a-zA-Z]+]*)', firmware)
        version = match.group(1).strip(' ').replace('\xa0', '') if match else 'N/A'

        match = re.search(
            r'((?:[1-9]|0[1-9]|10|11|12)(?:\s|\.|/|-)(?:[a-zA-Z]+|[1-9]|[1-2][0-9]|30|31)(?:\s|\.|/|-)(?:20|19)\d{2})',
            firmware)
        date = datetime.strptime(match.group(1).replace(' ', '/').replace('\xa0', '/'), r"%m/%d/%Y").strftime(
            "%Y-%m-%d") if match else 'N/A'

        return dict(file_urls=file_urls, vendor='Linksys', device_name=device_name,
                    firmware_version=version, device_class=device_class, release_date=date)

    def map_device_class(self, product: str) -> str:
        for identifiers in self.device_classes.keys():
            for shortcut in identifiers.shortcuts:
                if product.startswith(shortcut):
                    return self.device_classes[identifiers]

        raise UnknownDeviceClassException(
            'The product: {} cannot be found in the Device Class dictionary.'.format(product))
