from lxml.etree import HTML
from PIL import Image
import requests

# types
from PIL.PngImagePlugin import PngImageFile
from typing import Iterator


class WikiFlagScraper:

    def __init__(self):
        self.doc = None
        self.img_urls = None
        self.url_dict = None

    def get_pages(self):
        page_url = "https://en.wikipedia.org/wiki/Member_states_of_the_United_Nations"
        page = requests.get(page_url)
        self.doc = HTML(page.content)
        self.url_dict = self.make_mapping()

    def make_mapping(self) -> dict:
        return {
            x.attrib['alt']: f"https:{x.attrib['src']}"
            for x in self.doc.xpath('.//span[@class="flagicon"]/a/img')
        }

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
