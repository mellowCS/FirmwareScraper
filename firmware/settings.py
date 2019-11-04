BOT_NAME = 'firmware'

SPIDER_MODULES = ['firmware.spiders']
NEWSPIDER_MODULE = 'firmware.spiders'

FILES_STORE = "./output/"

ROBOTSTXT_OBEY = True

DOWNLOADER_MIDDLEWARES = {
    'firmware.middlewares.FirmwareDownloaderMiddleware': 543,
}

ITEM_PIPELINES = {
    'firmware.pipelines.AsusPipeline': 300
}

# Enable to run with Selenium
# Set to the driver executable path
#SELENIUM_DRIVER_EXECUTABLE_PATH = ''
