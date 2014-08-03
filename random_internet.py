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
def body_text_or_none(url):
    """
    Given a URL, fire off an asynchronous request to return
    the site's body as UTF-8 text. If the request fails for whatever reason,
    None will be returned instead.
    """
    import aiohttp
    import socket
    import ssl

    try:
        response = yield from aiohttp.request(
            url= url,
            method= "GET",
            headers= {
                # Use pretty much the most common user agent for requests.
                "User-Agent": COMMON_USER_AGENT,
            },
        )
    except aiohttp.errors.OsConnectionError:
        return None
    except socket.error:
        return None
    except ssl.CertificateError:
        return None

    if response.status != 200:
        # Nothing returned here.
        return None

    # Read the document now.
    body = yield from response.read()

    return body.decode("utf-8", "ignore")

class Counter:
    """
    This object is a decrementing counter. It is initialised with
    an integer. That integer will be decremented until it hits zero.
    Once it hits zero, Counter.Complete will be raised.
    """
    class Complete(Exception):
        pass

    def __init__(self, count):
        self.__count = count

    def decrement(self):
        """
        Decrement the counter.

        If the counter hits zero, Counter.Complete will be raised.
        """
        self.__count -= 1

        if self.__count == 0:
            raise Counter.Complete()

@asyncio.coroutine
def handle_single_site(counter, url, handler, body_test_func):
    """
    Open the site. If the site is alive according to returning status 200
    and the :body_test_func: returning True, then pass the URL for the
    site to the handler function and decrement the counter.
    """
    try:
        body = yield from asyncio.wait_for(
            body_text_or_none(url),
            timeout= 5
        )
    except asyncio.TimeoutError:
        return

    if body is None:
        return

    if not body_test_func(body):
        return

    handler(url)
    counter.decrement()

@asyncio.coroutine
def handle_living_sites(infinite_url_seq, handler, body_test_func,
batch_size, count):
    """
    Given an infinite sequence of URLs to try, print
    the first :count: URLs which point to locations that exist.
    """
    counter = Counter(count)

    # Loop through sites in batch sizes until we have collected as
    # many random results as we can.
    try:
        while True:
            yield from asyncio.gather(*[
                handle_single_site(
                    counter= counter,
                    url= next(infinite_url_seq),
                    handler= handler,
                    body_test_func= body_test_func,
                )
                for _ in range(batch_size)
            ])
    except Counter.Complete:
        return

def value_from(key, dictionary):
     """
     Given a key and a dictionary, take a value from the dictionary
     matching the given key.
     """
     return dictionary[key]

def main():
    import webbrowser
    import re

    def parse_args():
        import argparse

        parser = argparse.ArgumentParser(
            description= "Retrieve a random sample of the Internet",
        )

        parser.add_argument(
            "--count",
            type= int,
            help= (
                "The number of valid URLs to retrieve."
                " (default 20)"
            ),
            default= 20
        )

        parser.add_argument(
            "--batch-size",
            type= int,
            help= (
                "The batch size to fetch with. "
                "This should generally be larger than the 'count'."
                " (default 100)"
            ),
            default= 100
        )

        parser.add_argument(
            "--handler",
            help= (
                "The handler to use for the retrieved URLs. "
                "'print' and will print results to stdout. "
                "'browser' will open all links in the default browser."
                " (default 'print')"
            ),
            choices= (
                "print",
                "browser",
            ),
            default= "print",
        )

        return parser.parse_args()

    arguments = parse_args()

    count = arguments.count
    batch_size = arguments.batch_size
    handler = value_from(arguments.handler, {
        "print": print,
        "browser": webbrowser.open,
    })

    word_list = load_word_list("corncob_lowercase.txt")

    tld_list = (
        "com",
        "net",
        "org",
        "co.uk",
    )

    PARKED_RE = re.compile("|".join((
        # If you mention these domain registrars, it's parked.
        r"namecheap\.com",
        r"123reg\.co\.uk",
        r"tactic\.co\.uk",
        r"godaddy\.com",
        r"easynic\.com",
        r"directnic\.com",
        r"hostmonstrer\.com",
        r"dreamhost\.com",
        r"easily\.co\.uk",
        r"livetodot\.com",
        r"webhosting\.yahoo\.com",
        r"smallbusiness\.yahoo\.com",
        r"webmailer\.de",
        # Strings for vulture companies which park websites.
        r"future media architects",
        r"sedoparking\.com",
        r"digimedia\.com",
        r"buydomains\.com",
        r"domainnamesales\.com",
        r"smartname\.com",
        r"cajun\.domains",
        r"1and1\.com",
        r"secureserver\.net",
        r"directdomains\.com",
        r"buydomainnames\.co\.uk",
        r"rmgserving\.com",
        r"domainfort\.com",
        # This appears in comments on some Sedo Holding pages.
        r"turing_cluster_prod",
        # This appears on some garbage pages. Either Sedo or Yahoo.
        r"<html><head></head><body><!-- vbe --></body></html>",
        # This JavaScript cookie line appears on some parked pages.
        r"document\.cookie = \"jsc=1\";",
        # A few parked sites have this PHP script thing.
        r"log_click\.php\?",
        # If these ever appear anywhere in a page, it's definitely parked.
        r"domainpark",
        r"registrar parking",
        # This is in some URLs for German domain parkers.
        r"domanregistrering",
        # This appears in some shit parked JavaScript.
        r"applyFrameKiller",
        # Look for strings which talk about selling the domain.
        r"full list of domains",
        r"domain names? for sale",
        # "is for sale" and "may be for sale", etc. only appear on parked shit.
        r"(?:is|may ?be) (?:availiable)? for sale",
        r"for enquiries about this domain",
        r"domain(?: name) is available",
        r"get your domain name",
        r"whois",
        r"has been reserved for future use",
        # Plesk garbage
        r"parallels\.com",
        # This happens on broken Apache pages we don't care about.
        r"site temporarily unavailable",
        r"403 Forbidden",
        # Seen on some default Apache pages.
        r"<h1 align=\"center\">It Worked!</h1>",
        # Anything which talks about search results or 'listings'
        r"below are sponsored listings",
        r"related searches",
        # Filter out JS bullshit
        r"requires javascript",
    )), re.IGNORECASE | re.DOTALL)

    asyncio.get_event_loop().run_until_complete(
        handle_living_sites(
            infinite_url_seq= produce_infinitely(
                lambda: random_http_url(word_list, tld_list)
            ),
            handler= handler,
            body_test_func= lambda body: PARKED_RE.search(body) is None,
            batch_size= batch_size,
            count= count,
        )
    )

if __name__ == "__main__":
    main()

