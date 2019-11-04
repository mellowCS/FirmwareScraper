BOT_NAME = 'firmware'

SPIDER_MODULES = ['firmware.spiders']
NEWSPIDER_MODULE = 'firmware.spiders'

FILES_STORE = "./output/"

ROBOTSTXT_OBEY = True

DOWNLOAD_TIMEOUT = 320
DOWNLOADER_MIDDLEWARES = {
    'firmware.middlewares.FirmwareDownloaderMiddleware': 543,
}

ITEM_PIPELINES = {
    'firmware.pipelines.HpPipeline': 300,
    'firmware.pipelines.LinksysPipeline': 1
}

FILES_STORE = 'firmware_files/'


# Enable to run with Selenium
# Set to the driver executable path
#SELENIUM_DRIVER_EXECUTABLE_PATH = 
