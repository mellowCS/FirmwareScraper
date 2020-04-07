import json
import re
from datetime import datetime
from os import mkdir, chdir, stat
from os.path import isdir as is_directory
from os.path import isfile as is_file
from ftplib import FTP, error_perm


class FTPClass:
    def __init__(self, ftp_address, things_to_skip, device_classes, thread_number, max_threads=10):
        self.ftp_client = FTP(ftp_address)
        self.things_to_skip = things_to_skip
        self.device_classes_dict = device_classes
        self.thread_number = thread_number
        self.max_threads = max_threads
        self.already_seen = ['fw', 'sw', 'rev', 'drv', 'code']
        self.json_file = list()

    def main(self):
        print(self.ftp_client.login())
        try:
            for (directory_name, _) in self.start_iteration():
                if directory_name in self.things_to_skip:
                    continue
                # try:
                self.ftp_client.cwd(directory_name)
                self.get_subpage(directory_name)
                self.ftp_client.cwd('/')
                # except error_perm:
                #    self.LOG(error_perm, directory_name)
                #    continue
        except KeyboardInterrupt:
            print('shutting down slowly')
        finally:
            self.ftp_client.close()
            with open('dlink.json', mode='w') as f:
                json.dump(self.json_file, f)
                f.close()

    def get_subpage(self, this_directory_name):

        for (new_directory_name, _) in self.start_iteration():
            # try:
            self.ftp_client.cwd(new_directory_name)
            self.get_sub_subpage(new_directory_name)
            self.ftp_client.cwd('..')

            # except error_perm:
            #    # trying to access file or permission denied
            #    self.LOG(error_perm, new_directory_name)
            #    continue

    def get_sub_subpage(self, this_directory_name):
        for (new_directory, _) in self.start_iteration():
            # archive, documentation, driver_software
            if 'driver_software' == new_directory:
                self.ftp_client.cwd('driver_software')
                self.download_directory(this_directory_name)
                self.ftp_client.cwd('..')

    def download_directory(self, device_name):

        for (file_name, file_details) in self.start_iteration():
            if not re.search('zip$', file_name) or (
                    is_file(file_name) and stat(file_name).st_size == file_details['size']):
                continue

            if '_fw_' in file_name:
                try:
                    device_initials = device_name.split('-')[0]
                    device_class = self.device_classes_dict[device_initials]
                    if device_initials == 'dwl' and 'ap' in device_name:
                        device_class = 'Access Point'
                except Exception as e:
                    device_class = None
                    self.LOG(e)
                try:
                    release_date = datetime.timestamp(datetime.strptime(file_details['modify'], "%Y%m%d%H%M%S"))
                except Exception as e:
                    release_date = None
                    self.LOG(e)
                try:
                    firmware_version = file_name.split('_')[3]
                except Exception as e:
                    firmware_version = None
                    self.LOG(e)

                self.json_file.append(
                    {'device_name': device_name,
                     'vendor': 'D-Link',
                     'firmware_version': firmware_version,
                     'device_class': device_class,
                     'release_date': release_date,
                     'file_urls': 'ftp://{}{}/{}'.format(self.ftp_client.host, self.ftp_client.pwd(), file_name)
                     })

                with open('{}'.format(file_name), 'wb') as filepath:
                    self.ftp_client.retrbinary('{} {}'.format('RETR', file_name), filepath.write)
                    filepath.close()
            if '_sw_' in file_name:  # software
                pass
            if '_rev' in file_name:  # revision?
                pass
            if '_drv_' in file_name:  # driver
                pass

    def start_iteration(self):
        # skip until @archive
        site_columns = self.ftp_client.mlsd()
        next(site_columns)
        next(site_columns)
        next(site_columns)
        return site_columns

    def LOG(self, error):
        with open('logfile.txt', 'a') as logfile:
            logfile.write('Errormessage: {} \n Directory: {}\n'.format(error, self.ftp_client.pwd()))


if __name__ == '__main__':
    ftp_address = 'ftp.dlink.de'

    things_to_skip = {
        '@archive', 'anleitungen', 'D-Link_Assist_Anleitung.pdf', 'Hinweise Datenblaetter.txt',
        'Images_High_Resolution', 'Images_Low_Resolution', 'index_info.txt', 'Legal - Information', 'Product_Images',
        'Product_Information_Material', 'self - service', 'software', 'Supportsystem_Anleitung_Mass_RMA.pdf',
        'Terms_and_Conditions', 'tmp', 'Warranty_Documents',
        # deprecated systems
        'ant24', 'ant70', 'dcf', 'de', 'dfw', 'dhd', 'dif', 'dm', 'dph', 'dvc', 'dvg', 'dvg', 'dta', 'dsn', 'dsm',
        'dns', 'dvs', 'dfl', 'dbt', 'dev', 'dcm', 'dgl', 'dhs', 'di', 'dws', 'dfe', 'du'
    }

    name_dictionary = {
        'dsr': 'Router (Business)', 'dwc': 'Wireless Controller', 'dsl': 'Router (Modem)', 'dnr': 'Video Recorder',
        'dps': 'Redundant Power Supply', 'dsp': 'Smart Plug', 'dub': 'USB Extensions', 'dem': 'Transceiver',
        'dwl': 'Wireless LAN'
    }
    # for dwl: ap = Access Point, e = enterprise, s = small to medium business, g = SuperG?!, m = MIMO,
    # p = power over ethernet, plus = 802.11b+, ag = 802.11a and 802.11g, else PCIe, Adapter many more

    for name in {'covr', 'dir', 'dva', 'go'}:  # go-plk = powerline connection, go-dsl = modem-router
        name_dictionary[name] = 'Router (Home)'
    for name in {'dwr', 'dwm'}:
        name_dictionary[name] = 'Router (mobile)'
    for name in {'dba', 'dap', 'dwl'}:
        name_dictionary[name] = 'Access Point'
    for name in {'des', 'dgs', 'dkvm', 'dqs', 'dxs'}:
        name_dictionary[name] = 'Switch'
    for name in {'dge', 'dwa', 'dxe'}:
        name_dictionary[name] = 'PCIe-Networkcard'
    for name in {'dnc', 'cwm', 'ds', 'dv'}:
        name_dictionary[name] = 'Software'
    for name in {'dcs', 'dsh'}:
        name_dictionary[name] = 'Smart Wi-Fi Camera'
    for name in {'dis', 'dmc'}:
        name_dictionary[name] = 'Converter'

    downloads_directory = 'firmware_files'
    if is_directory(downloads_directory):
        chdir(downloads_directory)
    else:
        mkdir(downloads_directory)
        chdir(downloads_directory)

    # todo start threads here? maybe skip every 1,2,3,4 and so on OR do it with a queue
    #  get element from queue, check for things to skip, get new one or connect

    max_thread = 1
    for number in range(max_thread):
        working_class = FTPClass(ftp_address, things_to_skip, name_dictionary, thread_number=number + 1,
                                 max_threads=max_thread)
        working_class.main()
