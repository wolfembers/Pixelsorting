# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from string import ascii_lowercase, ascii_uppercase, digits
from typing import List, Tuple, Any, Callable
from datetime import datetime
from colorsys import rgb_to_hsv
import random as rand
import argparse
import os
import socket
import json

from PIL import Image, ImageFilter
from requests import get, post
from tqdm import tqdm
import numpy as np


# MISC FUNCTIONS #
def clear():  # clear screen
    return os.system("cls" if os.name == "nt" else "clear")


def has_internet(host: str, port: int, timeout: int) -> bool:
    """
    Checks for internet.
    ------
    :param host: 8.8.8.8 (google-public-dns-a.google.com)
    :param port: 53
    :param timeout: 3

    Service: domain (DNS/TCP)

    Examples
    ------
    >>> internet = has_internet("8.8.8.8", 53, 3)
    >>> print(internet)
    True
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def parse_args_full(
    url: str,
    int_func_input: str,
    sort_func_input: str,
    arg_parse_input: list,
    internet: bool,
) -> List[Any]:
    """
    Combining the misc. args.
    -----
    :param url: The inputted URL, number of default image, or local file path.
    :param int_func_input: The interval function used.
    :param sort_func_input: The sorting function used.
    :param arg_parse_input: Other args (angle, char. length, etc.)
    :param internet: true/false for having internet.
    :returns: List of args.
    """
    full_args = []  # type: List
    full_args.append("-l " + url)
    full_args.append("-i " + int_func_input)
    full_args.append("-s " + sort_func_input)
    full_args.append("-y " + str(internet))
    full_args += arg_parse_input
    return full_args


def PixelAppend(size1: int, size0: int, data: Any, msg: str) -> List:
    """
    Making a 3D array of pixel values from a PIL image.
    -----
    :param size1: img.size[1]/height
    :param size0: img.size[0]/width
    :param data: PixelAccess object from img.load()
    :param msg: Message for the progress bar
    :returns: 3D array of pixel values.

    Example
    -----
    >>> pixels = PixelAppend(size1, size0, data, "Appending")
    """
    pixels = []  # type: List
    for y in ProgressBars(size1, msg):
        Append(pixels, [])
        for x in range(size0):
            AppendDataPIL(pixels, x, y, data)
    return pixels


def elementary_ca() -> Tuple[Any,str]:
    """
    Generate images of elementary cellular automata.
    ------
    :returns: PIL Image object.
    """
    width = rand.randrange(300, 500, 5)  # type: int
    height = rand.randrange(300, 500, 5)  # type: int
    rulenumber = rand.randrange(10, 30)  # type: int
    scalefactor = rand.randrange(1, 5)  # type: int
    msg = f'Width: {width}||Height: {height}||Rule #: {rulenumber}||Scale: {scalefactor}'

    # Define colors of the output image
    true_pixel = (255, 255, 255)  # type: Tuple[int, int, int]
    false_pixel = (0, 0, 0)  # type: Tuple[int, int, int]

    # Generates a dictionary that tells you what your state should be based on the rule number
    # and the states of the adjacent cells in the previous generation
    def generate_rule(rulenumber: int) -> dict:
        rule = {}  # type: dict
        for left in [False, True]:
            for middle in [False, True]:
                for right in [False, True]:
                    rule[(left, middle, right)] = rulenumber % 2 == 1
                    rulenumber //= 2
        return rule

    # Generates a 2d representation of the state of the automaton at each generation
    def generate_ca(rule: dict) -> List:
        ca = []  # type: List
        # Initialize the first row of ca randomly
        Append(ca, [])
        for x in range(width):
            AppendPartial(ca, 0, bool(rand.getrandbits(1)))

        # Generate the succeeding generation
        # Cells at the eges are initialized randomly
        for y in range(1, height):
            Append(ca, [])
            AppendPartial(ca, y, bool(rand.getrandbits(1)))
            for x in range(1, width - 1):
                AppendPartial(
                    ca, y, (rule[(ca[y - 1][x - 1], ca[y - 1][x], ca[y - 1][x + 1])])
                )
            AppendPartial(ca, y, bool(rand.getrandbits(1)))
        return ca

    rule = generate_rule(rulenumber)
    ca = generate_ca(rule)

    newImg = Image.new("RGB", [width, height])

    print("Creating file image...")
    for y in ProgressBars(height, "Placing pixels..."):
        for x in range(width):
            newImg.putpixel(
                (x, y),
                true_pixel
                if ca[int(y / scalefactor)][int(x / scalefactor)]
                else false_pixel,
            )

    print("File image created!")
    newImg.save("elementary_ca.png")
    return newImg, msg


black_pixel = (0, 0, 0, 255)  # type: Tuple[int, int, int, int]
white_pixel = (255, 255, 255, 255)  # type: Tuple[int, int, int, int]

# LAMBDA FUNCTIONS #
ImgOpen = lambda u, i: (Image.open((get(u, stream=True).raw) if i else u)).convert(
    "RGBA"
)  # type: Callable[[str, bool], Any]
Append = lambda l, obj: l.append(obj)  # type: Callable[[Any, Any], Any]
AppendDataPIL = lambda l, x, y, d: l[y].append(
    d[x, y]
)  # type: Callable[[List, int, int, Any], List]
AppendDataList = lambda l, x, y, d: l.append(
    d[y][x]
)  # type: Callable[[List, int, int, Any], Any]
AppendPartial = lambda l, y, x: l[y].append(x)  # type: Callable[[List, int, Any], List]
ImgPixels = lambda img, x, y, data: img.putpixel(
    (x, y), data[y][x]
)  # type: Callable[[Any, int, int, Any], Any]
RandomWidth = lambda c: int(c * (1 - rand.random()))  # type: Callable[[int], int]
ProgressBars = lambda r, d: tqdm(
    range(r), desc=("{:30}".format(d))
)  # type: Callable[[Any, str], Any]
AppendBW = (
    lambda l, x, y, d, t: AppendPartial(l, y, white_pixel)
    if (lightness(d[y][x]) < t)
    else AppendPartial(l, y, black_pixel)
)  # type: Callable[[List, int, int, Any, float], List]


# SORTING PIXELS #
lightness = (
    lambda p: rgb_to_hsv(p[0], p[1], p[2])[2] / 255.0
)  # type: Callable[[Any], float]
intensity = lambda p: p[0] + p[1] + p[2]  # type: Callable[[Any], float]
hue = lambda p: rgb_to_hsv(p[0], p[1], p[2])[0] / 255.0  # type: Callable[[Any], float]
saturation = (
    lambda p: rgb_to_hsv(p[0], p[1], p[2])[1] / 255.0
)  # type: Callable[[Any], float]
minimum = lambda p: min(p[0], p[1], p[2])  # type: Callable[[Any], float]


# READING FUNCTIONS #
def read_image_input(url_input: str, internet: bool) -> Tuple[str, bool, bool, Any]:
    """
    Reading the image input.
    -----
    :param url_input: The inputted URL, number of default image, or local file path.
    :param internet: true/false for having internet.
    :returns: (in order) url[str], url_given[bool], url_random[bool], random_url[str]
    """
    try:
        if internet:
            if url_input in ["", " ", "0", "1", "2", "3", "4", "5", "6"]:
                raise IOError
            else:
                ImgOpen(url_input, internet)
                return url_input, True, False, None
        else:
            if url_input in ["", " "]:
                url = "images/default.jpg"
            else:
                url = url_input
            return url, True, False, False
    except IOError:
        random_url = str(rand.randint(0, 5))
        url_options = {
            "0": "https://s.put.re/TKnTHivM.jpg",
            "1": "https://s.put.re/Ds9KV8jX.jpg",
            "2": "https://s.put.re/QsUQbC1R.jpg",
            "3": "https://s.put.re/5zgcV3TT.jpg",
            "4": "https://s.put.re/567w8wpK.jpg",
            "5": "https://s.put.re/gcYkpmbd.jpg",
            "6": "https://s.put.re/AXipZo53.jpg",
        }
        try:
            return (
                (
                    url_options[
                        (
                            url_input
                            if url_input in ["0", "1", "2", "3", "4", "5", "6"]
                            else random_url
                        )
                    ]
                    if url_input in ["", " ", "0", "1", "2", "3", "4", "5", "6"]
                    else url_input
                ),
                (
                    False
                    if url_input in ["", " ", "0", "1", "2", "3", "4", "5", "6"]
                    else True
                ),
                (True if url_input in ["", " "] else False),
                (random_url if url_input in ["", " "] else None),
            )
        except KeyError:
            return url_options[random_url], False, True, random_url


def read_interval_function(int_func_input: str) -> Any:
    """
    Reading the interval function.
    -----
    :param int_func_input: A (lowercase) string.
    :returns: Interval function.
    :raises KeyError: String not in selection.

    Example
    -----
    >>> interval = read_interval_function("random")
    >>> print(interval)
    function<random>
    """
    try:
        return {
            "random": random,
            "threshold": threshold,
            "edges": edge,
            "waves": waves,
            "snap": snap_sort,
            "file": file_mask,
            "file-edges": file_edges,
            "shuffle-total": shuffle_total,
            "shuffle-axis": shuffled_axis,
            "none": none,
        }[int_func_input]
    except KeyError:
        return random


def read_sorting_function(sort_func_input: str) -> Any:
    """
    Reading the sorting function.
    -----
    :param sort_func_input: A (lowercase) string.
    :returns: Sorting function.
    :raises KeyError: String not in selection.

    Example
    -----
    >>> sortFunc = read_sorting_function("hue")
    >>> print(sortFunc)
    lambda<hue>
    """
    try:
        return {
            "lightness": lightness,
            "hue": hue,
            "intensity": intensity,
            "minimum": minimum,
            "saturation": saturation,
        }[sort_func_input]
    except KeyError:
        return lightness


def read_preset(
    preset_input: str
) -> Tuple[str, str, str, bool, bool, bool, bool, bool, bool]:
    """
    Returning values for 'presets'.
    -----
    :param preset_input: A (lowercase) string.
    :returns: (in order) arg_parse_input, int_func_input, sort_func_input, preset_true, int_rand, sort_rand, shuffled, snapped, file_sorted
    :raises KeyError: String not in selection.
    """
    try:
        # order-- arg_parse_input, int_func_input, sort_func_input, preset_true, int_rand, sort_rand, shuffled, snapped
        int_func_input = {
            "1": "random",
            "2": "threshold",
            "3": "edges",
            "4": "waves",
            "5": "file",
            "6": "file-edges",
        }
        sort_func_input = {
            "1": "lightness",
            "2": "hue",
            "3": "intensity",
            "4": "minimum",
            "5": "saturation",
        }
        return {
            "main": (
                ("-r 50 -c 250 -a 45"),
                "random",
                "intensity",
                True,
                False,
                False,
                False,
                False,
                False,
            ),
            "main file": (
                ("-r 50 -t .65"),
                "file",
                sort_func_input[str(rand.randint(1, 5))],
                True,
                False,
                True,
                False,
                False,
                True,
            ),
            "full random": (
                (
                    "-a "
                    + str(rand.randrange(0, 360))
                    + " -c "
                    + str(rand.randrange(50, 500, 15))
                    + " -u "
                    + str((rand.randrange(50, 100, 5) / 100))
                    + " -t "
                    + str((rand.randrange(5, 50, 5) / 100))
                    + " -r "
                    + str(rand.randrange(5, 100, 5))
                ),
                int_func_input[str(rand.randint(1, 6))],
                sort_func_input[str(rand.randint(1, 5))],
                True,
                True,
                True,
                False,
                False,
                False,
            ),
            "snap-sort": (
                ("-r 50 -c 250 -a 45"),
                "snap",
                "intensity",
                True,
                False,
                False,
                False,
                True,
                False,
            ),
        }[preset_input]
    except KeyError:
        print("[WARNING] Invalid preset name, no preset will be applied")
        return "", "", "", False, False, False, False, False, False


# SORTER #
def sort_image(
    pixels: List, intervals: List, args: Any, sorting_function: Callable[[Any], float]
) -> List:
    """
    Sorts the image.
    -----
    :param pixels: List of pixel values.
    :param intervals: List of pixel values after being run through selected interval function.
    :param args: Arguments.
    :param sorting_function: Sorting function used in sorting of pixels.
    :returns: List of sorted pixels.
    """
    sorted_pixels = []  # type: List
    sort_interval = (
        lambda lst, func: [] if lst == [] else sorted(lst, key=func)
    )  # type: Callable[[List[Any], Callable[[Any], float]], List[Any]]
    for y in ProgressBars(len(pixels), "Sorting..."):
        row = []  # type: List
        x_min = 0
        for x_max in intervals[y]:
            interval = []  # type: List
            for x in range(x_min, x_max):
                AppendDataList(interval, x, y, pixels)
            if rand.randint(0, 100) >= args.randomness:
                row += sort_interval(interval, sorting_function)
            else:
                row += interval
            x_min = x_max
        AppendDataList(row, 0, y, pixels)
        Append(sorted_pixels, row)
    return sorted_pixels


# UTIL #
id_generator = lambda n: "".join(
    rand.choice(ascii_lowercase + ascii_uppercase + digits) for _ in range(n)
)  # type: Callable[[int], str]


def crop_to(image_to_crop: Any, args: Any) -> Any:
    """
    Crops image to the size of a reference image. This function assumes
    that the relevant image is located in the center and you want to crop away
    equal sizes on both the left and right as well on both the top and bottom.
    :param image_to_crop
    :param reference_image
    :return: image cropped to the size of the reference image
    """
    reference_image = ImgOpen(args.url, args.internet)
    reference_size = reference_image.size  # type: Tuple[int, int]
    current_size = image_to_crop.size  # type: Tuple[int, int]
    dx = current_size[0] - reference_size[0]
    dy = current_size[1] - reference_size[1]
    left = dx / 2
    upper = dy / 2
    right = dx / 2 + reference_size[0]
    lower = dy / 2 + reference_size[1]
    return image_to_crop.crop(box=(int(left), int(upper), int(right), int(lower)))


# INTERVALS #
def edge(pixels: Any, args: Any) -> List:
    edge_data = (
        ImgOpen(args.url, args.internet)
        .rotate(args.angle, expand=True)
        .filter(ImageFilter.FIND_EDGES)
        .convert("RGBA")
        .load()
    )  # type: Any

    filter_pixels = PixelAppend(
        len(pixels), len(pixels[0]), edge_data, "Finding threshold..."
    )
    edge_pixels = []  # type: List
    intervals = []  # type: List

    for y in ProgressBars(len(pixels), "Thresholding..."):
        Append(edge_pixels, [])
        for x in range(len(pixels[0])):
            AppendBW(edge_pixels, x, y, filter_pixels, args.bottom_threshold)

    for y in tqdm(
        range(len(pixels) - 1, 1, -1), desc=("{:30}".format("Cleaning up..."))
    ):
        for x in range(len(pixels[0]) - 1, 1, -1):
            if (
                edge_pixels[y][x] == black_pixel
                and edge_pixels[y][x - 1] == black_pixel
            ):
                edge_pixels[y][x] = white_pixel

    for y in ProgressBars(len(pixels), "Defining intervals..."):
        Append(intervals, [])
        for x in range(len(pixels[0])):
            if edge_pixels[y][x] == black_pixel:
                AppendPartial(intervals, y, x)
        AppendPartial(intervals, y, len(pixels[0]))
    return intervals


def threshold(pixels: Any, args: Any) -> List:
    intervals = []  # type: List

    for y in ProgressBars(len(pixels), "Determining intervals..."):
        Append(intervals, [])
        for x in range(len(pixels[0])):
            if (
                lightness(pixels[y][x]) < args.bottom_threshold
                or lightness(pixels[y][x]) > args.upper_threshold
            ):
                AppendPartial(intervals, y, x)
        AppendPartial(intervals, y, len(pixels[0]))
    return intervals


def random(pixels: Any, args: Any) -> List:
    intervals = []  # type: List

    for y in ProgressBars(len(pixels), "Determining intervals..."):
        Append(intervals, [])
        x = 0
        while True:
            width = RandomWidth(args.clength)
            x += width
            if x > len(pixels[0]):
                AppendPartial(intervals, y, len(pixels[0]))
                break
            else:
                AppendPartial(intervals, y, x)
    return intervals


def waves(pixels: Any, args: Any) -> List:
    intervals = []  # type: List

    for y in ProgressBars(len(pixels), "Determining intervals..."):
        Append(intervals, [])
        x = 0
        while True:
            width = args.clength + rand.randint(0, 10)
            x += width
            if x > len(pixels[0]):
                AppendPartial(intervals, y, len(pixels[0]))
                break
            else:
                AppendPartial(intervals, y, x)
    return intervals


def file_mask(pixels: Any, args: Any) -> List:
    img = elementary_ca()[0].resize((len(pixels[0]), len(pixels)), Image.ANTIALIAS)
    data = img.load()  # type: Any

    file_pixels = PixelAppend(img.size[1], img.size[0], data, "Defining edges...")
    intervals = []  # type: List

    for y in tqdm(
        range(len(pixels) - 1, 1, -1), desc=("{:30}".format("Cleaning up edges..."))
    ):
        for x in range(len(pixels[0]) - 1, 1, -1):
            if (
                file_pixels[y][x] == black_pixel
                and file_pixels[y][x - 1] == black_pixel
            ):
                file_pixels[y][x] = white_pixel

    for y in ProgressBars(len(pixels), "Defining intervals..."):
        Append(intervals, [])
        for x in range(len(pixels[0])):
            if file_pixels[y][x] == black_pixel:
                AppendPartial(intervals, y, x)
        AppendPartial(intervals, y, len(pixels[0]))

    return intervals


def file_edges(pixels: Any, args: Any) -> List:
    edge_data = (
        elementary_ca()[0]
        .rotate(args.angle, expand=True)
        .resize((len(pixels[0]), len(pixels)), Image.ANTIALIAS)
        .filter(ImageFilter.FIND_EDGES)
        .convert("RGBA")
        .load()
    )  # type: Any

    filter_pixels = PixelAppend(
        len(pixels), len(pixels[0]), edge_data, "Defining edges..."
    )
    edge_pixels = []  # type: List
    intervals = []  # type: List

    for y in ProgressBars(len(pixels), "Thresholding..."):
        Append(edge_pixels, [])
        for x in range(len(pixels[0])):
            AppendBW(edge_pixels, x, y, filter_pixels, args.bottom_threshold)

    for y in tqdm(
        range(len(pixels) - 1, 1, -1), desc=("{:30}".format("Cleaning up edges..."))
    ):
        for x in range(len(pixels[0]) - 1, 1, -1):
            if (
                edge_pixels[y][x] == black_pixel
                and edge_pixels[y][x - 1] == black_pixel
            ):
                edge_pixels[y][x] = white_pixel

    for y in ProgressBars(len(pixels), "Defining intervals..."):
        Append(intervals, [])
        for x in range(len(pixels[0])):
            if edge_pixels[y][x] == black_pixel:
                AppendPartial(intervals, y, x)
        AppendPartial(intervals, y, len(pixels[0]))
    return intervals


def snap_sort(pixels: Any, args: Any) -> List:
    input_img = ImgOpen("thanos_img.png", False)
    print("Opening the soul stone...")
    pixels_snap = np.asarray(input_img)  # type: Any

    print("Preparing for balance...")
    nx, ny = input_img.size
    xy = np.mgrid[:nx, :ny].reshape(2, -1).T  # type: Any
    rounded = int(round(int(xy.shape[0] / 2), 0))  # type: int

    numbers_that_dont_feel_so_good = xy.take(
        np.random.choice(xy.shape[0], rounded, replace=False), axis=0
    )  # type: Any
    print(f'Number of those worthy of the sacrifice: {("{:,}".format(rounded))}')

    pixels_snap.setflags(write=1)
    for i in ProgressBars(len(numbers_that_dont_feel_so_good), "Snapping..."):
        pixels_snap[numbers_that_dont_feel_so_good[i][0]][
            numbers_that_dont_feel_so_good[i][1]
        ] = [0, 0, 0, 0]

    print("Sorted perfectly in half.")
    feel_better = Image.fromarray(pixels_snap, "RGBA")  # type: Any
    feel_better.save("snapped_pixels.png")

    snapped_img = ImgOpen("snapped_pixels.png", False)
    data = snapped_img.load()  # type: Any
    size0, size1 = snapped_img.size
    pixels_return = PixelAppend(size1, size0, data, "Returning saved...")

    os.remove("snapped_pixels.png")
    os.remove("thanos_img.png")
    print(
        f"{('///' * 15)}\nPerfectly balanced, as all things should be.\n{('///' * 15)}"
    )

    return pixels_return


def shuffle_total(pixels: Any, args: Any) -> List:
    print("Creating array from image...")
    input_img = ImgOpen(args.url, args.internet)
    height = input_img.size[1]  # type: int
    shuffle = np.array(input_img)  # type: Any

    for i in ProgressBars(int(height), "Shuffling image..."):
        np.random.shuffle(shuffle[i])
    shuffled_out = Image.fromarray(shuffle, "RGB")  # type: Any
    shuffled_out.save("shuffled.png")
    shuffled_img = ImgOpen("shuffled.png", False)
    data = shuffled_img.load()  # type: Any

    size0, size1 = input_img.size
    pixels = PixelAppend(size1, size0, data, "Recreating image...")

    os.remove("shuffled.png")
    return pixels


def shuffled_axis(pixels: Any, args: Any) -> List:
    print("Creating array from image...")
    input_img = ImgOpen(args.url, args.internet)
    height = input_img.size[1]  # type: int
    shuffle = np.array(input_img)  # type: Any

    for _ in ProgressBars(height, "Shuffling image..."):
        np.random.shuffle(shuffle)
    shuffled_out = Image.fromarray(shuffle, "RGB")  # type: Any
    shuffled_out.save("shuffled.png")
    shuffled_img = ImgOpen("shuffled.png", False)
    data = shuffled_img.load()  # type: Any

    size0, size1 = input_img.size
    pixels = PixelAppend(size1, size0, data, "Recreating image...")

    os.remove("shuffled.png")
    return pixels


def none(pixels: Any, args: Any) -> List:
    intervals = []  # type: List
    for y in ProgressBars(len(pixels), "Determining intervals..."):
        Append(intervals, [len(pixels[y])])
    return intervals


# MAIN #
def main():
    """
    Pixelsorting an image.
    """
    clear()
    # remove old image files that didn't get deleted before
    removeOld = lambda f: os.remove(f) if os.path.isfile(f) else None
    removeOld("image.png")
    removeOld("thanos_img.png")
    removeOld("shuffled.png")
    removeOld("snapped_pixels.png")
    removeOld("elementary_ca.png")

    print(
        "Pixel sorting based on web hosted images.\nMost of the backend is sourced from https://github.com/satyarth/pixelsort"
        + "\nThe output image is uploaded to put.re after being sorted.\n"
        + "\nTo see any past runs, args used, and the result image, open 'output.txt'\n"
        + (35 * "--")
        + "\nThanks for using this program!\nPress any key to continue..."
    )
    input()
    clear()

    internet = has_internet("8.8.8.8", 53, 3)

    if internet:
        url_input = input(
            "Please input the URL of the image or the default image #:\n(this might take a while depending the image resolution)\n"
        )
        url, url_given, url_random, random_url = read_image_input(url_input, internet)
    else:
        print("Internet not connected! Local image must be used.")
        url_input = input(
            "Please input the location of the local file (default image in images folder):\n"
        )
        url, url_given, url_random, random_url = read_image_input(url_input, internet)
    input_img = ImgOpen(url, internet)

    width, height = input_img.size
    resolution_msg = f"Resolution: {width}x{height}"
    image_msg = (
        (
            f"[WARNING] No image url given, using {('random' if url_random else 'chosen')} default image {(random_url if url_random else str(url_input))}"
        )
        if not url_given
        else "Using given image "
    )
    clear()

    # preset input
    print(f"{image_msg}\n{resolution_msg}")
    preset_q = input("\nDo you wish to apply a preset? (y/n)\n").lower()
    clear()
    if preset_q in ["y", "yes", "1"]:
        print(
            "Preset options:\n"
            "-1|main -- Main args (r 50, c 250, a 45, random, intensity)\n"
            "-2|main file -- Main args, but only for file and file edges\n"
            "-3|full random -- Randomness in every arg!\n"
            "-4|snap-sort -- Run from it, dread it, destiny still arrives."
        )
        preset_input = input("\nChoice: ").lower()
        if preset_input in ["1", "2", "3", "4"]:
            preset_input = {
                "1": "main",
                "2": "main file",
                "3": "full random",
                "4": "snap-sort",
            }[preset_input]
        # if presets are applied, they take over args
        arg_parse_input, int_func_input, sort_func_input, preset_true, int_rand, sort_rand, shuffled, snapped, file_sorted = read_preset(
            preset_input
        )
    else:
        preset_true = False
    clear()

    # int func, sort func & int msg, sort msg
    if not preset_true:
        # int func input
        print(f"{image_msg}\n{resolution_msg}")
        print(
            "\nWhat interval function are you using?\nOptions (default is random):\n"
            "-1|random\n"
            "-2|threshold\n"
            "-3|edges\n"
            "-4|waves\n"
            "-5|snap\n"
            "-6|shuffle-total\n"
            "-7|shuffle-axis\n"
            "-8|file\n"
            "-9|file-edges\n"
            "-10|none\n"
            "-11|random select"
        )
        int_func_input = input("\nChoice: ").lower()
        int_func_options = [
            "random",
            "threshold",
            "edges",
            "waves",
            "snap",
            "shuffle-total",
            "shuffle-axis",
            "file",
            "file-edges",
            "none",
        ]
        if int_func_input in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            int_func_input = int_func_options[int(int_func_input) - 1]
            int_rand = False
        elif int_func_input in ["11", "random select"]:
            int_func_input = int_func_options[rand.randint(0, 3)]
            int_rand = True
        shuffled = (
            True if int_func_input in ["shuffle-total", "shuffle-axis"] else False
        )
        snapped = True if int_func_input in ["snap"] else False
        file_sorted = True if int_func_input in ["file", "file-edges"] else False

        int_msg = (
            (
                "Interval function: "
                if not int_rand
                else "Interval function (randomly selected): "
            )
            + int_func_input
            if int_func_input in int_func_options
            else "Interval function: random (default)"
        )
        clear()

        # sort func input
        print(f"{image_msg}\n{int_msg}\n{resolution_msg}")
        print(
            "\nWhat sorting function are you using?\nOptions (default is lightness):\n"
            "-1|lightness\n"
            "-2|hue\n"
            "-3|intensity\n"
            "-4|minimum\n"
            "-5|saturation\n"
            "-6|random select"
        )
        sort_func_input = input("\nChoice: ").lower()
        sort_func_options = ["lightness", "hue", "intensity", "minimum", "saturation"]
        if sort_func_input in ["1", "2", "3", "4", "5"]:
            sort_func_input = sort_func_options[int(sort_func_input) - 1]
            sort_rand = False
        elif sort_func_input in ["6", "random select"]:
            sort_func_input = sort_func_options[rand.randint(0, 4)]
            sort_rand = True
        else:
            sort_rand = False
        sort_msg = (
            (
                "Sorting function: "
                if not sort_rand
                else "Sorting function (randomly selected): "
            )
            + sort_func_input
            if sort_func_input in sort_func_options
            else "Sorting function: lightness (default)"
        )
        clear()

    # int func msg, sort func msg
    if preset_true:
        int_msg = (
            (
                "Interval function: "
                if not int_rand
                else "Interval function (randomly selected): "
            )
            + int_func_input
            if int_func_input
            in [
                "random",
                "threshold",
                "edges",
                "waves",
                "snap",
                "shuffle-total",
                "shuffle-axis",
                "file",
                "file-edges",
                "none",
            ]
            else "Interval function: random (default)"
        )

        sort_msg = (
            (
                "Sorting function: "
                if not sort_rand
                else "Sorting function (randomly selected): "
            )
            + sort_func_input
            if sort_func_input
            in ["lightness", "hue", "intensity", "minimum", "saturation"]
            else "Sorting function: lightness (default)"
        )

    # hosting site
    if internet:
        output_image_path = "image.png"
        site_msg = "Uploading sorted image to put.re"
    else:
        print("Internet not connected! Image will be saved locally.\n")
        file_name = input(
            "Name of output file (leave empty for randomized name):\n(do not include the file extension, .png will always be used.)\n"
        )
        output_image_path = (
            (id_generator(5) + ".png") if file_name in ["", " "] else file_name
        )
        site_msg = f"Internet not connected, saving locally as {output_image_path}"
    clear()

    # args
    if not preset_true:
        needs_help = input("Do you need help with args? (y/n)\n")
        clear()
        if needs_help in ["y", "yes", "1"]:
            print(
                f"{image_msg}\n{resolution_msg}\n{int_msg}\n{sort_msg}\n{site_msg}\n"
                f"\nWhat args will you be adding?\n"
                f'{("{:21}".format("Parameter"))}{("{:>6}".format("| Flag |"))}{("{:>12}".format("Description"))}\n'
                f'{("{:21}".format("---------------------"))}{("{:>6}".format("|------|"))}{("{:>12}".format("------------"))}\n'
                f'{("{:21}".format("Randomness"))}{("{:>6}".format("| -r   |"))}What percentage of intervals not to sort. 0 by default.\n'
                f'{("{:21}".format("Char. length"))}{("{:>6}".format("| -c   |"))}Characteristic length for the random width generator.\n{29 * " "}Used in mode random.\n'
                f'{("{:21}".format("Angle"))}{("{:>6}".format("| -a   |"))}Angle at which you\'re pixel sorting in degrees. 0 (horizontal) by default.\n'
                f'{("{:21}".format("Threshold (lower)"))}{("{:>6}".format("| -t   |"))}How dark must a pixel be to be considered as a \'border\' for sorting?\n{29 * " "}Takes values from 0-1. 0.25 by default. Used in edges and threshold modes.\n'
                f'{("{:21}".format("Threshold (upper)"))}{("{:>6}".format("| -u   |"))}How bright must a pixel be to be considered as a \'border\' for sorting?\n{29 * " "}Takes values from 0-1. 0.8 by default. Used in threshold mode.\n'
            )
        else:
            print(
                f"{image_msg}\n{resolution_msg}\n{int_msg}\n{sort_msg}\n{site_msg}\n"
                f"\nWhat args will you be adding?\n"
                f'{("{:21}".format("Parameter"))}{("{:>6}".format("| Flag |"))}\n'
                f'{("{:21}".format("---------------------"))}{("{:>6}".format("|------|"))}\n'
                f'{("{:21}".format("Randomness"))}{("{:>6}".format("| -r   |"))}\n'
                f'{("{:21}".format("Char. length"))}{("{:>6}".format("| -c   |"))}\n'
                f'{("{:21}".format("Angle"))}{("{:>6}".format("| -a   |"))}\n'
                f'{("{:21}".format("Threshold (lower)"))}{("{:>6}".format("| -t   |"))}\n'
                f'{("{:21}".format("Threshold (upper)"))}{("{:>6}".format("| -u   |"))}\n'
            )
        arg_parse_input = input("\nArgs: ")
        clear()

    # args
    parse = argparse.ArgumentParser(description="pixel mangle an image")
    """
    (Taken args)
    :-l,--url -> url
    :-i,--int_function -> interval function
    :-s,--sorting_function -> sorting function
    :-t,--bottom_threshold -> bottom/lower threshold
    :-u,--upper_threshold -> top/upper threshold
    :-c,--clength -> character length
    :-a,--angle -> angle for rotation
    :-r,--randomness -> randomness
    :-y,--internet -> is internet connected
    """
    parse.add_argument(
        "-l",
        "--url",
        help="URL of a given image. Used as the input image.",
        default="https://s.put.re/QsUQbC1R.jpg",
    )
    parse.add_argument(
        "-i",
        "--int_function",
        help="random, threshold, edges, waves, snap, shuffle-total, shuffle-axis, file, file-edges, none",
        default="random",
    )
    parse.add_argument(
        "-s",
        "--sorting_function",
        help="lightness, intensity, hue, saturation, minimum",
        default="lightness",
    )
    parse.add_argument(
        "-t",
        "--bottom_threshold",
        type=float,
        help="Pixels darker than this are not sorted, between 0 and 1",
        default=0.25,
    )
    parse.add_argument(
        "-u",
        "--upper_threshold",
        type=float,
        help="Pixels darker than this are not sorted, between 0 and 1",
        default=0.8,
    )
    parse.add_argument(
        "-c",
        "--clength",
        type=int,
        help="Characteristic length of random intervals",
        default=50,
    )
    parse.add_argument(
        "-a",
        "--angle",
        type=float,
        help="Rotate the image by an angle (in degrees) before sorting",
        default=0,
    )
    parse.add_argument(
        "-r",
        "--randomness",
        type=float,
        help="What percentage of intervals are NOT sorted",
        default=15,
    )
    parse.add_argument(
        "-y",
        "--internet",
        type=bool,
        help="Is internet connected or not? Boolean.",
        default=True,
    )

    # add a space to start of arg_parse_in, used for splitting
    if arg_parse_input not in ["", " "] and arg_parse_input[0] is not " ":
        arg_parse_input = " " + arg_parse_input

    if arg_parse_input not in [None, "", " "]:
        args_in = arg_parse_input.split(" -")
        args_in[:] = ["-" + x for x in args_in]
        args_in.pop(0)
    else:
        print("No args given")
        args_in = ""

    args_full = parse_args_full(url, int_func_input, sort_func_input, args_in, internet)

    __args = parse.parse_args(args_full)

    interval_function = read_interval_function(int_func_input)
    sorting_function = read_sorting_function(sort_func_input)

    print(
        f"{image_msg}\n{resolution_msg}\n"
        f'{("Preset: " + preset_input if preset_true else "No preset applied")}'
        f"\n{int_msg}\n{sort_msg}\n{site_msg}"
    )

    # even if they were never given, at some point they need to be assigned to default values properly
    if int_func_input in ["", " "]:
        int_func_input = "random"
    if sort_func_input in ["", " "]:
        sort_func_input = "lightness"

    print(f"Lower threshold: {__args.bottom_threshold}") if int_func_input in [
        "threshold",
        "edges",
        "file-edges",
    ] else None
    print(f"Upper threshold: {__args.upper_threshold}") if int_func_input in [
        "random",
        "waves",
    ] else None
    print(f"Characteristic length: {__args.clength}") if int_func_input in [
        "random",
        "waves",
    ] else None
    print(f"Randomness: {__args.randomness} %")
    print(f"Angle: {__args.angle} °")
    print("------------------------------")

    print("Opening image...")

    print("Rotating image...")
    input_img = input_img.rotate(__args.angle, expand=True)

    print("Getting data...")
    data = input_img.load()  # type: Any

    size0, size1 = input_img.size
    pixels = PixelAppend(size1, size0, data, "Getting pixels...")

    if shuffled or snapped:
        if snapped:
            intervals = random(pixels, __args)
            sorted_pixels = sort_image(pixels, intervals, __args, sorting_function)
            print(
                f"{('///' * 15)}\nRun from it. Dread it. Destiny still arrives.\n{('///' * 15)}"
            )
            thanos_img = Image.new("RGBA", input_img.size)
            size0, size1 = thanos_img.size
            for y in ProgressBars(size1, "The end is inevitable..."):
                for x in range(size0):
                    ImgPixels(thanos_img, x, y, sorted_pixels)
            thanos_img.save("thanos_img.png")
            sorted_pixels = interval_function(intervals, __args)
        else:
            sorted_pixels = interval_function(pixels, __args)
    else:
        intervals = interval_function(pixels, __args)
        sorted_pixels = sort_image(pixels, intervals, __args, sorting_function)

    output_img = Image.new("RGBA", input_img.size)
    size0, size1 = output_img.size
    for y in ProgressBars(size1, "Building output image..."):
        for x in range(size0):
            ImgPixels(output_img, x, y, sorted_pixels)

    if __args.angle is not 0:
        print("Rotating output image back to original orientation...")
        output_img = output_img.rotate(360 - __args.angle, expand=True)

        print("Crop image to apropriate size...")
        output_img = crop_to(output_img, __args)

    print("Saving image...")
    output_img.save(output_image_path)

    if internet:
        date_time = datetime.now().strftime("%m/%d/%Y %H:%M")

        print("Uploading...")
        r = post(
            "https://api.put.re/upload",
            files={"file": ("image.png", open("image.png", "rb"))},
        )
        output = json.loads(r.text)
        link = output["data"]["link"]
        print("Image uploaded!")

        if file_sorted:
            r = post(
                "https://api.put.re/upload",
                files={"file": ("elementary_ca.png", open("elementary_ca.png", "rb"))},
            )
            output = json.loads(r.text)
            file_link = output["data"]["link"]
            print("File image uploaded!")
            os.remove("elementary_ca.png")

        # delete old file, seeing as its uploaded
        print("Removing local file...")
        removeOld(output_image_path)

        # output to 'output.txt'
        print("Saving config to 'output.txt'...")
        with open("output.txt", "a") as f:
            f.write(
                f"\nStarting image url: {url}\n{resolution_msg}\n"
                f'{("File image: ") if file_sorted else None}{(file_link if file_sorted else None)}{(elementary_ca()[1] if file_sorted else None)}\n'
                f'{("Int func: " if not int_rand else "Int func (randomly chosen): ")}{int_func_input}\n'
                f'{("Sort func: " if not sort_rand else "Sort func (randomly chosen): ")}{sort_func_input}\n'
                f'Args: {(arg_parse_input if arg_parse_input is not None else "No args")}\n'
                f'Sorted on: {date_time}\n\nSorted image: {link}\n{(35 * "-")}'
            )

        print("Done!")
        print(f"Link to image: {link}")
    else:
        print("Not saving config to 'output.txt', as there is no internet.\nDone!")
    output_img.show()


if __name__ == "__main__":
    main()
