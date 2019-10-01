# -*- coding: utf-8 -*-

from time import sleep

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class FirmwareSpiderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        settings = cls()
        crawler.signals.connect(settings.spider_opened, signal=signals.spider_opened)
        return settings

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):

        for request in start_requests:
            yield request

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class FirmwareDownloaderMiddleware(object):

    def __init__(self, driver_executable_path=None):
        options = webdriver.FirefoxOptions()
        options.headless = True
        if driver_executable_path is None:
            print('Selenium driver path not set correctly')
            self.driver = None

        else:
            self.driver = webdriver.Firefox(options=options, executable_path=driver_executable_path)
            self.wait = WebDriverWait(self.driver, 15)

    @classmethod
    def from_crawler(cls, crawler):
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        settings = cls(driver_executable_path=driver_executable_path)
        crawler.signals.connect(settings.spider_opened, signal=signals.spider_opened)

        return settings

    def process_request(self, request, spider):
        if "selenium" not in request.meta:
            return None
        self.driver.get(request.url)

        if "asus" in request.meta:
            body = self.asus_processor()
        else:
            sleep(2)
            body = str.encode(self.driver.page_source)

        return HtmlResponse(self.driver.current_url, body=body, encoding='utf-8', request=request)

    def asus_processor(self):
        try:
            self.wait.until(
                expected_conditions.presence_of_element_located((By.LINK_TEXT, 'DOWNLOAD')))

        except TimeoutException:
            print("No DOWNLOAD Field accessible for " + self.driver.current_url,
                  "Stop processing of " + self.driver.current_url)
            raise IgnoreRequest

        finally:
            return str.encode(self.driver.page_source)

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    def spider_closed(self):
        self.driver.quit()
