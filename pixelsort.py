# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import random as rand
import socket
import sys
from colorsys import rgb_to_hsv
from datetime import datetime
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Any, Callable, List, Tuple

import numpy as np
from PIL import Image, ImageFilter
from requests import get, post
from tqdm import tqdm

from intervals import (
    edge,
    file_edges,
    file_mask,
    none,
    random,
    shuffle_total,
    shuffled_axis,
    snap_sort,
    threshold,
    waves,
)
from MiscFuncs import CropTo, ElementaryCA, HasInternet, PixelAppend, UploadImg
from MiscLambdas import (
    Append,
    AppendBW,
    AppendList,
    AppendPartial,
    AppendPIL,
    IDGen,
    ImgOpen,
    ImgPixels,
    ProgressBars,
    RandomWidth,
    black_pixel,
    white_pixel,
)
from Sorting import SortImage, hue, intensity, lightness, minimum, saturation


# MISC FUNCTIONS #
def clear():  # clear screen
    return os.system("cls" if os.name == "nt" else "clear")


'''
def HasInternet(host: str, port: int, timeout: int) -> bool:
    """
    Checks for internet.
    ------
    :param host: 8.8.8.8 (google-public-dns-a.google.com)
    :param port: 53
    :param timeout: 3

    Service: domain (DNS/TCP)

    Examples
    ------
    >>> internet = HasInternet("8.8.8.8", 53, 3)
    >>> print(internet)
    True
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


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
    pixels: List = []
    for y in ProgressBars(size1, msg):
        Append(pixels, [])
        for x in range(size0):
            AppendPIL(pixels, x, y, data)
    return pixels


def ElementaryCA(pixels: Any) -> Any:
    """
    Generate images of elementary cellular automata.
    Selected rules from https://en.wikipedia.org/wiki/Elementary_cellular_automaton
    ------
    :param pixels: 2D list of RGB values.
    :returns: PIL Image object.
    """
    width: int = rand.randrange(100, 150)
    height: int = rand.randrange(100, 150)
    ruleprompt: Any = input(
        f"Rule selection (max of 255)(leave blank for random)\n"
        f"(Recommended to leave blank, most of the rules aren't good): "
    )
    try:
        if int(ruleprompt) in range(255):
            rulenumber: int = int(ruleprompt)
    except ValueError:
        rules: List = [26, 19, 23, 25, 35, 106, 11, 110, 45, 41, 105, 54, 3, 15, 9, 154]
        rulenumber = rules[rand.randrange(0, len(rules))]

    scalefactor: int = rand.randrange(1, 5)

    # Define colors of the output image
    true_pixel: Tuple[int, int, int] = (255, 255, 255)
    false_pixel: Tuple[int, int, int] = (0, 0, 0)

    # Generates a dictionary that tells you what your state should be based on the rule number
    # and the states of the adjacent cells in the previous generation
    def generate_rule(rulenumber: int) -> dict:
        rule: dict = {}
        for left in [False, True]:
            for middle in [False, True]:
                for right in [False, True]:
                    rule[(left, middle, right)] = rulenumber % 2 == 1
                    rulenumber //= 2
        return rule

    # Generates a 2d representation of the state of the automaton at each generation
    def generate_ca(rule: dict) -> List:
        ca: List = []
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

    print(f"Creating file image..\nRule: {rulenumber}")
    for y in ProgressBars(height, "Placing pixels..."):
        for x in range(width):
            newImg.putpixel(
                (x, y),
                true_pixel
                if ca[int(y / scalefactor)][int(x / scalefactor)]
                else false_pixel,
            )

    print("File image created!")
    newImg.save("images/ElementaryCA.png")
    return newImg


def UploadImg(img: str) -> str:
    """
    Upload an image to put.re
    -----
    :param img: A string of a local file.
    :returns: String of link of the uploaded file.
    
    Example
    -----
    >>> link = UploadImg("https://i.redd.it/ufj4p5zwf9v21.jpg")
    >>> print(link)
    >>> "https://s.put.re/Uc2A2Z7t.jpg"
    (those links are actually correct.)
    """
    r = post("https://api.put.re/upload", files={"file": (img, open(img, "rb"))})
    output = json.loads(r.text)
    link: str = output["data"]["link"]
    return link


# LAMBDA FUNCTIONS #
ImgOpen: Callable[[str, bool], Any] = lambda u, i: (
    Image.open((get(u, stream=True).raw) if i else u)
).convert("RGBA")
Append: Callable[[Any, Any], Any] = lambda l, obj: l.append(obj)
AppendPIL: Callable[[Any, int, int, Any], Any] = lambda l, x, y, d: l[y].append(d[x, y])
AppendList: Callable[[List, int, int, Any], Any] = lambda l, x, y, d: l.append(d[y][x])
AppendPartial: Callable[[List, int, Any], List] = lambda l, y, x: l[y].append(x)
ImgPixels: Callable[[Any, int, int, Any], Any] = lambda i, x, y, d: i.putpixel(
    (x, y), d[y][x]
)
RandomWidth: Callable[[int], int] = lambda c: int(c * (1 - rand.random()))
ProgressBars: Callable[[Any, str], Any] = lambda r, d: tqdm(
    range(r), desc=("{:30}".format(d))
)
AppendBW: Callable[[List, int, int, Any, float], List] = (
    lambda l, x, y, d, t: AppendPartial(l, y, white_pixel)
    if (lightness(d[y][x]) < t)
    else AppendPartial(l, y, black_pixel)
)


# SORTING PIXELS #
lightness: Callable[[Any], float] = (lambda p: rgb_to_hsv(p[0], p[1], p[2])[2] / 255.0)
intensity: Callable[[Any], float] = lambda p: p[0] + p[1] + p[2]
hue: Callable[[Any], float] = lambda p: rgb_to_hsv(p[0], p[1], p[2])[0] / 255.0
saturation: Callable[[Any], float] = (lambda p: rgb_to_hsv(p[0], p[1], p[2])[1] / 255.0)
minimum: Callable[[Any], float] = lambda p: min(p[0], p[1], p[2])
'''

# READING FUNCTIONS #
def ReadImageInput(url_input: str, internet: bool) -> Tuple[str, bool, bool, Any]:
    """
    Reading the image input.
    -----
    :param url_input: The inputted URL, number of default image, or local file path.
    :param internet: true/false for having internet.
    :returns: (in order) url[str], url_given[bool], url_random[bool], random_url[str]
    """
    print("Opening image...")
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
            "6": "https://s.put.re/K49iqXVJ.png",
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


def ReadIntervalFunction(int_func_input: str) -> Callable[[Any, Any], List]:
    """
    Reading the interval function.
    -----
    :param int_func_input: A (lowercase) string.
    :returns: Interval function.
    :raises KeyError: String not in selection.

    Example
    -----
    >>> interval = ReadIntervalFunction("random")
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


def ReadSortingFunction(sort_func_input: str) -> Callable[[Any], float]:
    """
    Reading the sorting function.
    -----
    :param sort_func_input: A (lowercase) string.
    :returns: Sorting function.
    :raises KeyError: String not in selection.

    Example
    -----
    >>> sortFunc = ReadSortingFunction("hue")
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


def ReadPreset(
    preset_input: str
) -> Tuple[str, str, str, bool, bool, bool, bool, bool, bool, bool, bool]:
    """
    Returning values for 'presets'.
    -----
    :param preset_input: A (lowercase) string.
    :returns: (in order) arg_parse_input, int_func_input, sort_func_input, preset_true, int_rand, sort_rand, int_chosen, sort_chosen, shuffled, snapped, file_sorted
    :raises KeyError: String not in selection.
    """
    try:
        # order-- arg_parse_input, int_func_input, sort_func_input, preset_true, int_rand, sort_rand, shuffled, snapped, file_sorted
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
                True,
                True,
                False,
                False,
                False,
            ),
            "main file": (
                (f"-r {rand.randrange(15, 65)} -t {float(rand.randrange(65, 90)/100)}"),
                "file-edges",
                "minimum",
                True,
                False,
                False,
                True,
                True,
                False,
                False,
                True,
            ),
            "full random": (
                (
                    f"-a {rand.randrange(0, 360)}"
                    f"-c {rand.randrange(50, 500, 15)}"
                    f"-u {(rand.randrange(50, 100, 5) / 100)}"
                    f"-t {(rand.randrange(5, 50, 5) / 100)}"
                    f"-r {rand.randrange(5, 100, 5)}"
                ),
                int_func_input[str(rand.randint(1, 6))],
                sort_func_input[str(rand.randint(1, 5))],
                True,
                True,
                True,
                True,
                True,
                False,
                False,
                False,
            ),
            "snap-sort": (
                (
                    f"-r {rand.randrange(15,50,5)} -c {rand.randrange(50, 250, 10)} -a {rand.randrange(0,180)}"
                ),
                "snap",
                "minimum",
                True,
                False,
                False,
                True,
                True,
                False,
                True,
                False,
            ),
        }[preset_input]
    except KeyError:
        print("[WARNING] Invalid preset name, no preset will be applied")
        return "", "", "", False, False, False, False, False, False, False, False


'''
# SORTER #
def SortImage(
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
    sorted_pixels: List = []
    sort_interval: Callable[[List[Any], Callable[[Any], float]], List[Any]] = (
        lambda lst, func: [] if lst == [] else sorted(lst, key=func)
    )
    for y in ProgressBars(len(pixels), "Sorting..."):
        row: List = []
        x_min = 0
        for x_max in intervals[y]:
            interval: List = []
            for x in range(x_min, x_max):
                AppendList(interval, x, y, pixels)
            if rand.randint(0, 100) >= args.randomness:
                row += sort_interval(interval, sorting_function)
            else:
                row += interval
            x_min = x_max
        AppendList(row, 0, y, pixels)
        Append(sorted_pixels, row)
    return sorted_pixels
'''

'''
# UTIL #
IDGen: Callable[[int], str] = lambda n: "".join(
    rand.choice(ascii_lowercase + ascii_uppercase + digits) for _ in range(n)
)



def CropTo(image_to_crop: Any, args: Any) -> Any:
    """
    Crops image to the size of a reference image. This function assumes
    that the relevant image is located in the center and you want to crop away
    equal sizes on both the left and right as well on both the top and bottom.
    :param image_to_crop
    :param reference_image
    :return: image cropped to the size of the reference image
    """
    reference_image = ImgOpen(args.url, args.internet)
    reference_size: Tuple[int, int] = reference_image.size
    current_size: Tuple[int, int] = image_to_crop.size
    dx = current_size[0] - reference_size[0]
    dy = current_size[1] - reference_size[1]
    left = dx / 2
    upper = dy / 2
    right = dx / 2 + reference_size[0]
    lower = dy / 2 + reference_size[1]
    return image_to_crop.crop(box=(int(left), int(upper), int(right), int(lower)))

'''

"""
# INTERVALS #
def edge(pixels: Any, args: Any) -> List:
    edge_data: Any = (
        ImgOpen(args.url, args.internet)
        .rotate(args.angle, expand=True)
        .filter(ImageFilter.FIND_EDGES)
        .convert("RGBA")
        .load()
    )

    filter_pixels = PixelAppend(
        len(pixels), len(pixels[0]), edge_data, "Finding threshold..."
    )
    edge_pixels: List = []
    intervals: List = []

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
    intervals: List = []

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
    intervals: List = []

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
    intervals: List = []

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
    img = ElementaryCA(pixels).resize((len(pixels[0]), len(pixels)), Image.ANTIALIAS)
    data: Any = img.load()

    file_pixels = PixelAppend(img.size[1], img.size[0], data, "Defining edges...")
    intervals: List = []

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
    edge_data: Any = (
        ElementaryCA(pixels)
        .rotate(args.angle, expand=True)
        .resize((len(pixels[0]), len(pixels)), Image.ANTIALIAS)
        .filter(ImageFilter.FIND_EDGES)
        .convert("RGBA")
        .load()
    )

    filter_pixels = PixelAppend(
        len(pixels), len(pixels[0]), edge_data, "Defining edges..."
    )
    edge_pixels: List = []
    intervals: List = []

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
    input_img = ImgOpen("images/thanos_img.png", False)
    pixels_snap: Any = np.asarray(input_img)

    print("The hardest choices require the strongest wills...")
    nx, ny = input_img.size
    xy: Any = np.mgrid[:nx, :ny].reshape(2, -1).T
    rounded: int = int(round(int(xy.shape[0] / 2), 0))

    numbers_that_dont_feel_so_good: Any = xy.take(
        np.random.choice(xy.shape[0], rounded, replace=False), axis=0
    )
    print(f'Number of those worthy of the sacrifice: {("{:,}".format(rounded))}')

    pixels_snap.setflags(write=1)
    for i in ProgressBars(len(numbers_that_dont_feel_so_good), "Snapping..."):
        pixels_snap[numbers_that_dont_feel_so_good[i][1]][
            numbers_that_dont_feel_so_good[i][0]
        ] = [0, 0, 0, 0]

    print("Sorted perfectly in half.")
    feel_better: Any = Image.fromarray(pixels_snap, "RGBA")
    feel_better.save("images/snapped_pixels.png")

    snapped_img = ImgOpen("images/snapped_pixels.png", False)
    data: Any = snapped_img.load()
    size0, size1 = snapped_img.size
    pixels_return = PixelAppend(size1, size0, data, "I hope they remember you...")

    os.remove("images/snapped_pixels.png")
    os.remove("images/thanos_img.png")
    print(f"{('/' * 45)}\nPerfectly balanced, as all things should be.\n{('/' * 45)}")

    return pixels_return


def shuffle_total(pixels: Any, args: Any) -> List:
    print("Creating array from image...")
    input_img = ImgOpen(args.url, args.internet)
    height: int = input_img.size[1]
    shuffle: Any = np.array(input_img)

    for i in ProgressBars(int(height), "Shuffling image..."):
        np.random.shuffle(shuffle[i])
    shuffled_out: Any = Image.fromarray(shuffle, "RGB")
    shuffled_out.save("images/shuffled.png")
    shuffled_img = ImgOpen("images/shuffled.png", False)
    data: Any = shuffled_img.load()

    size0, size1 = input_img.size
    pixels = PixelAppend(size1, size0, data, "Recreating image...")

    os.remove("images/shuffled.png")
    return pixels


def shuffled_axis(pixels: Any, args: Any) -> List:
    print("Creating array from image...")
    input_img = ImgOpen(args.url, args.internet)
    height: int = input_img.size[1]
    shuffle: Any = np.array(input_img)

    for _ in ProgressBars(height, "Shuffling image..."):
        np.random.shuffle(shuffle)
    shuffled_out: Any = Image.fromarray(shuffle, "RGB")
    shuffled_out.save("images/shuffled.png")
    shuffled_img = ImgOpen("images/shuffled.png", False)
    data: Any = shuffled_img.load()

    size0, size1 = input_img.size
    pixels = PixelAppend(size1, size0, data, "Recreating image...")

    os.remove("images/shuffled.png")
    return pixels


def none(pixels: Any, args: Any) -> List:
    intervals: List = []
    for y in ProgressBars(len(pixels), "Determining intervals..."):
        Append(intervals, [len(pixels[y])])
    return intervals
"""


# MAIN #
def main():
    """
    Pixelsorting an image.
    """

    # arg parsing arguments
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
        default=10,
    )
    parse.add_argument(
        "-y",
        "--internet",
        type=bool,
        help="Is internet connected or not? Boolean.",
        default=True,
    )

    clear()
    # remove old image files that didn't get deleted before
    removeOld = lambda f: os.remove(f) if os.path.isfile(f) else None
    removeOld("images/image.png")
    removeOld("images/thanos_img.png")
    removeOld("images/shuffled.png")
    removeOld("images/snapped_pixels.png")
    removeOld("images/ElementaryCA.png")

    print(
        "Pixel sorting based on web hosted images.\nMost of the backend is sourced from https://github.com/satyarth/pixelsort"
        + "\nThe output image is uploaded to put.re after being sorted.\n"
        + "\nTo see any past runs, args used, and the result image, open 'output.txt'\n"
        + (35 * "--")
        + "\nThanks for using this program!\nPress any key to continue..."
    )
    input()
    clear()

    internet = HasInternet("8.8.8.8", 53, 3)

    if internet:
        url_input = input(
            "Please input the URL of the image or the default image #:\n(this might take a while depending the image resolution)\n"
        )
        if len(url_input) > 50:
            print("Image URL too long, uploading to put.re for a shorter URL...")
            img = ImgOpen(url_input, internet)
            img.save("image.png")
            url_input = UploadImg("image.png")
            removeOld("image.png")
        url, url_given, url_random, random_url = ReadImageInput(url_input, internet)
    else:
        print("Internet not connected! Local image must be used.")
        url_input = input(
            "Please input the location of the local file (default image in images folder):\n"
        )
        url, url_given, url_random, random_url = ReadImageInput(url_input, internet)
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
            "-4|snap-sort -- You could not live with your own failure. And where did that bring you? Back to me."
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
        arg_parse_input, int_func_input, sort_func_input, preset_true, int_rand, sort_rand, int_chosen, sort_chosen, shuffled, snapped, file_sorted = ReadPreset(
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
            int_chosen = True
            int_rand = False
        elif int_func_input in ["11", "random select"]:
            int_func_input = int_func_options[rand.randint(0, 3)]
            int_chosen = True
            int_rand = True
        else:
            int_chosen, int_func_input = (
                (True, int_func_input)
                if int_func_input in int_func_options
                else (False, "random")
            )
            int_rand = False
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
            if int_chosen
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
            sort_chosen = True
            sort_rand = False
        elif sort_func_input in ["6", "random select"]:
            sort_func_input = sort_func_options[rand.randint(0, 4)]
            sort_chosen = True
            sort_rand = True
        else:
            sort_chosen, sort_func_input = (
                (True, sort_func_input)
                if sort_func_input in sort_func_options
                else (False, "lightness")
            )
            sort_rand = False

        sort_msg = (
            (
                "Sorting function: "
                if not sort_rand
                else "Sorting function (randomly selected): "
            )
            + sort_func_input
            if sort_chosen
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
        output_image_path = "images/image.png"
        site_msg = "Uploading sorted image to put.re"
    else:
        print("Internet not connected! Image will be saved locally.\n")
        file_name = input(
            "Name of output file (leave empty for randomized name):\n(do not include the file extension, .png will always be used.)\n"
        )
        output_image_path = (IDGen(5) + ".png") if file_name in ["", " "] else file_name
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

    if arg_parse_input in ["", " ", None]:
        print("No args given!")
        arg_parse_input = ""

    args_full = f"{arg_parse_input} -l {url} -i {int_func_input} -s {sort_func_input} -y {str(internet)}"

    __args = parse.parse_args(args_full.split())

    interval_function = ReadIntervalFunction(int_func_input)
    sorting_function = ReadSortingFunction(sort_func_input)

    print(
        f"{image_msg}\n{resolution_msg}\n"
        f'{("Preset: " + preset_input if preset_true else "No preset applied")}'
        f"\n{int_msg}\n{sort_msg}\n{site_msg}"
    )

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
    data: Any = input_img.load()

    size0, size1 = input_img.size
    pixels = PixelAppend(size1, size0, data, "Getting pixels...")

    if shuffled or snapped:
        if snapped:
            intervals = file_edges(pixels, __args)
            sorted_pixels = SortImage(pixels, intervals, __args, sorting_function)
            print(
                f"{('/' * 45)}\nDread it. Run from it. Destiny still arrives.\n{('/' * 45)}"
            )
            thanos_img = Image.new("RGBA", input_img.size)
            size0, size1 = thanos_img.size
            for y in ProgressBars(size1, "The end is near..."):
                for x in range(size0):
                    ImgPixels(thanos_img, x, y, sorted_pixels)
            thanos_img.save("images/thanos_img.png")
            print("I am... inevitable...")
            sorted_pixels = interval_function(intervals, __args)
        else:
            sorted_pixels = interval_function(pixels, __args)
    else:
        intervals = interval_function(pixels, __args)
        sorted_pixels = SortImage(pixels, intervals, __args, sorting_function)

    output_img = Image.new("RGBA", input_img.size)
    size0, size1 = output_img.size
    for y in ProgressBars(size1, "Building output image..."):
        for x in range(size0):
            ImgPixels(output_img, x, y, sorted_pixels)

    if __args.angle is not 0:
        print("Rotating output image back to original orientation...")
        output_img = output_img.rotate(360 - __args.angle, expand=True)

        print("Crop image to apropriate size...")
        output_img = CropTo(output_img, __args)

    print("Saving image...")
    output_img.save(output_image_path)

    if internet:
        date_time = datetime.now().strftime("%m/%d/%Y %H:%M")

        print("Uploading...")
        link = UploadImg("images/image.png")
        print("Image uploaded!")

        if file_sorted:
            file_link = UploadImg("images/ElementaryCA.png")
            print("File image uploaded!")

        # delete old file, seeing as its uploaded
        print("Removing local file...")
        removeOld(output_image_path)
        removeOld("images/ElementaryCA.png")

        # output to 'output.txt'
        print("Saving config to 'output.txt'...")
        with open("output.txt", "a") as f:
            f.write(
                f"\nStarting image url: {url}\n{resolution_msg}\n"
                f'{("Int func: " if not int_rand else "Int func (randomly chosen): ")}{int_func_input}\n'
                f'{(("File link: ")+file_link) if file_sorted else ""}\n'
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
