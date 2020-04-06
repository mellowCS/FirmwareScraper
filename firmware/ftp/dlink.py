import re
from os import mkdir, chdir
from os.path import isdir as is_directory
from ftplib import FTP, error_perm


class FTPClass:
    def __init__(self, ftp_address, things_to_skip, thread_number, max_threads=10):
        self.ftp_client = FTP(ftp_address)
        self.things_to_skip = things_to_skip
        self.thread_number = thread_number
        self.max_threads = max_threads

    def main(self):
        print(self.ftp_client.login())
        for (directory_name, _) in self.start_iteration():
            print(directory_name)
            if directory_name in self.things_to_skip:
                continue
            try:
                self.ftp_client.cwd(directory_name)
                self.maintain_directory_tree(directory_name)
                self.get_subpage()
                break
            except error_perm:
                self.LOG(error_perm, directory_name)
                continue

        self.ftp_client.close()

    def get_subpage(self):
        skip_first_parameters = 3
        for (directory_name, _) in self.start_iteration():
            try:
                self.ftp_client.cwd(directory_name)
                self.maintain_directory_tree(directory_name)
                self.get_sub_subpage()
            except error_perm:
                # trying to access file or permission denied
                self.LOG(error_perm, directory_name)
                continue

    def get_sub_subpage(self):
        for (directory, _) in self.start_iteration():
            # archive, documentation, driver_software
            if 'driver_software' == directory:
                self.ftp_client.cwd(directory)
                self.get_directory()

    def get_directory(self):

        for (file_name, file_details) in self.start_iteration():
            # skip the file, if it ends with 'pdf' or 'txt'
            if re.search('pdf$|txt$', file_name):
                continue
            # todo check if file already exists?
            if 'code' in file_name:
                # todo put into json
                pass
            if 'fw' in file_name:
                # todo put into json
                pass
            if 'sw' in file_name:
                # todo skip or put into json
                pass
            if 'rev' in file_name:
                # todo put revision number into json?
                pass

            with open('{}'.format(file_name), 'wb') as filepath:
                self.ftp_client.retrbinary('{} {}'.format('RETR', file_name), filepath)
                filepath.close()
        self.go_to_main_directory()

    def start_iteration(self):
        # skip until @archive
        site_columns = self.ftp_client.mlsd()
        next(site_columns)
        next(site_columns)
        next(site_columns)
        return site_columns

    def go_to_main_directory(self):
        while self.ftp_client.pwd() != '/':
            self.ftp_client.cwd('..')

    @staticmethod
    def LOG(error, directory_name):
        with open('logfile.txt', 'a') as logfile:
            logfile.write('Errormessage: {} \n Directory: {}\n'.format(error, directory_name))

    @staticmethod
    def maintain_directory_tree(directory_name):
        if is_directory(directory_name):
            chdir(directory_name)
        else:
            mkdir(directory_name)
            chdir(directory_name)


if __name__ == '__main__':
    ftp_address = 'ftp.dlink.de'

    things_to_skip = {
        '@archive',
        'anleitungen',
        'ant24', 'ant70',  # Antennen - keine Firmware vorhanden, soweit die manuelle Prüfung es ergeben hat
        'D-Link_Assist_Anleitung.pdf',
        'Hinweise Datenblaetter.txt',
        'Images_High_Resolution',
        'Images_Low_Resolution',
        'index_info.txt',
        'Legal - Information',
        'Product_Images',
        'Product_Information_Material',
        'self - service',
        'software',
        'Supportsystem_Anleitung_Mass_RMA.pdf',
        'Terms_and_Conditions',
        'tmp',
        'Warranty_Documents'
    }
    # todo start threads here? maybe skip every 1,2,3,4 and so on OR do it with a queue
    # get element from queue, check for things to skip, get new one or connect
    name_dictionary = {}
    for name in {'covr', 'dgl', 'dir', 'dva'}:  # covr = smart home, dir = mesh? dva = HorstBox
        name_dictionary[name] = 'Router (Home)'
    for name in {'dsr'}:
        name_dictionary[name] = 'Router (Business)'
    for name in {'dcm', 'dsl'}:
        name_dictionary[name] = 'Router (Modem)'
    for name in {'dwr'}:
        name_dictionary[name] = 'Router (mobile)'
    for name in {'dba', 'dap', 'dwl'}:
        name_dictionary[name] = 'Access Point'
    for name in {}:
        name_dictionary[name] = 'Wireless Controller'
    for name in {}:
        name_dictionary[name] = 'Repeater'
    for name in {'des', 'dgs', 'dhs', 'di', 'dkvm', 'dqs'}:  # dkvm = kvm switch, dqs = enterprise data center switch
        name_dictionary[name] = 'Switch'
    for name in {'dev'}:
        name_dictionary[name] = 'Bridge'
    for name in {}:
        name_dictionary[name] = 'USB-Networkcard'
    for name in {'dfe', 'dge'}:
        name_dictionary[name] = 'PCIe-Networkcard'
    for name in {'dbt'}:
        name_dictionary[name] = 'Bluetooth-Adapter'
    for name in {'dnc', 'cwm', 'ds', 'dv'}:
        name_dictionary[name] = 'Software'
    for name in {'dcf', 'de', 'dfw', 'dhd', 'dif'}:
        # todo outdated:
        #  dcf = 'bt' = bluetooth, 'w' = wireless-Adapter,
        #  de = ethernetcable-adapter
        #  dfw = PCI Adapter
        #  dhd = TV-Wifi-Adapter zum streamen
        #  dif = _
        #  dm = _
        #  dph = phone/phone adapter
        #  dvc = videophone
        #  dvg = VoIP Station Gateway?
        # TODO DVG last one!
        name_dictionary[name] = 'Wi-Fi Water Sensor'
    for name in {'dcs', 'dsh'}:
        name_dictionary[name] = 'Smart Wi-Fi Camera'
    for name in {'dem'}:
        name_dictionary[name] = 'Transceiver'
    for name in {'dfl'}:  # "NetDefend
        name_dictionary[name] = 'Business Firewall'
    for name in {'dis', 'dmc'}:
        name_dictionary[name] = 'Converter'  # ethernet, media etc. glasfaser zu trashfaser
    for name in {'dnr'}:
        name_dictionary[name] = 'Video Recorder'
    for name in {'dns'}:
        name_dictionary[name] = 'Network Attached Storage'
    for name in {'dps'}:
        name_dictionary[name] = 'Redundant Power Supply'
    for name in {'dsm'}:
        name_dictionary[name] = 'Media Player'
    for name in {'dsn'}:
        name_dictionary[name] = 'Storage Array'
    for name in {'dsp'}:
        name_dictionary[name] = 'Smart Powr Supply'
    for name in {'dta'}:
        name_dictionary[name] = 'ISDN Card'
    for name in {'du', 'dub'}:  # PCI card & extern & card
        name_dictionary[name] = 'USB Extensions'

    # create own Downloads directory
    FTPClass.maintain_directory_tree('firmware_files')

    max_thread = 1
    for number in range(max_thread):
        working_class = FTPClass(ftp_address, things_to_skip, thread_number=number + 1, max_threads=max_thread)
        working_class.main()
