import pytest

import avm
from mock_classes import MockResponse, MockRequest

PRODUCT_PAGE = u'''<html lang="en">
                       <head>
                           <meta charset="UTF-8">
                           <title>Index of /fritzbox/</title>
                       </head>
                       <body>
                           <pre>
                               <a href="../">../</a>
                               <a href="beta/">beta/</a>
                               01-Jan-2019 02:45 -
                               <a href="fritzbox-1234/">fritzbox-1234/</a>
                               12-Aug-2019 12:13 -
                               <a href="tools/">tools/</a>
                               13-Sep-2017 21:18 -
                               <a href="license.txt">license.txt</a>
                               21-Jun-2018 01:10 28193
                           </pre>
                       </body>
                   </html>'''

LOCATION_PAGE = u'''<html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <title>Index of /fritzbox/fritzbox-1234/</title>
                        </head>
                        <body>
                            <pre>
                                <a href="../">../</a>
                                <a href="deutschland/">deutschland/</a>
                                12-Aug-2019 12:13 -
                                <a href="other/">other/</a>
                                13-Sep-2017 21:18 -
                            </pre>
                        </body>
                    </html>'''

OS_PAGE = u'''<html lang="en">
                  <head>
                      <meta charset="UTF-8">
                      <title>Index of /fritzbox/fritzbox-1234/deutschland/</title>
                  </head>
                  <body>
                      <pre>
                          <a href="../">../</a>
                          <a href="fritz.os/">fritz.os/</a>
                          12-Aug-2019 12:13 -
                          <a href="recover/">recover/</a>
                          13-Sep-2017 21:18 -
                      </pre>
                  </body>
              </html>'''

FIRWMARE_PAGE = u'''<html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <title>Index of /fritzbox/fritzbox-1234/deutschland/fritz.os/</title>
                        </head>
                        <body>
                            <pre>
                                <a href="../">../</a>
                                <a href="FRITZ.Box_1234-07.12.image">FRITZ.Box_1234-07.12.image</a>
                                12-Aug-2019 12:13 22241280
                                <a href="info_de.txt">info_de.txt</a>
                                13-Sep-2017 21:18 47418
                            </pre>
                        </body>
                    </html>'''


@pytest.fixture(scope='session', autouse=True)
def spider_instance():
    return avm.AvmSpider()


@pytest.fixture(scope='function', autouse=True)
def mocked_request(monkeypatch):
    monkeypatch.setattr(avm, 'Request', MockRequest)


@pytest.mark.parametrize('response, expected', [(MockResponse(url='/fritzbox/', body=PRODUCT_PAGE), '/fritzbox/fritzbox-1234/')])
def test_parse(spider_instance, response, expected):
    for request in spider_instance.parse(response=response):
        assert request.url == expected


@pytest.mark.parametrize('response, expected', [(MockResponse(url='/fritzbox/fritzbox-1234/', body=LOCATION_PAGE), ['/fritzbox/fritzbox-1234/deutschland/', '/fritzbox/fritzbox-1234/other/']),
                                                (MockResponse(url='/fritzbox/fritzbox-1234/other/', body=OS_PAGE), ['/fritzbox/fritzbox-1234/other/fritz.os/']),
                                                (MockResponse(url='/fritzbox/fritzbox-1234/other/fritz.os/', body=FIRWMARE_PAGE), ['/FRITZ.Box_1234-07.12.image'])])
def test_parse_product(monkeypatch, spider_instance, response, expected):
    with monkeypatch.context() as monkey:
        monkey.setattr(avm.AvmSpider, 'parse_firmware', lambda *_, **__: [MockRequest(url='/FRITZ.Box_1234-07.12.image', callback=None, cb_kwargs=None)])
        for index, request in enumerate(spider_instance.parse_product(response=response)):
            assert request.url == expected[index]


@pytest.mark.parametrize('response, device_name, expected', [(MockResponse(url='/fritzbox/fritzbox-1234/other/fritz.os/', body=FIRWMARE_PAGE), 'fritzbox-1234', ['test'])])
def test_parse_firmware(monkeypatch, spider_instance, response, device_name, expected):
    with monkeypatch.context() as monkey:
        monkey.setattr(avm.AvmSpider, 'prepare_meta_data', lambda *_, **__: {})
        monkey.setattr(avm.AvmSpider, 'prepare_item_pipeline', lambda *_, **__: {'test': ['test']})
        assert list(spider_instance.parse_firmware(response=response, device_name=device_name)) == expected


@pytest.mark.parametrize('meta_data, expected', [(dict(file_urls=['/FRITZ.Box_1234-07.12.image'], vendor='AVM',
                                                       device_name='fritzbox-1234', firmware_version='07.12',
                                                       device_class='Router', release_date='12-08-2019'),
                                                  [dict(file_urls=['/FRITZ.Box_1234-07.12.image'], vendor=['AVM'],
                                                       device_name=['fritzbox-1234'], firmware_version=['07.12'],
                                                       device_class=['Router'], release_date=['12-08-2019'])]
                                                  )])
def test_prepare_item_pipeline(spider_instance, meta_data, expected):
    assert list(spider_instance.prepare_item_pipeline(meta_data=meta_data)) == expected


def test_prepare_meta_data():
    pass


@pytest.mark.parametrize('product, expected', [('fritzbox-6430-cable', 'Router'), ('fritzrepeater-1200', 'Repeater'), ('fritzwlan-repeater-310-a', 'Repeater'),
                                               ('fritzwlan-usb-stick-ac-430', 'Wifi-Stick'), ('fritzpowerline-1000e', 'PLC Adapter')])
def test_map_device_class(spider_instance, product, expected):
    assert spider_instance.map_device_class(product=product) == expected


@pytest.mark.parametrize('response, prefix, expected', [(MockResponse(url='/fritzbox/', body=PRODUCT_PAGE), ('beta', 'tools', 'license', '..'), ['/fritzbox/fritzbox-1234/'])])
def test_extract_links(spider_instance, response, prefix, expected):
    assert spider_instance.extract_links(response=response, prefix=prefix) == expected


@pytest.mark.parametrize('response, expected', [(MockResponse(url='/fritzbox/fritzbox-1234/other/fritz.os/', body=FIRWMARE_PAGE), ['12-08-2019', '13-09-2017'])])
def test_extract_dates(spider_instance, response, expected):
    assert spider_instance.extract_dates(response=response) == expected


@pytest.mark.parametrize('date, expected', [('12-Aug-2019', '12-08-2019'), ('24-Dec-2019', '24-12-2019')])
def test_convert_date(spider_instance, date, expected):
    assert spider_instance.convert_date(date=date) == expected


@pytest.mark.parametrize('firmware, specifier, expected', [('fritz.powerline_1000ET_01_05.image', 'fritzpowerline-1000e-t', '01.05'),
                                                           ('fritz.powerline_1000A_E_02_06.image', 'fritzpowerline-1000a-e', '02.06'),
                                                           ('FRITZ.Powerline_1260E.157.07.12.image', None, '157.07.12'),
                                                           ('FRITZ.Box_6810_LTE.108.06.34.image', None, '108.06.34'),
                                                           ('FRITZ.Box_3490.en-de-es-it-fr-pl.140.07.01.image', None, '140.07.01')])
def test_extract_version(spider_instance, firmware, specifier, expected):
    assert spider_instance.extract_version(firmware=firmware, product_specifier=specifier) == expected


@pytest.mark.parametrize('array, prefix, index, expected', [(['a', 'b', 'c'], '', 0, ['abc', 'a_b_c', 'a_bc', 'ab_c']),
                                                            (['a', 'b', 'c', 'd'], '', 0, ['abcd', 'a_b_c_d', 'a_bcd', 'ab_cd', 'abc_d', 'a_b_cd', 'a_bc_d', 'ab_c_d'])])
def test_permutations(spider_instance, array, prefix, index, expected):
    assert sorted(list(spider_instance.permutations(array=array, prefix=prefix, index=index))) == sorted(expected)
