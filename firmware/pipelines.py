from scrapy.pipelines.files import FilesPipeline


class FirmwarePipeline(object):
    def process_item(self, item, spider):
        return item

    def file_path(self, request, response=None, info=None):
        return request.url.split('/')[-1]


class AsusPipeline(FilesPipeline):

    def file_path(self, request, response=None, info=None):
        return request.url.split('/')[-1]

