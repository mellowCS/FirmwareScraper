from datetime import datetime
from typing import Generator

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class TPLink(Spider):
    handle_httpstatus_list = [404]
    name = 'tplink'

    allowed_domains = [
        'www.tp-link.com',
        'static.tp-link.com'
    ]

    start_urls = [
        'https://www.tp-link.com/de/home-networking/wifi-router/',  # these are routers without integrated modem
        'https://www.tp-link.com/de/home-networking/all-gateways/',  # these are routers with integrated modem
        'https://www.tp-link.com/de/home-networking/deco/',  # these are AIO access points like the fritz mesh solutions
        'https://www.tp-link.com/de/home-networking/mifi/',  # portable routers with 3G/4G modems
        'https://www.tp-link.com/de/home-networking/range-extender/',  # repeaters
        'https://www.tp-link.com/de/home-networking/powerline/',  # powerline adapters
        'https://www.tp-link.com/de/home-networking/access-point/',  # PoE-powered wifi access points
        'https://www.tp-link.com/de/home-networking/soho-switch/', #Soho switch
        'https://www.tp-link.com/de/home-networking/all-adapter/',
        'https://www.tp-link.com/de/home-networking/all-network-expansion/',
        'https://www.tp-link.com/de/home-networking/all-accessories/',
        'https://www.tp-link.com/de/home-networking/cloud-camera/',
        'https://www.tp-link.com/de/home-networking/smart-bulb/',
        'https://www.tp-link.com/de/home-networking/smart-plug/'
    ]
    XPATH = {
        'products_on_page': '//a[contains(@class,"tp-product-link")]/@href',
        'product_pages': '//li[@class="tp-product-pagination-item"]/a[@class="tp-product-pagination-btn"]/@href',
        'product_name': '//h2[@class="product-name"]/text()',
        'product_support_link': '//a[contains(@class,"support")]/@href',
        'hardware_versions': '//dl[@class="select-version"][1]/dd/ul/li/a/text()',
        'current_version': '//span[@class="current-version"]/text()',
        'firmware_download_link': '//tr[@class="basic-info"][1]//a[contains(@class, download)]/@href',
        'firmware_version': '//span[@id="verison-hidden"]/text()',
        'firmware_release_date': '//tr[@class="detail-info"][1]/td[1]/span[2]/text()[1]',
    }

    def parse(self, response: Response, **kwargs: {}) -> Generator[Request, None, None]:
        for product_url in TPLink.extract_products_on_page(response=response):
            print("Schedule product", product_url)
            yield Request(url=product_url, callback=TPLink.parse_product_details)
        for page_url in TPLink.extract_pages(response=response):
            print("Schedule product page", page_url)
            yield Request(url=page_url, callback=self.parse)

    @staticmethod
    def parse_product_details(product_page: Response):
        device_names = product_page.xpath(TPLink.XPATH['product_name']).extract()
        if not device_names:
            return []
        device_name = device_names[0]
        device_class = TPLink.map_device_class(product_page.url)

        support_link = TPLink.extract_product_support_link(product_page)

        return [Request(
            url=support_link,
            callback=TPLink.parse_firmware,
            cb_kwargs=dict(device_name=device_name, device_class=device_class),
        )]

    @staticmethod
    def parse_firmware(support_page: Response, device_name: str, device_class: str):
        res = []
        hw_versions = support_page.xpath(TPLink.XPATH['hardware_versions']).extract()
        if hw_versions:
            print(f"\tSchedule hardware versions: {hw_versions}")
            for version in hw_versions:
                res.append(Request(
                    url=f"{support_page.url}{version.lower()}",
                    callback=TPLink.parse_firmware_version,
                    cb_kwargs=dict(device_name=device_name, device_class=device_class),
                ))
            yield from res
        else:
            print(f"\tSchedule firmware version: {support_page.url}")
            yield from TPLink.parse_firmware_version(support_page, device_name, device_class)

    @staticmethod
    def parse_firmware_version(support_page: Response, device_name: str, device_class: str):
        print(f"\t\tParse firmware hwversion: {support_page.url}")
        file_url = TPLink.extract_firmware_download_link(support_page)
        firmware_version = TPLink.extract_firmware_version(support_page)
        firmware_release_date = TPLink.extract_firmware_release_date(support_page)
        hw_version = TPLink.extract_hardware_version(support_page)
        if any(not var for var in [device_name, device_class, file_url, firmware_version, firmware_release_date]):
            return

        meta_data = TPLink.prepare_meta_data(device_name, device_class, file_url, firmware_version,
                                             firmware_release_date, hw_version)
        yield from TPLink.prepare_item_pipeline(meta_data)


    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> Generator[FirmwareItem, None, None]:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_urls'])
        loader.add_value('file_urls', meta_data['file_urls'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('release_date', meta_data['release_date'])
        loader.add_value('hw_version', meta_data['hw_version'])
        yield loader.load_item()

    @staticmethod
    def prepare_meta_data(device_name: str, device_class: str, file_url: str, firmware_version: str,
                          firmware_release_date, hw_version:str) -> dict:
        return {
            'file_urls': [file_url],
            'vendor': 'TP-Link',
            'device_name': device_name,
            'firmware_version': firmware_version.replace(device_name, '').strip(),
            'device_class': device_class,
            'release_date': datetime.strptime(firmware_release_date.strip(), '%Y-%m-%d').strftime('%d-%m-%Y'),
            'hw_version': hw_version
        }

    @staticmethod
    def extract_products_on_page(response: Response) -> Generator[str, None, None]:
        for result in response.xpath(TPLink.XPATH['products_on_page']).extract():
            yield response.urljoin(result)

    @staticmethod
    def extract_product_support_link(product_page: Response) -> str:
        return product_page.urljoin(product_page.xpath(TPLink.XPATH['product_support_link']).extract()[0])

    @staticmethod
    def extract_firmware_download_link(support_page: Response) -> str:
        download_links = support_page.xpath(TPLink.XPATH['firmware_download_link']).extract()
        if download_links:
            return support_page.urljoin(download_links[0])
        else:
            return ""

    @staticmethod
    def extract_firmware_version(support_page: Response) -> str:
        firmware_version = support_page.xpath(TPLink.XPATH['firmware_version']).extract()
        if firmware_version:
            return firmware_version[0]
        else:
            return ""

    def extract_hardware_version(support_page: Response) -> str:
        hardware_version = support_page.xpath(TPLink.XPATH['current_version']).extract()
        if hardware_version:
            return hardware_version[0]
        else:
            return ""

    @staticmethod
    def extract_firmware_release_date(support_page: Response) -> str:
        firmware_release_date = support_page.xpath(TPLink.XPATH['firmware_release_date']).extract()
        if firmware_release_date:
            return firmware_release_date[0]
        else:
            return ""

    @staticmethod
    def extract_pages(response: Response) -> Generator[str, None, None]:
        for page in response.xpath(TPLink.XPATH['product_pages']).extract():
            yield response.urljoin(page)

    @staticmethod
    def map_device_class(product_url: str) -> str:
        if any(kw in product_url for kw in ['wifi-router', 'all-gateways', 'mifi']):
            return 'Router'
        if 'range-extender' in product_url:
            return 'Repeater'
        if 'powerline' in product_url:
            return 'PLC Adapter'
        if any(kw in product_url for kw in ['access_point', 'deco']):
            return 'AP'
        return 'Router'
#
