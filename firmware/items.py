# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FirmwareItem(scrapy.Item):
    vendor = scrapy.Field()
    device_name = scrapy.Field()
    firmware_version = scrapy.Field()
    device_class = scrapy.Field()
    release_date = scrapy.Field()

    file_urls = scrapy.Field()
    files = scrapy.Field()
