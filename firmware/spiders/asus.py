from datetime import datetime

from scrapy import Spider
from scrapy.exceptions import NotSupported
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class AsusSpider(Spider):
    name = 'asus'
    manufacturer = 'ASUS'
    device_dictionary = dict(
        gt='Router (Home)',  # Gaming
        rt='Router (Home)',
        rp='Repeater',
        ea='Access Point',
        ly='Router (Home)',  # Mesh
        bl='Router (Home)',  # Mesh
        ds='Router (Modem)',  # Modem
        pc='PCIe-Networkcard',
        us='USB-Networkcard',
        bt='Bluetooth-Adapter',
        br='Router (Business)',
        es='Server',
        rs='Server',
        ro='Router (Gaming)'  # ROG Rapture
    )
    base_url = 'https://www.asus.com/de/Networking-IoT-Servers/{}/All-series/filter/'
    start_urls = [
        base_url.format('WiFi-Routers'),
        base_url.format('Modem-Routers'),
        base_url.format('WiFi-6')
    ]

    def parse(self, response):
        for url_redirect in set(response.xpath('//div[contains(@class, "ProductCardNormal")]//a/@href').getall()):
            if url_redirect[-1] != '/':
                continue
            response.follow(response.url)
            yield response.follow(
                url=f'{url_redirect}HelpDesk_BIOS/',
                meta={'selenium': True,
                      'dont_redirect': True,
                      'handle_httpstatus_list': [302],
                      'asus': True
                      },
                callback=self.parse_firmware
            )

    def parse_firmware(self, response):
        meta_data = self.prepare_meta_data(response)
        if meta_data['file_urls'] is None:
            return []
        return self.prepare_item_pipeline(response=response, meta_data=meta_data)

    @staticmethod
    def prepare_item_pipeline(response, meta_data):
        item_loader_class = ItemLoader(item=FirmwareItem(), response=response, date_fmt=['%Y-%m-%d'])

        item_loader_class.add_value('device_name', meta_data['device_name'])
        item_loader_class.add_value('vendor', meta_data['vendor'])
        item_loader_class.add_value('firmware_version', meta_data['firmware_version'])
        item_loader_class.add_value('device_class', meta_data['device_class'])
        item_loader_class.add_value('release_date', meta_data['release_date'])
        item_loader_class.add_value('file_urls', meta_data['file_urls'])

        return item_loader_class.load_item()

    def prepare_meta_data(self, response):
        product_name = response.xpath('//h1[contains(@class, "productTitle")]/text()').get()
        return {
            'vendor': 'asus',
            'release_date': self.extract_release_date(response),
            'device_name': product_name,
            'firmware_version': self.extract_firmware_version(response),
            'device_class': self.extract_device_class(response.url, product_name),
            'file_urls':
                response.xpath('//div[contains(@class,"ProductSupportDriverBIOS__contentRight")]//a/@href').get()
        }

    @staticmethod
    def extract_firmware_version(response):
        firmware_version = response.xpath('//div[contains(@class,"ProductSupportDriverBIOS__version")]/text()').get()
        return firmware_version.replace('Version', '').strip() if firmware_version else None

    @staticmethod
    def extract_release_date(response):
        release_date = response.xpath('//div[contains(@class,"ProductSupportDriverBIOS__releaseDate")]/text()').get()
        return datetime.strptime(release_date.strip(), '%Y/%m/%d').date().isoformat() if release_date else None

    def extract_device_class(self, response_url, product_name):
        if product_name[:2].lower() in self.device_dictionary:
            return self.device_dictionary[product_name[:2].lower()]
        if 'Motherboards' in response_url:
            return 'Motherboard'
        if 'Commercial' in response_url:
            return 'BIOS'
        return None  # undefined
