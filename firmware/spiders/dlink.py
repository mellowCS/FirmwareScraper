from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from time import sleep


class DlinkSpider(Spider):
    name='dlink'
    handle_http_status = [404]

    start_urls = ['https://support.dlink.com/AllPro.aspx']

    def __init__(self):
        super().__init__()
        self.options = Options()
        self.options.headless = True
        self.driver = webdriver.Firefox(options=self.options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def parse(self, response):
        self.driver.get(response.url)
        for 