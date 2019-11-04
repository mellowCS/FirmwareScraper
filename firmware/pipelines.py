from scrapy.pipelines.files import FilesPipeline


class HpPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None):
        return request.url.split('/')[-1]


class LinksysPipeline(HpPipeline):
    pass
