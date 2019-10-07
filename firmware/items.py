
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class FirmwareItem(Item):
    vendor = Field()
    device_name = Field()
    firmware_version = Field()
    device_class = Field()
    release_date = Field()

    file_urls = Field()
    files = Field()
