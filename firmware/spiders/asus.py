from bs4 import BeautifulSoup

from scrapy import Spider
from scrapy.http import Request
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
        br='Router (Business)'
    )
    base_url = 'https://www.asus.com/de/{0}/AllProducts/'
    start_urls = [
        base_url.format('Networking'),
        base_url.format('Motherboards'),
        base_url.format('Commercial-Gaming-Station'),
        base_url.format('Commercial-Servers-Workstations')
    ]

    def parse(self, response):
        for product_anchor in response.xpath('//div[@class="product_level_1"]/table/tbody/tr/td/ul/li/a').getall():
            product_name, product_link = self.extract_anchor_attributes(product_anchor)
            if 'AiMesh' in product_name:
                continue

            yield Request(
                url='https://www.asus.com%sHelpDesk_BIOS/' % product_link,
                meta={'selenium': True,
                      'dont_redirect': True,
                      'handle_httpstatus_list': [302],
                      'asus': True
                      },
                callback=self.parse_firmware,
                cb_kwargs=dict(product_name=product_name)
            )

    def parse_firmware(self, response, product_name):
        meta_data = self.prepare_meta_data(response, product_name)
        return self.prepare_item_pipeline(meta_data=meta_data)

    @staticmethod
    def prepare_item_pipeline(response, meta_data):
        item_loader_class = ItemLoader(item=FirmwareItem(), response=response, date_fmt=['%Y-%m-%d'])

        item_loader_class.add_value('device_name', meta_data['device_name'])
        item_loader_class.add_value('vendor', meta_data['vendor'])
        item_loader_class.add_value('firmware_version', meta_data['firmware_version'])
        item_loader_class.add_value('device_class', meta_data['device_class'])
        item_loader_class.add_value('release_date', meta_data['release_date'])
        item_loader_class.add_value("file_urls", meta_data['file_urls'])

        return item_loader_class.load_item()

    def prepare_meta_data(self, response, product_name):
        return {
            'vendor': 'asus',
            'release_date': self.extract_release_date(response),
            'device_name': product_name,
            'firmware_version': self.extract_firmware_version(response),
            'device_class': self.extract_device_class(response.url, product_name),
            'file_urls': response.xpath('//div[@class="download-inf-r"]/a/@href').get()
        }

    @staticmethod
    def extract_anchor_attributes(product_anchor):
        soup = BeautifulSoup(product_anchor, 'lxml')
        product_link = soup.a.get('href')
        product_name = soup.a.get_text()
        if 'ROG Rapture' in product_name:
            product_name = product_name.replace('ROG Rapture ', '')

        return product_name, product_link

    @staticmethod
    def extract_firmware_version(response):
        firmware_version = response.xpath('//span[@class="version"]/text()').get()
        if not firmware_version:
            firmware_version = None

        if 'Beta' in response.xpath('//span[@class="beta"]/text()').get():
            firmware_version = firmware_version + '-beta'

        return firmware_version.replace('Version ', '').replace(' ', '_')

    @staticmethod
    def extract_release_date(response):
        release_date = response.xpath('//span[@class="lastdate"]/text()').get()
        if not release_date:
            release_date = None

        return release_date.replace('/', '-')

    def extract_device_class(self, response_url, product_name):
        if 'Motherboards' in response_url:
            return 'Motherboard'
        if 'Commercial' in response_url:
            return 'BIOS'
        if product_name[:2].lower() in self.device_dictionary:
            return self.device_dictionary[product_name[:2].lower()]
        return None  # Networking
