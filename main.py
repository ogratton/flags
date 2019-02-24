from typing import NamedTuple, NewType, Tuple, Set, List, Iterator
from scrape_flags import WikiFlagScraper
from math import sqrt
from operator import mul
from functools import reduce


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

    def __init__(self, test=False):
        self.wiki_flags = WikiFlagScraper()
        if not test:
            self.wiki_flags.get_pages()

    def get_colours(self, country, high_res=True, url=None) -> Set[str]:
        if url:
            # for testing
            image = WikiFlagScraper.get_image_from_url(url)
        else:
            # we get the high-res images to minimise artifacts that mess with colours
            image = self.wiki_flags.get_image(country, high_res=high_res)

        # we set the colour profile to RGBA because PIL moans about transparency with RGB
        image = image.convert("RGBA")
        num_pixels = reduce(mul, image.size)
        freq_colours = [FreqColour(f, Colour(c[:3])) for f, c in image.getcolors()]
        colours = self._reduce_colours(freq_colours, num_pixels)
        return colours

    def _reduce_colours(self, freq_colours: List[FreqColour], num_pixels) -> Set[str]:
        """
        We don't really care how many shades of red we have
        (especially as these are likely png artifacts),
        just that there is some
        """
        colours = set()
        most_common_colours = self._remove_likely_artifacts(freq_colours, num_pixels)
        for freq_colour in most_common_colours:
            colours.add(self._reduce_colour(freq_colour))
        return colours

    def _reduce_colour(self, freq_colour: FreqColour) -> str:
        min_dist = (256**3, None)
        for colour_name, colour_value in self.COLOURS.items():
            distance = self._distance(colour_value, freq_colour.colour)
            if distance < min_dist[0]:
                min_dist = (distance, colour_name)
        return min_dist[1]

    @staticmethod
    def _remove_likely_artifacts(freq_colours: List[FreqColour], num_pixels, threshold=1) -> Iterator[FreqColour]:
        """
        Filter out colours that only occur less than 1% of the time
        """
        min_occurrences = num_pixels * (threshold/100)
        return filter(lambda x: x.freq > min_occurrences, freq_colours)

    @staticmethod
    def _distance(c1: Colour, c2: Colour) -> float:
        return sqrt(sum([abs(x-y) for x, y in zip(c1, c2)]))


if __name__ == "__main__":

    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Canada_%28Pantone%29.svg/1024px-Flag_of_Canada_%28Pantone%29.svg.png"

    flags = Flags(test=False)
    print(flags.get_colours("Ireland"))
