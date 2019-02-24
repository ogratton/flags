from typing import NamedTuple, NewType, Tuple, Set, List, Iterator
from flag_manager import FlagManager
from operator import mul
from functools import reduce

# for typing only
from PIL.PngImagePlugin import PngImageFile


Colour = NewType('Colour', Tuple[int, int, int])


class FreqColour(NamedTuple):
    freq: int
    colour: Colour


class Flags:

    COLOURS = {
        # TODO the only problem with this now is these values
        # Could make a 3d visualisation of the colours we're using
        # This should define a range, not just a spot
        # Probably best not to pick "true" red, as dark red will be reported as black
        "red": Colour((200, 0, 0)),
        "green": Colour((0, 200, 0)),
        "blue": Colour((0, 0, 200)),
        "black": Colour((0, 0, 0)),
        "white": Colour((255, 255, 255)),
        "yellow": Colour((255, 255, 0)),
        "pink": Colour((255, 105, 180)),
        "orange": Colour((255, 165, 0)),
    }

    def __init__(self, high_res=False, threshold=5, force_update=False):
        self.flag_manager = FlagManager(high_res=high_res, force_update=force_update)
        self.threshold = threshold
        self.country_colours = dict()

    def get_all(self):
        for country, image in self.flag_manager.image_dict.items():
            self.country_colours[country] = self.get_colours_from_image(image, country)

    def get_one(self, country):
        return self.get_colours_from_image(self.flag_manager.image_dict[country], country)

    def get_colours_from_image(self, image: PngImageFile, country: str) -> Set[str]:
        # we set the colour profile to RGBA because PIL moans about transparency with RGB
        image = image.convert("RGBA")
        num_pixels = reduce(mul, image.size)
        img_colours = image.getcolors(num_pixels)
        if not img_colours:
            print(f"Could not get image colours for {country}")
            return set()
        # print(sorted(img_colours, key=lambda x: x[0], reverse=True))
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

    def test_one():
        flags = Flags(high_res=False, threshold=3)
        print(flags.get_one("Somalia"))

    def test_from_file():
        flags = Flags(high_res=False, threshold=3)
        from PIL import Image
        img = Image.open("flag_cache/23px-Flag_of_the_United_Kingdom.svg.png")
        print(flags.get_colours_from_image(img, "UK"))

    def test_all():
        hi_res = True
        thresh = 3
        results_fname = f"results_{'high' if hi_res else 'low'}_res_t={thresh}.txt"
        with open(results_fname, 'w+') as res_file:
            flags = Flags(high_res=hi_res, threshold=thresh)
            flags.get_all()
            print(*[f"{k}: {v}" for k, v in flags.country_colours.items()], sep='\n', file=res_file)

    test_all()
