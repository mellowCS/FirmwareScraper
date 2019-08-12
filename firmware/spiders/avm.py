from scrapy import Request, Spider
from scrapy.loader import ItemLoader
from firmware.items import FirmwareItem
import re


class AvmSpider(Spider):
    name = 'avm'

    start_urls = [
        'http://download.avm.de/fritzbox/',
        'http://download.avm.de/fritzwlan/',
        'http://download.avm.de/fritzpowerline/'
    ]

    def parse(self, response):
        for product_url in self.link_extractor(response=response, prefix=('beta', 'tools', 'license', '..')):
            yield Request(url=product_url, callback=self.parse_product)

    def parse_product(self, response):
        path = response.request.url.split('/')[:-1]
        if path[-1] == 'fritz.os':
            yield from self.prepare_item_download(response, path)
        else:
            for sub in self.link_extractor(response=response, prefix=('recover', '..')):
                yield Request(url=response.urljoin(sub), callback=self.parse_product)

    def prepare_item_download(self, response, path: str):
        release_dates = self.date_extractor(response)
        for index, file_url in enumerate(self.link_extractor(response=response, prefix='..')):
            if file_url.endswith('.image'):
                loader = ItemLoader(item=FirmwareItem(), selector=file_url)
                loader.add_value('file_urls', file_url)
                loader.add_value('vendor', 'avm')
                loader.add_value('device_name', path[-3])
                loader.add_value('device_class', path[-4])
                loader.add_value('release_date', release_dates[index])
                yield loader.load_item()

    @staticmethod
    def link_extractor(response, prefix) -> list:
        return [response.urljoin(p) for p in response.xpath('//a/@href').extract() if not p.startswith(prefix)]

    @staticmethod
    def date_extractor(response) -> list:
        release_dates = list()
        for text in response.xpath('//pre/text()').extract():
            match = re.search(r'(\d{2}-\w{3}-\d{4} \d{2}:\d{2})', text)
            if match:
                release_dates.append(match.group(1))

        return release_dates
