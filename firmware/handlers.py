from json import dumps

from scrapy.core.downloader.handlers.ftp import FTPDownloadHandler
from scrapy.http import TextResponse
from twisted.protocols.ftp import FTPFileListProtocol

from firmware.custom_requests import FTPFileRequest

# Thanks to https://gearheart.io/articles/crawling-ftp-server-with-scrapy/


class FTPHandler(FTPDownloadHandler):

    def __init__(self, settings):
        self.result = None
        super().__init__(settings)

    def gotClient(self, client, request, filepath):
        # download file
        if isinstance(request, FTPFileRequest):
            return super().gotClient(client, request, filepath)

        # ftp listings
        proto = FTPFileListProtocol()
        return client.list(filepath, proto).addCallbacks(
            callback=self._build_response,
            callbackArgs=[request, proto],
            errback=self._failed,
            errbackArgs=[request],
        )

    def _build_response(self, result, request, protocol):
        # encode ftp listings in TextResponse JSON structure
        self.result = result
        return TextResponse(url=request.url, status=200, body=dumps(protocol.files), encoding='utf-8')
