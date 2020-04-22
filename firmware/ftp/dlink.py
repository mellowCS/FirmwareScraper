import json
import re
from datetime import datetime
from ftplib import FTP, error_perm

from os import mkdir, chdir, stat
from os.path import isdir as is_directory
from os.path import isfile as is_file


class FTPClass:
    def __init__(self, address):
        self.ftp_client = FTP(address)
        self.already_seen = ['fw', 'sw', 'rev', 'drv', 'code']
        self.json_file = list()
        self.files_skipped = {
            '@archive', 'anleitungen', 'D-Link_Assist_Anleitung.pdf', 'Hinweise Datenblaetter.txt',
            'Images_High_Resolution', 'Images_Low_Resolution', 'index_info.txt', 'Legal - Information',
            'Product_Images',
            'Product_Information_Material', 'self - service', 'software', 'Supportsystem_Anleitung_Mass_RMA.pdf',
            'Terms_and_Conditions', 'tmp', 'Warranty_Documents',
            # deprecated systems
            'ant24', 'ant70', 'dcf', 'de', 'dfw', 'dhd', 'dif', 'dm', 'dph', 'dvc', 'dvg', 'dvg', 'dta', 'dsn', 'dsm',
            'dns', 'dvs', 'dfl', 'dbt', 'dev', 'dcm', 'dgl', 'dhs', 'di', 'dws', 'dfe', 'du'
        }
        self.device_classes_dict = {
            'dba': 'Access Point', 'dap': 'Access Point',
            'dis': 'Converter', 'dmc': 'Converter',
            'dge': 'PCIe-Networkcard', 'dwa': 'PCIe-Networkcard', 'dxe': 'PCIe-Networkcard',
            'dps': 'Redundant Power Supply',
            'dsr': 'Router (Business)',
            'dwr': 'Router (mobile)', 'dwm': 'Router (mobile)',
            'dsl': 'Router (Modem)',
            'covr': 'Router (Home)', 'dir': 'Router (Home)', 'dva': 'Router (Home)', 'go': 'Router (Home)',
            'dsp': 'Smart Plug',
            'dcs': 'Smart Wi-Fi Camera', 'dsh': 'Smart Wi-Fi Camera',
            'des': 'Switch', 'dgs': 'Switch', 'dkvm': 'Switch', 'dqs': 'Switch', 'dxs': 'Switch',
            'dem': 'Transceiver',
            'dub': 'USB Extensions',
            'dnr': 'Video Recorder',
            'dwc': 'Wireless Controller',
            'dwl': 'other'
        }
        # for dwl: ap = Access Point, e = enterprise, s = small to medium business, g = SuperG?!, m = MIMO,
        # p = power over ethernet, plus = 802.11b+, ag = 802.11a and 802.11g, else PCIe, Adapter many more
        # go-plk = powerline connection, go-dsl = modem-router

    def main(self):
        print(self.ftp_client.login())
        try:
            for (directory_name, _) in self.start_iteration():
                if directory_name in self.files_skipped:
                    continue
                try:
                    self.ftp_client.cwd(directory_name)
                    self.get_subpage()
                    self.ftp_client.cwd('/')
                except error_perm as error:
                    self.logging(error)
                    continue
        except KeyboardInterrupt:
            print('shutting down slowly')
        finally:
            self.ftp_client.close()
            with open('dlink.json', mode='w') as file:
                json.dump(self.json_file, file)
                file.close()

    def get_subpage(self):

        for (directory_name, _) in self.start_iteration():
            try:
                self.ftp_client.cwd(directory_name)
                self.get_sub_subpage(directory_name)
                self.ftp_client.cwd('..')

            except error_perm as error:
                # trying to access file or permission denied
                self.logging(error)
                continue

    def get_sub_subpage(self, this_directory_name):
        for (new_directory, _) in self.start_iteration():
            if new_directory == 'driver_software':
                self.ftp_client.cwd('driver_software')
                self.download(this_directory_name)
                self.ftp_client.cwd('..')

    def download(self, device_name):

        for (file_name, file_details) in self.start_iteration():
            if not re.search('zip$', file_name) or (
                    is_file(file_name) and stat(file_name).st_size == file_details['size']):
                continue

            if '_fw_' in file_name:
                self.append_device_information(device_name, file_details, file_name)
                with open('{}'.format(file_name), 'wb') as file:
                    self.ftp_client.retrbinary('{} {}'.format('RETR', file_name), file.write)
                    file.close()
            if '_sw_' in file_name:  # software
                pass
            if '_rev' in file_name:  # revision?
                pass
            if '_drv_' in file_name:  # driver
                pass
            if 'code' in file_name:  # sourcecode
                pass

    def append_device_information(self, device_name, file_details, file_name):
        self.json_file.append(
            {'device_name': device_name,
             'vendor': 'D-Link',
             'firmware_version': self.extract_firmware_version(file_name),
             'device_class': self.extract_device_class(device_name),
             'release_date': self.extract_release_date(file_details),
             'file_urls': 'ftp://{}{}/{}'.format(self.ftp_client.host, self.ftp_client.pwd(), file_name)
             })

    def extract_device_class(self, device_name):
        try:
            device_initials = device_name.split('-')[0]
            device_class = self.device_classes_dict[device_initials]
            if device_initials == 'dwl' and 'ap' in device_name:
                device_class = 'Access Point'

        except Exception as error:
            device_class = None
            self.logging(error)
        return device_class

    def extract_release_date(self, file_details):
        try:
            release_date = datetime.timestamp(datetime.strptime(file_details['modify'], "%Y%m%d%H%M%S"))
        except Exception as error:
            release_date = None
            self.logging(error)
        return release_date

    def extract_firmware_version(self, file_name):
        try:
            firmware_version = file_name.split('_')[3]
        except Exception as error:
            firmware_version = None
            self.logging(error)
        return firmware_version

    def start_iteration(self):
        site_columns = self.ftp_client.mlsd()
        next(site_columns)
        next(site_columns)
        next(site_columns)
        return site_columns

    def logging(self, error):
        with open('0_logfile.txt', 'a') as logfile:
            logfile.write('Errormessage: {} \n Directory: {}\n'.format(error, self.ftp_client.pwd()))


if __name__ == '__main__':
    DOWNLOADS = 'firmware_files'
    if is_directory(DOWNLOADS):
        chdir(DOWNLOADS)
    else:
        mkdir(DOWNLOADS)
        chdir(DOWNLOADS)

    THIS = FTPClass('ftp.dlink.de')
    THIS.main()
