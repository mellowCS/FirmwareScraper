import pytest
from urllib.parse import urljoin
from parsel import Selector
import avm

TEST_PAGE = u'''<html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Title</title>
                    </head>
                    <body>
                        <pre>
                            <a href="../">../</a>
                            <a href="beta/">beta/</a>
                            <a href="fritz.os/">fritz.os/</a>
                            12-Aug-2019 12:13 -
                            <a href="tools/">tools/</a>
                            13-Sep-2017 21:18 -
                            <a href="license.txt">license.txt</a>
                            21-Jun-2018 01:10 28193
                        </pre>
                    </body>
                </html>'''


class MockResponse:
    def __init__(self, url, body=''):
        self.url = url
        self.body = body

    def urljoin(self, url):
        return urljoin(self.url, url)

    def xpath(self, xpath):
        selector = Selector(text=self.body)
        return selector.xpath(xpath)


class MockRequest:
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback

    def requested_url(self):
        return self.url

    def callback_function(self):
        return self.callback


@pytest.fixture(scope='session', autouse=True)
def spider_instance():
    return avm.AvmSpider()


@pytest.mark.parametrize('response, expected', [(MockResponse(url='root/', body=TEST_PAGE), ['root/fritz.os/'])])
def test_parse(mocker, spider_instance, response, expected):
    mocker.patch(target='avm.Request', new=MockRequest)
    for index, request in enumerate(spider_instance.parse(response=response)):
        assert request.requested_url() == expected[index]


def test_parse_product():
    pass


def test_prepare_item_download():
    pass


@pytest.mark.parametrize('response, prefix, expected', [(MockResponse(url='root/', body=TEST_PAGE), ('tools', 'license', '../', 'beta'), ['root/fritz.os/'])])
def test_link_extractor(spider_instance, response, prefix, expected):
    assert spider_instance.link_extractor(response=response, prefix=prefix) == expected


@pytest.mark.parametrize('response, expected', [(MockResponse(url='root/', body=TEST_PAGE), ['12-Aug-2019 12:13', '13-Sep-2017 21:18', '21-Jun-2018 01:10'])])
def test_date_extractor(spider_instance, response, expected):
    assert spider_instance.date_extractor(response=response) == expected
