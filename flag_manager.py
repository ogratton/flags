from lxml.etree import HTML
from PIL import Image
import requests
import os

# for typing only
from PIL.PngImagePlugin import PngImageFile


class FlagManager:

    def __init__(self, high_res=False, force_update=False):
        """
        Note: force_update still uses the local flag_cache,
        it just goes via Wikipedia in case there's a new country :D
        """
        self.__high_res = high_res
        self.__res_str = 'hi' if self.__high_res else 'lo'
        self.__force_update = force_update
        self.__url_dict = None
        self.image_dict = self.__make_image_dict()

        if not self.image_dict:
            print("No cached items found, forcing update")
            self.__init__(high_res=high_res, force_update=True)

    def __make_image_dict(self) -> dict:
        if self.__force_update:
            # scrape-y scrape
            print("Downloading files from Wikipedia...")
            self.__url_dict = self.__make_url_dict()
            return {
                country: self.get_image(country)
                for country in self.__url_dict
            }
        else:
            # read-y read
            print("Reading files from local cache...")
            dir_path = os.path.dirname(os.path.realpath(__file__))
            path = f'{dir_path}/flag_cache/{self.__res_str}/'
            files = sorted(list(os.walk(path))[0][2])
            return {
                file_name[:-4]: Image.open(f"{path}{file_name}")
                for file_name in files
            }

    @staticmethod
    def __make_url_dict() -> dict:
        page_url = "https://en.wikipedia.org/wiki/Member_states_of_the_United_Nations"
        page = requests.get(page_url)
        doc = HTML(page.content)
        return {
            x.attrib['alt']: f"https:{x.attrib['src']}"
            for x in doc.xpath('.//span[@class="flagicon"]/a/img')
        }

    def get_image(self, country: str) -> PngImageFile:
        """
        Fetch the flag of a country
        """
        url = self.__url_dict[country]
        if self.__high_res:
            url = self.__get_high_res_url(country)

        file_path = f"flag_cache/{self.__res_str}/{country}.png"
        try:
            return Image.open(file_path)
        except IOError:
            print(f"> Getting Flag of {country}: {url}")
            return self.get_image_from_url(url, file_path)

    @staticmethod
    def get_image_from_url(url, file_path=None):
        response = requests.get(url, stream=True)
        response.raw.decode_content = True
        image = Image.open(response.raw)
        if file_path:
            image.save(file_path)
        return image

    @staticmethod
    def __get_high_res_url(country) -> str:
        """
        Fetch the larger version of the thumbnail
        Unfortunately, we can't just go straight to "/File:Flag_of_{country}"
        because (e.g.) R.O.Ireland doesn't follow the pattern. So we go via the
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
