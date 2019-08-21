from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class LinksysSpider(Spider):
    handle_httpstatus_list = [404]
    name = 'linksys'

    # allowed_domains = ['https://www.linksys.com']

    start_urls = ['https://www.linksys.com/de/support/sitemap/']

    def parse(self, response: Response):
        for product_page in response.xpath('//div[@class="item"]//@href').extract():
            yield Request(url=response.urljoin(product_page), callback=self.parse_product)

    def parse_product(self, response):
        product_software = response.xpath('//div[@class="support-downloads col-sm-6"]//a[@title="Software herunterladen"]/@href').get()
        if product_software:
            yield Request(url=response.urljoin(product_software), callback=self.parse_firmware)
        else:
            yield None

    @staticmethod
    def parse_firmware(response):
        for software_url in response.xpath('//@href').extract():
            if '/firmware/' in software_url:
                print(software_url)