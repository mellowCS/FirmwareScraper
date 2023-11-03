# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from firmware.spiders.asus import AsusSpider
from firmware.spiders.avm import AvmSpider
from firmware.spiders.hp import HewlettPackardSpider
from firmware.spiders.linksys import LinksysSpider
from firmware.spiders.tplink import TPLink

crawlers = [
    AvmSpider,
    HewlettPackardSpider,
    LinksysSpider,
    TPLink,
    AsusSpider
]