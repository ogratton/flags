from typing import NamedTuple, NewType, Tuple, Set, List, Iterator
from scrape_flags import WikiFlagScraper
from operator import mul
from functools import reduce
import os


TEST = os.environ.get("TEST")


Colour = NewType('Colour', Tuple[int, int, int])


class FreqColour(NamedTuple):
    freq: int
    colour: Colour


class Flags:

    COLOURS = {
        "red": Colour((255, 0, 0)),
        "green": Colour((0, 255, 0)),
        "blue": Colour((0, 0, 255)),
        "black": Colour((0, 0, 0)),
        "white": Colour((255, 255, 255)),
        "yellow": Colour((255, 255, 0)),
        "pink": Colour((255, 105, 180)),
        "orange": Colour((255, 165, 0)),
    }

    def __init__(self, high_res=False, threshold=5):
        self.wiki_flags = WikiFlagScraper()
        if not TEST:
            self.wiki_flags.get_pages()
            print(*self.wiki_flags.url_dict.keys(), sep='\n')
        self.high_res = high_res
        self.threshold = threshold

    def get_all(self):
        for country in self.wiki_flags.url_dict:
            self.get_colours(country)

    def get_colours(self, country, test_url=None) -> Set[str]:
        if TEST and test_url:
            image = WikiFlagScraper.get_image_from_url(test_url)
        else:
            # we get the high-res images to minimise artefacts that mess with colours
            image = self.wiki_flags.get_image(country, high_res=self.high_res)

        # we set the colour profile to RGBA because PIL moans about transparency with RGB
        image = image.convert("RGBA")
        num_pixels = reduce(mul, image.size)
        print(num_pixels)
        img_colours = image.getcolors()
        if not img_colours:
            raise ValueError(f"Could not get image colours for {country}")
        freq_colours = [FreqColour(f, Colour(c[:3])) for f, c in img_colours]
        colours = self._reduce_colours(freq_colours, num_pixels)
        return colours

    def _reduce_colours(self, freq_colours: List[FreqColour], num_pixels) -> Set[str]:
        """
        We don't really care how many shades of red we have
        (especially as these are likely compression artefacts),
        just that there is some
        """
        colours = set()
        most_common_colours = self._remove_likely_artefacts(freq_colours, num_pixels)
        for freq_colour in most_common_colours:
            colours.add(self._reduce_colour(freq_colour))
        return colours

    def _reduce_colour(self, freq_colour: FreqColour) -> str:
        return min(
            (
                ((self._distance(freq_colour.colour, col_val)), col_name)
                for col_name, col_val in self.COLOURS.items()
            ),
            key=lambda x: x[0]
        )[1]
        # More traditional way of doing this:
        # min_dist = (1e10, None)
        # for colour_name, colour_value in self.COLOURS.items():
        #     distance = self._sq_distance(colour_value, freq_colour.colour)
        #     if distance < min_dist[0]:
        #         min_dist = (distance, colour_name)
        # return min_dist[1]

    def _remove_likely_artefacts(self, freq_colours: List[FreqColour], num_pixels) -> Iterator[FreqColour]:
        """
        Filter out colours that only occur less than 1% of the time
        as these are probably compression artefacts
        """
        min_occurrences = num_pixels * (self.threshold/100)
        return filter(lambda x: x.freq > min_occurrences, freq_colours)

    @staticmethod
    def _distance(c1: Colour, c2: Colour) -> float:
        """
        Euclidean square distance (but with abs instead)
        We don't care about the actual distance, only
        relative comparisons, so we don't sqrt as it's
        slow. Squaring is also slower than abs (maybe)
        """
        return sum([abs(x-y) for x, y in zip(c1, c2)])


if __name__ == "__main__":

    canada_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Canada_%28Pantone%29.svg/1024px-Flag_of_Canada_%28Pantone%29.svg.png"

    flags = Flags(high_res=True, threshold=10)
    print(flags.get_colours("Ukraine"))
