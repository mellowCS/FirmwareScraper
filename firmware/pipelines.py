import os
from hashlib import sha256

from scrapy.pipelines.files import FilesPipeline


class StoreFirmwarePipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        hashsum = sha256(response.body).hexdigest()
        path = [hashsum[:2], hashsum[2:4], hashsum[4:]]
        print("OutPath", os.path.join(*path))
        return os.path.join(*path)

class FirmwarePipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None):
        return request.url.split('/')[-1]


class HpPipeline(FirmwarePipeline):
    pass


class LinksysPipeline(FirmwarePipeline):
    pass


class AvmPipeline(FirmwarePipeline):
    pass


class AsusPipeline(FirmwarePipeline):
    pass
