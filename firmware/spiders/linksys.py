from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

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
        'product_urls': '//div[@class="item"]//@href',
        'device_names': '//div[@class="item"]//a/text()',
        'software_exists': '//div[@class="support-downloads col-sm-6"]//a[@title="Software herunterladen"]/@href',
        'firmware': '//a[contains(@href, "/firmware/") and contains(@href, ".img")]/@href'
    }

    start_urls = ['https://www.linksys.com/de/support/sitemap/']

    def parse(self, response: Response) -> Request:
        for product_url, device_name in list(zip(response.xpath(self.x_path['product_urls']).extract(), response.xpath(self.x_path['device_names']).extract())):
            yield Request(url=response.urljoin(product_url), callback=self.parse_product, cb_kwargs=dict(device_name=device_name))

    def parse_product(self, response: Response, device_name: str) -> Request:
        software_page = response.xpath(self.x_path['software_exists']).get()
        if software_page:
            yield Request(url=response.urljoin(software_page), callback=self.parse_firmware, cb_kwargs=dict(device_name=device_name))

    def parse_firmware(self, response: Response, device_name: str) -> FirmwareItem:
        for firmware in response.xpath(self.x_path['firmware']).extract():
            yield from self.prepare_item_pipeline(meta_data=self.prepare_meta_data(response=response, device_name=device_name, file_url=firmware))

    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> FirmwareItem:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_urls'])
        loader.add_value('file_urls', meta_data['file_urls'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('release_date', meta_data['release_date'])

        yield loader.load_item()

    def prepare_meta_data(self, response: Response, device_name: str, file_url: str) -> dict:
        return {
            'file_urls': file_url,
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
