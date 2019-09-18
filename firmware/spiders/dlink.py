import logging
import re
from typing import Generator

from scrapy import Spider
from scrapy.http import Response
from scrapy.loader import ItemLoader
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from firmware.items import FirmwareItem


class DlinkSpider(Spider):
    name='dlink'
    handle_http_status = [404]

    start_urls = ['https://support.dlink.com/AllPro.aspx']

    x_path = dict(
        product_appendix='//table//tr//a[@class="aRedirect"][1]/@alt',
        hardware_versions='//div[@class=" sel_mg"]/a[@class="selectBox downloadddl selectBox-dropdown"]',
        firmware_options='//ul[@class="ulA" and li//span[contains(text(), "Firmware")]]//select[contains(@class, "downloadlistddl")]/option[@value]',
        select_box='//ul[@class="ulA" and li//span[contains(text(), "Firmware")]]//a[@class="selectBox downloadlistddl downloadlistddl_Yes selectBox-dropdown"]',
        date='//ul[@class="ulA" and li//span[contains(text(), "Firmware")]]/li/span[@class="fileDate"]'
    )

    def __init__(self):
        super().__init__()
        self.options = Options()
        self.options.headless = True
        LOGGER.setLevel(logging.WARNING)
        LOGGER.propagate = False
        self.driver = webdriver.Firefox(options=self.options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def parse(self, response: Response) -> Generator[list, None, None]:
        product_urls = ['https://support.dlink.com/ProductInfo.aspx?m=' + url for url in response.xpath(self.x_path['product_appendix']).extract()]
        for url in product_urls:
            yield from self.parse_firmware(url=url)
        self.__exit__(None, None, None)

    def parse_firmware(self, url: str) -> Generator[list, None, None]:
        files, dates = list(), list()
        self.driver.get(url=url)
        hardware_versions = self.driver.find_elements_by_xpath(self.x_path['hardware_versions'])
        if len(hardware_versions) > 2:
            select_hardware = self.driver.find_element_by_xpath(self.x_path['select_hardware'])
            select_hardware.click()
            select_options = len(hardware_versions) - 1
            while select_options > 0:
                select_hardware.send_keys(Keys.ARROW_DOWN)
                WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located)
                files_of_current_version = self.driver.find_elements_by_xpath(self.x_path['firmware_options'])
                files.extend(files_of_current_version)
                dates.extend(self.extract_dates(url=url, files=files_of_current_version))
                select_options -= 1
        else:
            files = self.driver.find_elements_by_xpath(self.x_path['firmware_options'])
            dates = self.extract_dates(url=url, files=files)

        print('\n++++++++++++++++++++++++++++++++++++++++++ FIRMWARE COLLECTED +++++++++++++++++++++++++++++++++++++++++\n')
        for file_url, date in list(zip(files, dates)):
            print(
                'FILE: {} ----------------------------- DATE: {}'.format(file_url.get_attribute('value'), date))
            yield from self.prepare_item_pipeline(
                self.prepare_meta_data(file_url=file_url.get_attribute('value'), date=date, device_name='Bla'))

    def extract_dates(self, url: str, files: list):
        dates = list()
        print('DEBUG FILE PRINT: {}'.format(url))
        dates.append(self.driver.find_element_by_xpath(self.x_path['date']).text)
        if len(files) > 1:
            select_box = self.driver.find_element_by_xpath(self.x_path['select_box'])
            dates.append(self.driver.find_element_by_xpath(self.x_path['date']).text)

            select_box.click()
            select_options = len(files) - 1
            while select_options > 0:
                select_box.send_keys(Keys.ARROW_DOWN)
                dates.append(self.driver.find_element_by_xpath(self.x_path['date']).text)
                select_options -= 1

        return dates

    def prepare_meta_data(self, file_url: str, date: str, device_name: str) -> dict:
        file_url_components = file_url.split('|')
        match = re.search(r'.*\((.*)\)', file_url_components[-1])
        version = match.group(1) if match else 'N/A'

        return dict(file_urls=file_url_components[1],
                    vendor='D-Link',
                    device_name=device_name,
                    firmware_version=version,
                    device_class=self.map_device_class(device_name=device_name),
                    release_date=self.convert_date(date=date)
                    )

    @staticmethod
    def prepare_item_pipeline(meta_data: dict) -> Generator[FirmwareItem, None, None]:
        loader = ItemLoader(item=FirmwareItem(), selector=meta_data['file_urls'])
        loader.add_value('file_urls', meta_data['file_urls'])
        loader.add_value('vendor', meta_data['vendor'])
        loader.add_value('device_name', meta_data['device_name'])
        loader.add_value('firmware_version', meta_data['firmware_version'])
        loader.add_value('device_class', meta_data['device_class'])
        loader.add_value('release_date', meta_data['release_date'])

        yield loader.load_item()

    @staticmethod
    def map_device_class(device_name: str) -> str:
        return device_name

    @staticmethod
    def convert_date(date: str) -> str:
        day_month_year = date.split('/')
        day_month_year[0], day_month_year[1] = day_month_year[1], day_month_year[0]
        return '-'.join(['0' + digit if len(digit) < 2 else digit for digit in day_month_year])

    @staticmethod
    def extract_version(self) -> str:
        return str()
