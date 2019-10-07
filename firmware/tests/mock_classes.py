from urllib.parse import urljoin

from parsel import Selector


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
    def __init__(self, url, callback, cb_kwargs=None):
        self.url = url
        self.callback = callback
        self.cb_kwargs = cb_kwargs
