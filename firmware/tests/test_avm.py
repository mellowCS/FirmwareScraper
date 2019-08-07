import pytest
from scrapy.http import Response, Request
from firmware.spiders import avm
from pathlib import Path

SPIDER = avm.AvmSpider()


class RequestIO:
    def __init__(self, filename: str, url: str):
        self.filename = filename
        self.url = url


@pytest.fixture(params=[
    RequestIO(filename=str(Path(__file__).parent) + '/html_files/fritzwlan_fritzwlan-repeater-1160_deutschland_.html',
              url='http://download.avm.de/fritzwlan/fritzwlan-repeater-1160/deutschland/'),
    RequestIO(filename=str(Path(__file__).parent) + '/html_files/fritzwlan_fritzwlan-repeater-1160_deutschland_fritz.os_.html',
              url='http://download.avm.de/fritzwlan/fritzwlan-repeater-1160/deutschland/fritz.os/')])
def mock_data(request):
    return request.param


def test_parse(mock_data):
    SPIDER.parse(mock_data)


def test_parse_product(mock_data):
    SPIDER.parse_product(mock_data)


def test_link_extractor(mock_data):
    print(SPIDER.link_extractor(mock_data, '..'))
