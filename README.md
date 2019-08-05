
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

All developed spiders should be contained in the folder

```
.../FirmwareScraper/firmware/spiders/
```

### Naming Convention

The name of the spider should contain the source in a meaningful way (e.g. When crawling netgear firmware, the spider's name could be netgear.py)

It is not necessary to add the key word 'spider' (e.g. netgear_spider.py) as it is already contained in the spiders folder and it would just inflate the module's name.



