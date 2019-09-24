# -*- coding: utf-8 -*-
from datetime import datetime
from re import search

from scrapy import Spider
from scrapy.http import Request
from scrapy.loader import ItemLoader
from firmware.items import FirmwareItem


class HewlettPackardSpider(Spider):
    name = 'hp'

    def start_requests(self):
        urls = ['https://support.hp.com/za-en/document/c03933242']
        for url in urls:
            yield Request(url=url, dont_filter=True,
                          meta={'selenium': True, 'dont_redirect': True, 'handle_httpstatus_list': [302]})

    def parse(self, response):
        for table_row in response.xpath('//div[@class="section expandable"]/div/div/div/table/tbody/tr'):
            next_url = table_row.xpath('td')[4].xpath('div/a/@href').get()
            if not next_url:
                continue
            if 'http://' not in next_url:
                next_url = 'http://' + next_url

            meta_data = self.prepare_meta_data(table_row)

            yield Request(url=next_url, callback=self.parse_firmware, cb_kwargs=dict(meta_data=meta_data),
                          meta={'selenium': True, 'dont_redirect': True, 'handle_httpstatus_list': [302], 'hp': True})

    def parse_firmware(self, response, meta_data):
        meta_data['file_urls'] = response.xpath(
            '//a[@class="button-sm primary hpdiaButton desktopHpdia"]/@href').getall()
        return self.prepare_item_pipeline(response, meta_data)

    @staticmethod
    def prepare_item_pipeline(response, meta_data):
        loader = ItemLoader(item=FirmwareItem(), response=response, date_fmt=['%Y-%m-%d'])

        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('release_date', meta_data['release_date'])
        loader.add_value("file_urls", meta_data['file_urls'])

        return loader.load_item()

    @staticmethod
    def prepare_meta_data(table_row):
        release_date = table_row.xpath('td')[3].xpath('div/text()').get()
        release_date = datetime.strptime(release_date, '%Y%m%d').date().isoformat()
        device_name = table_row.xpath('td')[0].xpath('div').get()
        device_name = search(r'</a> ?(.*?)</div>', device_name).group(1)

        return {
            'vendor': 'HP', 'device_class': 'Printer', 'device_name': device_name,
            'release_date': release_date,
            'firmware_version': table_row.xpath('td')[2].xpath('div/text()').get()}
