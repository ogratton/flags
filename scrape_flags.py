from lxml.etree import HTML
from PIL import Image
import requests

# for typing only
from PIL.PngImagePlugin import PngImageFile


def cached_to_file(f):
    """
    Write the flags to disk so we don't have to download every time
    This is overfitted for purpose, could be made more general
    """
    def wrapper(cls, url):
        filepath = f"flag_cache/{url.split('/')[-1]}"
        try:
            return Image.open(filepath)
        except IOError:
            image = f(cls, url)
            # save image to disk for later
            image.save(filepath)
            return image
    return wrapper


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
            url = self.get_high_res_url(country)

        print(f"> Getting Flag of {country}: {url}")
        return self.get_image_from_url(url)

    def get_high_res_url(self, country) -> str:
        """
        Fetch the larger version of the thumbnail
        Unfortunately, we can't just go straight to "/File:Flag_of_{country}"
        because (e.g.) Ireland doesn't follow the pattern. So we go via the
        actual wiki pages and trust the wiki redirect system
        """
        wiki_stem = "https://en.wikipedia.org"
        country_page = requests.get(f"{wiki_stem}/wiki/{country}")
        country_doc = HTML(country_page.content)
        [v_card] = country_doc.xpath('.//table[@class="infobox geography vcard"]')
        [flag_elem] = v_card.xpath('.//a[@class="image" and contains(@title, "Flag")]')
        flag_page_url = f"{wiki_stem}{flag_elem.attrib['href']}"
        flag_page = requests.get(flag_page_url)
        doc = HTML(flag_page.content)
        [flag_url_elem] = doc.xpath('.//div[@id="file"]/a/img')
        return f"https:{flag_url_elem.attrib['src']}"

    @classmethod
    @cached_to_file
    def get_image_from_url(cls, url) -> PngImageFile:
        """
        Actually get the image
        Separated for testing purposes
        """
        response = requests.get(url, stream=True)
        response.raw.decode_content = True
        return Image.open(response.raw)
