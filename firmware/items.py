from scrapy.item import Item, Field


class FirmwareItem(Item):
    vendor = Field(default=None)
    device_name = Field(default=None)
    firmware_version = Field(default=None)
    device_class = Field(default=None)
    release_date = Field(default=None)

    files = Field()
    file_urls = Field()
