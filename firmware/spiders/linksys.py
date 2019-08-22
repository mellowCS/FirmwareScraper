from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader
from typing import Union

from firmware.items import FirmwareItem


class ClassIdentifier:
    def __init__(self, shortcuts):
        self.shortcuts = shortcuts


class UnknownDeviceClassException(Exception):
    def __init__(self, product):
        self.product = product
        self.error_message()

    def error_message(self):
        print('\nProduct: {} not defined in device class dictionary\n'.format(self.product))


class LinksysSpider(Spider):
    handle_httpstatus_list = [404]
    name = 'linksys'

    device_classes = {ClassIdentifier(['MR', 'EA', 'WRT', 'E', 'BEF', 'WKU', 'WRK']): 'Router',
                      ClassIdentifier(['X', 'AG', 'WAG']): 'Modem Router',
                      ClassIdentifier(['LRT']): 'VPN Router', ClassIdentifier(['WHW', 'VLP']): 'Wifi Mesh System',
                      ClassIdentifier(['LAPN', 'LAPAC']): 'Business Access Point', ClassIdentifier(['WAP']): 'Home Access Point',
                      ClassIdentifier(['SE', 'EZX']): 'Home Switch', ClassIdentifier(['LGS']): 'Business Switch',
                      ClassIdentifier(['LACX', 'LACG']): 'Transceiver', ClassIdentifier(['LACP']): 'Injector',
                      ClassIdentifier(['RE', 'WRE']): 'Repeater', ClassIdentifier(['WUSB', 'USB', 'AE']): 'Wifi USB Adapter',
                      ClassIdentifier(['WET', 'WUM']): 'Bridge', ClassIdentifier(['PL']): 'PLC Adapter', ClassIdentifier(['AM']): 'Modem',
                      ClassIdentifier(['CIT']): 'Internet Telephone', ClassIdentifier(['WGA', 'WMA', 'WPC']): 'Wireless Adapter',
                      ClassIdentifier(['DMP', 'DMC', 'DMR', 'DMS', 'KWH', 'MCC']): 'Wireless Home Audio', ClassIdentifier(['DMA']): 'Media Center Extender',
                      ClassIdentifier(['LNE', 'EG', 'WMP']): 'PCI Network Adapter', ClassIdentifier(['EF', 'EP', 'PPS', 'PSU', 'WPS']): 'Print Server',
                      ClassIdentifier(['LCA']): 'Business Camera', ClassIdentifier(['WMC']): 'Home Camera', ClassIdentifier(['LMR']): 'Business Video Recorder',
                      ClassIdentifier(['NMH']): 'Media Hub', ClassIdentifier(['PCM']): 'CardBus PC Card', ClassIdentifier(['NSL']): 'Network Storage Link',
                      ClassIdentifier(['WML']): 'Music System'}

    x_path = {
        'product_pages': '//div[@class="item"]//@href',
        'software_exists': '//div[@class="support-downloads col-sm-6"]//a[@title="Software herunterladen"]/@href',
        'product_name': '//div[@class="col-xs-9 support-product-details-block"]/h1/text()'
    }

    start_urls = ['https://www.linksys.com/de/support/sitemap/']

    def parse(self, response: Response) -> Request:
        for product_page in response.xpath(self.x_path['product_pages']).extract():
            yield Request(url=response.urljoin(product_page), callback=self.parse_product)

    def parse_product(self, response: Response) -> Union[FirmwareItem, None]:
        software_page = response.xpath(self.x_path['software_exists']).get()
        if software_page:
            yield Request(url=response.urljoin(software_page), callback=self.parse_firmware,
                          cb_kwargs=dict(device_name=response.xpath(self.x_path['product_name']).get()))

    def parse_firmware(self, response: Response, device_name: str) -> FirmwareItem:
        for file_url in response.xpath('//@href').extract():
            if self.is_firmware(software=file_url):
                yield self.prepare_item_pipeline(meta_data=self.prepare_meta_data(response=response, device_name=device_name, file_url=file_url))

    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> FirmwareItem:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_url'])
        loader.add_value('file_urls', meta_data['file_url'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('release_date', meta_data['release_date'])

        yield loader.load_item()

    @staticmethod
    def is_firmware(software: str) -> bool:
        return True if '/firmware/' in software and software.endswith('.img') else False

    def prepare_meta_data(self, response: Response, device_name: str, file_url: str) -> dict:
        return {
            'file_url': file_url,
            'vendor': 'Linksys',
            'device_name': device_name,
            'firmware_version': self.extract_version(response=response),
            'device_class': self.map_device_class(device_name),
            'release_date': self.extract_date(response=response)
        }

    def map_device_class(self, product: str) -> str:
        try:
            for identifiers in self.device_classes.keys():
                for shortcut in identifiers.shortcuts:
                    if product.startswith(shortcut):
                        return self.device_classes[identifiers]
        except UnknownDeviceClassException(product=product) as e:
            raise e

    @staticmethod
    def extract_date(response: Response) -> str:
        return ''

    @staticmethod
    def extract_version(response: Response) -> str:
        return ''
