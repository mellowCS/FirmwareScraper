import re
from datetime import datetime
from typing import Generator, List, Tuple, Union

from scrapy import FormRequest, Request, Selector, Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader

from firmware.items import FirmwareItem


class DLinkGPL(Spider):
    handle_httpstatus_list = [404]
    name = 'dlink_gpl'

    allowed_domains = [
        'tsd.dlink.com.tw',
        'dlink-gpl.s3.amazonaws.com'
    ]

    start_urls = [
        'https://tsd.dlink.com.tw/dlist?SourceType=download&OS=GPL',
    ]

    whitelist_enabled = False

    whitelist = ['COVR-1100']

    download_maxsize = 2147483648  # 2GiB

    XPATH = {
        'device_names': '//td[@class="pord_3"]//a/@title',
        'device_overview_rows': '//tr[contains(@onclick, "dwn(")]',
        'onclick': './@onclick',
        'version': './/td[2]/text()',
        'download_td': '//td[@class="MdDclist12"]',
        'download_link': './/a[contains(@href, "dlink-gpl.s3.amazonaws.com")]/@href',
        'current_page': '//input[@name="sel_PageNo"]/@value',
        'pagination': '//input[@name="sel_PageNo"]/parent::td/text()[position() = last()]',
    }

    IDENTIFIER_RE = re.compile(r'^dwn\(\'([A-Z]+)\',[\'\da-zA-Z]+\)$')
    VERSION_RE = re.compile(r'FW\sv(\d+\..+)')
    PAGINATION_RE = re.compile(r'^\((\d+)\s\/\s(\d+)\)$')

    def parse(self, response: Response, **kwargs: {}) -> Generator[Request, None, None]:
        extractor = DLinkGPL.extract_devices(response)
        for product, model in self.firmware_filter(extractor):
            product_detail_request = DLinkGPL.construct_detail_post_request(product, model)
            yield product_detail_request

        next_page = DLinkGPL.extract_pagination_next(response)
        if next_page is not None:
            move_to_next_page = self.construct_next_page_post_request(next_page)
            yield move_to_next_page

    def construct_next_page_post_request(self, next_page: str) -> Request:
        form_data = dict(Enter='OK', sel_PageNo=next_page, ModelCategory='0', ModelSno='0', ModelCategory_='', ModelSno_='', search_string='', ModelVer='', Model_Sno='', OS='GPL')
        return FormRequest('https://tsd.dlink.com.tw/downloads2008list.asp?t=1&OS=GPL&SourceType=download&pagetype=G', callback=self.parse, formdata=form_data)

    @staticmethod
    def parse_device_overview(response: Response, product: str = '', model: str = '') -> Generator[Request, None, None]:
        rows = DLinkGPL.extract_device_overview_rows(response)
        for row in rows:
            identifier = DLinkGPL.extract_firmware_identifier(row)
            if identifier == '':
                continue

            version = DLinkGPL.extract_version(row)

            file_request = DLinkGPL.construct_file_request(product, model, version, identifier)
            yield file_request

    @staticmethod
    def parse_gpl_download(response: Response, product: str = '', model: str = '', version: str = '') -> Generator[Request, None, None]:
        table_data = DLinkGPL.extract_table_data_from_download_page(response)

        date = DLinkGPL.extract_date_from_table(table_data)
        download_link = DLinkGPL.extract_download_link(table_data)

        if download_link == '':
            return

        meta_data = DLinkGPL.prepare_meta_data(product, model, version, download_link, date)
        yield from DLinkGPL.prepare_item_pipeline(meta_data)

    def firmware_filter(self, extractor: Generator[Tuple[str, str], None, None]) -> Generator[Tuple[str, str], None, None]:
        if not self.whitelist_enabled:
            yield from extractor
            return

        for product, model in extractor:
            device = f'{product}-{model}'
            if any(allowed in device for allowed in self.whitelist):
                yield product, model

    @staticmethod
    def construct_detail_post_request(product: str, model: str) -> FormRequest:
        form_data = dict(Enter='OK', ModelCategory='0', ModelSno='', ModelCategory_=product, ModelSno_=model, Model_Sno='', OS='GPL')
        cb_kwargs = dict(product=product, model=model)
        return FormRequest('https://tsd.dlink.com.tw/ddetail', callback=DLinkGPL.parse_device_overview, cb_kwargs=cb_kwargs, formdata=form_data)

    @staticmethod
    def construct_file_request(product: str, model: str, version: str, identifier: str) -> FormRequest:
        form_data = dict(Enter='OK', ModelCategory='0', ModelSno='0', ModelCategory_=product, ModelSno_=model, Model_Sno='', ModelVer='', docuSno=identifier, docuSource='1')
        cb_kwargs = dict(product=product, model=model, version=version)
        yield FormRequest('https://tsd.dlink.com.tw/ddgo', callback=DLinkGPL.parse_gpl_download, cb_kwargs=cb_kwargs, formdata=form_data)

    @staticmethod
    def extract_download_link(table_data: List[Selector]) -> str:
        all_links = table_data[2].xpath(DLinkGPL.XPATH['download_link']).extract()
        for link in all_links:
            if not link.endswith('.txt'):
                return link

        return ''

    @staticmethod
    def extract_pagination_next(response: Response) -> Union[str, None]:
        current_page = int(response.xpath(DLinkGPL.XPATH['current_page']).extract()[0].strip())
        pagination = response.xpath(DLinkGPL.XPATH['pagination']).extract()[0].strip()

        page_match = DLinkGPL.PAGINATION_RE.search(pagination)

        if page_match is None:
            return None

        if current_page != int(page_match.group(1)):
            return None

        last_page = int(page_match.group(2))

        if current_page >= last_page:
            return None

        return str(current_page + 1)

    @staticmethod
    def extract_date_from_table(table_data: List[Selector]) -> str:
        return table_data[3].xpath('.//text()').extract()[0].strip()

    @staticmethod
    def extract_table_data_from_download_page(response) -> List[Selector]:
        return response.xpath(DLinkGPL.XPATH['download_td'])

    @staticmethod
    def extract_devices(response: Response) -> Generator[Tuple[str, str], None, None]:
        for device in response.xpath(DLinkGPL.XPATH['device_names']).extract():
            product, model = device.split('-', 1)
            yield product, model

    @staticmethod
    def extract_device_overview_rows(response: Response) -> Generator[Selector, None, None]:
        for row in response.xpath(DLinkGPL.XPATH['device_overview_rows']):
            yield row

    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> Generator[FirmwareItem, None, None]:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_urls'])
        loader.add_value('file_urls', meta_data['file_urls'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('release_date', meta_data['release_date'])
        yield loader.load_item()

    @staticmethod
    def extract_version(row: Selector) -> str:
        description = row.xpath(DLinkGPL.XPATH['version']).extract()[0].strip()

        version_match = DLinkGPL.VERSION_RE.search(description)
        version = version_match.group(1) if version_match is not None else '0.0'
        return version

    @staticmethod
    def extract_firmware_identifier(row: Selector) -> str:
        onclick = row.xpath(DLinkGPL.XPATH['onclick']).extract()[0]

        identifier_match = DLinkGPL.IDENTIFIER_RE.search(onclick)
        if identifier_match is None:
            return ''

        identifier = identifier_match.group(1)
        return identifier

    @staticmethod
    def prepare_meta_data(product: str, model: str, firmware_version: str, file_url: str, date: str) -> dict:
        return {
            'file_urls': [file_url],
            'vendor': 'D-Link',
            'device_name': f'{product}-{model}',
            'firmware_version': firmware_version,
            'device_class': '-',  # no information available
            'release_date': datetime.strptime(date, '%Y/%m/%d').strftime('%d-%m-%Y')
        }
