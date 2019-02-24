from urllib.parse import unquote
from lxml.etree import HTML
from PIL import Image
import requests
import string
import re

# types
from PIL.PngImagePlugin import PngImageFile
from typing import Iterator


class WikiFlagScraper:

    def __init__(self):
        self.doc = None
        self.img_urls = None
        self.url_dict = None

    def get_pages(self):
        page_url = "https://en.wikipedia.org/wiki/List_of_sovereign_states"
        page = requests.get(page_url)
        self.doc = HTML(page.content)
        self.img_urls = self.get_img_urls()
        self.url_dict = self.make_mapping()

    def get_img_urls(self) -> Iterator[str]:
        return map(lambda x: f"https:{x.attrib['src']}", self.doc.xpath('.//span[@class="flagicon"]/img'))

    def make_mapping(self) -> dict:
        """
        Make dict of country name -> image url
        """
        url_dict = dict()
        for url in self.img_urls:
            url_str = unquote(url)
            name = re.search(r'Flag_of_(.*?)\.svg', url_str).group(1)
            # a few hacky things to clean up
            name = string.capwords(name.replace('_', ' '))
            if name[-1] == ')':
                name = ' '.join(name.split()[:-1])
            if name.startswith("The "):
                name = name[4:]

            url_dict[name] = url
        return url_dict

    def get_image(self, country: str, high_res=False) -> PngImageFile:
        """
        Fetch the flag of a country
        """
        # TODO On KeyError, try and fetch from wiki
        url = self.url_dict[country]
        if high_res:
            url = url.replace('23px', '1024px')

        print(f"> Getting Flag of {country}: {url}")
        return self.get_image_from_url(url)

    @classmethod
    def get_image_from_url(cls, url) -> PngImageFile:
        """
        Actually get the image
        Separated for testing purposes
        """
        response = requests.get(url, stream=True)
        response.raw.decode_content = True
        return Image.open(response.raw)
