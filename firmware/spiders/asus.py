# -*- coding: utf-8 -*-

from scrapy import Spider
from firmware.items import FirmwareItem
from scrapy.loader import ItemLoader
# -*- coding: utf-8 -*-
from scrapy.http import Request
from bs4 import BeautifulSoup

class AsusSpider(Spider):
    name = 'asus'
    # allowed_domains = ['asus.com']
    # itemname = 'dat_item'
    manufacturer = 'ASUSTeK Computer Inc.'
    device_dictionary = dict(
        gt="Gaming-Router",
        rt="Router",
        rp="Repeater",
        ea="Access Point",
        ly="Mesh-Router",
        bl="Mesh-Router",
        ds="Modem-Router",
        pc="PCIe-Netzwerkkarte",
        us="USB-Netzwerkkarte",
        bt="Bluetooth-Adapter",
        br="Business-Router"
    )
    base_url = 'https://www.asus.com/de/%s/AllProducts/'
    start_urls = [
        base_url % 'Networking',
        base_url % 'Motherboards',
        base_url % 'Commercial-Gaming-Station',
        base_url % 'Commercial-Servers-Workstations'
    ]
    # Motherboards, Networking,

    # todo doppelpacks und Lyra mini, eventuell Source Code, vlt fragen, was noch wichtig ist?
    def parse(self, response):

        for product_anchor in response.xpath('//div[@class="product_level_1"]/table/tbody/tr/td/ul/li/a').getall():
            product_name, product_link = self.extract_anchor_attributes(product_anchor)

            yield Request(
                url='https://www.asus.com%sHelpDesk_BIOS/' % product_link,
                meta={'selenium': True,
                      'dont_redirect': True,
                      'handle_httpstatus_list': [302]
                      },
                callback=self.parse_firmware,
                cb_kwargs=dict(product_name=product_name)
            )
            # as of scrapy 1.7 cb_kwargs=dict(productname=productname)

    def parse_firmware(self, response, product_name):
        # firmware: 'https://www.asus.com/Networking/RT-AX88U/HelpDesk_BIOS/'
        download_link = response.xpath('//div[@class="download-inf-r"]/a/@href').get()
        item_loader_class = ItemLoader(
            item=FirmwareItem(),
            response=response,
            date_fmt=["%Y/%m/%d"]
        )

        item_loader_class.add_value("file_urls", [download_link])
        item_loader_class.add_value("device_name", product_name)
        item_loader_class.add_value('vendor', self.manufacturer)
        item_loader_class.add_value('firmware_version', self.extract_firmware_version(response))
        item_loader_class.add_value('device_class', self.extract_device_class(product_name))
        item_loader_class.add_value('release_date', self.extract_realese_date(response))

        return item_loader_class.load_item()

    @staticmethod
    def extract_anchor_attributes(product_anchor):
        soup = BeautifulSoup(product_anchor, "lxml")
        product_link = soup.a.get('href')
        product_name = soup.a.get_text()
        return product_name, product_link


    @staticmethod
    def extract_firmware_version(response):
        firmware_version = response.xpath('//span[@class="version"]/text()').get()
        if not firmware_version:
            firmware_version = None

        if response.xpath('//span[@class="beta"]').extract():
            firmware_version = firmware_version + ' beta'

        return firmware_version

    @staticmethod
    def extract_realese_date(response):
        release_date = response.xpath('//span[@class="lastdate"]/text()').get()
        if not release_date:
            release_date =

        return release_date

    def extract_device_class(self, product_name):
        if product_name[:2].lower() in self.device_dictionary:
            device_class = self.device_dictionary[product_name[:2].lower()]
        else:
            device_class = product_name

        return device_class
