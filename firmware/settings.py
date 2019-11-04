# Scrapy settings for firmware project

BOT_NAME = 'firmware'

SPIDER_MODULES = ['firmware.spiders']
NEWSPIDER_MODULE = 'firmware.spiders'

FILES_STORE = 'firmware_files/'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
DOWNLOAD_TIMEOUT = 320

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

DOWNLOADER_MIDDLEWARES = {
    'firmware.middlewares.FirmwareDownloaderMiddleware': 543,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'firmware.pipelines.HpPipeline': 300,
    'firmware.pipelines.AvmPipeline': 1,
    'firmware.pipelines.LinksysPipeline': 1,
}

# Enable to run with Selenium. Set to the driver executable path
#SELENIUM_DRIVER_EXECUTABLE_PATH =
