from scrapy.pipelines.files import FilesPipeline


class LinksysPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None):
        return request.url.split('/')[-1]


class AvmPipeline(LinksysPipeline):
    pass
