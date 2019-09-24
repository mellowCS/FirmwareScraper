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
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        settings = cls()
        crawler.signals.connect(settings.spider_opened, signal=signals.spider_opened)
        return settings

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for request in start_requests:
            yield request

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class FirmwareDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

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
        # This method is used by Scrapy to create your spiders.
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

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        # else:
        #    return None

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
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    def spider_closed(self):
        self.driver.quit()
