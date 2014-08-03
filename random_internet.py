#!/usr/bin/env python

import asyncio

"""
This script finds a number of random websites on the Internet which are alive,
using random word lists.

The word list used for this script was taken from
http://www.mieliestronk.com/wordlist.html
"""

# Taken from a list of common user agents on the Internet.
COMMON_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36"
)

def produce_infinitely(func):
    """
    Given a function, produce a generator which applies it infinitely.
    """
    import itertools

    for _ in itertools.count():
        yield func()

def generate_lines(filename):
    """
    Given a filename, produce a generator of lines through that file.

    The file will be safely closed.
    """
    with open(filename) as some_file:
        for line in some_file:
            yield line

def load_word_list(filename):
    """
    Given a filename, load a list of words from that file.
    """
    return tuple(
        line.strip().lower()
        for line in
        generate_lines("corncob_lowercase.txt")
    )

def random_http_url(word_list, tld_list):
    """
    Produce a random HTTP URL by taking random words out of a word
    list and joining them together.

    A list of top-level domains will be tried randomly.
    """
    import random

    return "http://{}.{}".format(
        "".join(
            random.choice(word_list)
            for i in
            range(random.randint(1, 3))
        ),
        random.choice(tld_list)
    )

@asyncio.coroutine
def is_site_alive(url):
    """
    Given a URL, fire off an asynchronous request to determine
    if something exists at that URL and return True at the end of the
    coroutine if it does.
    """
    import aiohttp

    try:
        response = yield from aiohttp.request(
            url= url,
            # We'll use GET instead of HEAD, because some web apps
            # will be dumb and wrong and get confused by HEAD.
            method= "GET",
            headers= {
                # Use pretty much the most common user agent for requests.
                "User-Agent": COMMON_USER_AGENT,
            },
        )
    except aiohttp.errors.OsConnectionError:
        return False

    return response.status == 200

@asyncio.coroutine
def print_alive_sites(infinite_url_seq, count= 20):
    """
    Given an infinite sequence of URLs to try, print
    the first :count: URLs which point to locations that exist.
    """
    while count > 0:
        try:
            url = next(infinite_url_seq)

            is_alive = yield from asyncio.wait_for(
                is_site_alive(url),
                timeout= 5
            )

            if not is_alive:
                continue

            print(url)
        except asyncio.TimeoutError:
            continue

        count -= 1

def main():
    word_list = load_word_list("corncob_lowercase.txt")

    tld_list = (
        "com",
        "net",
        "org",
        "co.uk",
    )

    infinite_url_seq = produce_infinitely(
        lambda: random_http_url(word_list, tld_list)
    )

    loop = asyncio.get_event_loop()

    loop.run_until_complete(print_alive_sites(infinite_url_seq))

if __name__ == "__main__":
    main()

