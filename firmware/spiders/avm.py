from scrapy import Request, Spider
from scrapy.loader import ItemLoader
from firmware.items import FirmwareItem


class AvmSpider(Spider):
    name = 'AvmSpider'

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
        if path[-1] in ['fritz.os', 'recover']:
            for file_url in self.link_extractor(response=response, prefix='..'):
                loader = ItemLoader(item=FirmwareItem(), selector=file_url)
                loader.add_value('file_urls', file_url)
                yield loader.load_item()
        else:
            for sub in self.link_extractor(response=response, prefix='..'):
                yield Request(url=response.urljoin(sub), callback=self.parse_product)

    @staticmethod
    def link_extractor(response, prefix) -> list:
        return [response.urljoin(p) for p in response.xpath('//a/@href').extract() if not p.startswith(prefix)]
