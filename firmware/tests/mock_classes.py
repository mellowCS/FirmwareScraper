from parsel import Selector
from urllib.parse import urljoin


class MockResponse:
    def __init__(self, url, body):
        self.url = url
        self.body = body
        self.request = MockRequest(url, None)

    def urljoin(self, url):
        return urljoin(self.url, url)

    def xpath(self, xpath):
        selector = Selector(text=self.body)
        return selector.xpath(xpath)


class MockRequest:
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback
