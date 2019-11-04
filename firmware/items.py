from scrapy import Field, Item


class FirmwareItem(Item):
    vendor = Field()
    device_name = Field()
    firmware_version = Field()
    device_class = Field()
    release_date = Field()

    file_urls = Field()
    files = Field()
