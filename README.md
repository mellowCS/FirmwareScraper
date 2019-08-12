
# FirmwareScraper
The FirmwareScraper is able to scrape firmware from multiple vendor webpages using the scrapy library

## Installation

### Ubuntu 14.04 and above

Some packages need to be installed using apt-get/apt before installing scrapy

```
sudo apt-get install python-dev python-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev
```

As python 2 is almost at EOL, python3 additionally needs python3-dev

```
sudo apt-get install python3 python3-dev
```

Scrapy can then be installed using the following command:

```
pip install scrapy
```

For more information about the installation process of scrapy, [see here.](https://docs.scrapy.org/en/latest/intro/install.html#intro-install)

## Use

To use the existing scrapy project, just clone it into a repository of your choice

```
git clone https://github.com/mellowCS/FirmwareScraper.git
```

To run a spider, just go into the project's folder and type the following command into the terminal:

```
scrapy crawl *name of spider*
```

## Developer

All developed spiders and corresponding tests should be contained in the folders

```
.../FirmwareScraper/firmware/spiders/
.../FirmwareScraper/firmware/tests/
```

### File Download

For the file download, scrapy's file pipline is activated in settings.py. To store the files, a valid path has to be added

```
ITEM_PIPELINES = {
    'scrapy.pipelines.files.FilesPipeline': 1
}

FILES_STORE = 'valid/path/to/files/'
```

Additionally, the necessary fields are added to the FirmwareItem class in the items.py

```
class FirmwareItem(scrapy.Item):
    file_urls = scrapy.Field()
    files = scrapy.Field()
```

To add files to the pipeline use the following commands in the spider class

```
for url in ...:
    loader = ItemLoader(item=FirmwareItem(), selector=url)
    loader.add_value('file_urls', url)
    yield loader.load_item()
```

The scrapy script will then automatically download all the files in the pipeline.

To automatically create a json file while downloading the corresponding files, the spider has to be run with the following command

```
scrapy crawl *name of spider* -o file_name.json
```

The json file gets populated with the values added to the Field() variables of the Item class specified in the ItemLoader. See the pipeline example above.

### Naming Convention

The name of the spider should contain the source in a meaningful way (e.g. When crawling netgear firmware, the spider's name could be netgear.py)

It is not necessary to add the key word 'spider' (e.g. netgear_spider.py) as it is already contained in the spiders folder and it would just inflate the module's name.



