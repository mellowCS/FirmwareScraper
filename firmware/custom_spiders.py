from abc import ABCMeta

from scrapy import Spider

from firmware.custom_requests import FTPFileRequest, FTPListRequest


class FTPSpider(Spider, metaclass=ABCMeta):

    def start_requests(self):
        for url in self.start_urls:
            yield FTPListRequest(url) if url.endswith('/') else FTPFileRequest(url)
