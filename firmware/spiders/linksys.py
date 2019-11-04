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

    device_classes = {ClassIdentifier(['MR', 'EA', 'WRT', 'E', 'BEF', 'WKU', 'WRK']): 'Router',
                      ClassIdentifier(['X', 'AG', 'WAG']): 'Modem Router',
                      ClassIdentifier(['LRT']): 'VPN Router',
                      ClassIdentifier(['WHW', 'VLP']): 'Wifi Mesh System',
                      ClassIdentifier(['LAPN', 'LAPAC']): 'Business Access Point',
                      ClassIdentifier(['WAP']): 'Home Access Point',
                      ClassIdentifier(['SE', 'EZX']): 'Home Switch',
                      ClassIdentifier(['LGS']): 'Business Switch',
                      ClassIdentifier(['LACX', 'LACG']): 'Transceiver',
                      ClassIdentifier(['LACP']): 'Injector',
                      ClassIdentifier(['RE', 'WRE']): 'Repeater',
                      ClassIdentifier(['WUSB', 'USB', 'AE']): 'Wifi USB Adapter',
                      ClassIdentifier(['WET', 'WUM', 'WES']): 'Bridge',
                      ClassIdentifier(['PL']): 'PLC Adapter',
                      ClassIdentifier(['AM']): 'Modem',
                      ClassIdentifier(['CIT']): 'Internet Telephone',
                      ClassIdentifier(['WGA', 'WMA', 'WPC']): 'Wireless Adapter',
                      ClassIdentifier(['DMP', 'DMC', 'DMR', 'DMS', 'KWH', 'MCC']): 'Wireless Home Audio',
                      ClassIdentifier(['DMA']): 'Media Center Extender',
                      ClassIdentifier(['LNE', 'EG', 'WMP']): 'PCI Network Adapter',
                      ClassIdentifier(['EF', 'EP', 'PPS', 'PSU', 'WPS']): 'Print Server',
                      ClassIdentifier(['LCA']): 'Business Camera',
                      ClassIdentifier(['WMC']): 'Home Camera',
                      ClassIdentifier(['LMR']): 'Business Video Recorder',
                      ClassIdentifier(['NMH']): 'Media Hub',
                      ClassIdentifier(['PCM']): 'CardBus PC Card',
                      ClassIdentifier(['NSL']): 'Network Storage Link',
                      ClassIdentifier(['WML']): 'Music System'}

    x_path = {
        'product_urls': '//div[@class="item"]//@href',
        'device_names': '//div[@class="item"]//a/text()',
        'software_exists': '//div[@class="support-downloads col-sm-6"]//a[@title="Software herunterladen"]/@href',
        'firmware': '//div[@id="support-article-downloads"]/div[@class="article-accordian-content collapse-me"]',
    }

    start_urls = ['https://www.linksys.com/de/support/sitemap/']

    def parse(self, response: Response) -> Generator[Request, None, None]:
        for product_url, device_name in list(zip(response.xpath(self.x_path['product_urls']).extract(), response.xpath(self.x_path['device_names']).extract())):
            yield Request(url=response.urljoin(product_url), callback=self.parse_product, cb_kwargs=dict(device_name=device_name))

    def parse_product(self, response: Response, device_name: str) -> Generator[Request, None, None]:
        software_page = response.xpath(self.x_path['software_exists']).get()
        if software_page:
            yield Request(url=response.urljoin(software_page), callback=self.parse_versions, cb_kwargs=dict(device_name=device_name))

    def parse_versions(self, response: Response, device_name: str) -> Generator[FirmwareItem, None, None]:
        for version in response.xpath(self.x_path['firmware']).extract():
            yield from self.parse_urls(device_name=device_name, version=version)

    def parse_urls(self, device_name: str, version: str) -> Generator[FirmwareItem, None, None]:
        self.PRODUCT_DICTIONARIES = list()
        for firmware in re.findall(r'(Ver\.(?:.|\n)*?href=\"http://downloads\.linksys\.com/downloads/firmware/[\w\.]+\")', version):
            if re.search(r'(\.img|\.bin)', firmware):
                yield from self.parse_firmware(meta_data=self.prepare_meta_data(firmware=firmware, device_name=device_name, device_class=self.map_device_class(device_name)))

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

        match = re.search(r'Ver\.([^<([a-zA-Z]+]*)', firmware)
        version = match.group(1).strip(' ') if match else 'N/A'

        match = re.search(r'([^\d]+)(\d+/\d+/\d{4}).*', firmware)
        date = datetime.strptime(match.group(2), "%m/%d/%Y").strftime("%Y-%m-%d") if match else 'N/A'

        return dict(file_urls=file_urls, vendor='Linksys', device_name=device_name,
                    firmware_version=version, device_class=device_class, release_date=date)

    def map_device_class(self, product: str) -> str:
        for identifiers in self.device_classes.keys():
            for shortcut in identifiers.shortcuts:
                if product.startswith(shortcut):
                    return self.device_classes[identifiers]

        raise UnknownDeviceClassException('The product: {} cannot be found in the Device Class dictionary.'.format(product))