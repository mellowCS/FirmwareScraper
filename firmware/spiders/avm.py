import scrapy
from collections import namedtuple


class AvmSpider(scrapy.Spider):
    name = 'AvmSpider'
    Product = namedtuple('Product', ['name', 'country', 'type', 'urls'])

    def start_requests(self):
        urls = [
            'http://download.avm.de/fritzbox/',
            'http://download.avm.de/fritzwlan/',
            'http://download.avm.de/fritzpowerline/'
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for product_url in [response.urljoin(p) for p in response.xpath('//a/@href').extract() if p.startswith('fritz')]:
            yield scrapy.Request(url=product_url, callback=self.parse_product)

    def parse_product(self, response):
        if response.request.url.split('/')[-2] in ['fritz.os', 'recover']:
            product = self.Product(name=response.request.url.split('/')[-4], country=response.request.url.split('/')[-3], type=response.request.url.split('/')[-2],
                                   urls=[response.urljoin(p) for p in response.xpath('//a/@href').extract() if not p.startswith('..')])
            yield None
        else:
            for sub in [response.urljoin(p) for p in response.xpath('//a/@href').extract() if not p.startswith('..')]:
                yield scrapy.Request(url=response.urljoin(sub), callback=self.parse_product)
