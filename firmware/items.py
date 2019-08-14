# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class FirmwareItem(Item):
    vendor = Field(default=None)
    device_name = Field(default=None)
    firmware_version = Field(default=None)
    device_class = Field(default=None)
    release_date = Field(default=None)

    # used by FilesPipeline
    files = Field()
    file_urls = Field()
