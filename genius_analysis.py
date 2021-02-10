import os
import time
import uuid
from typing import Iterator, Iterable
from collections import Counter
from functools import wraps

from bs4 import BeautifulSoup
import requests


def repeat_after_delay_on_error(func, delay=0.5):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except (AttributeError, requests.exceptions.HTTPError) as error:
                print(f"An error occurred args={repr(args)}, kwargs={repr(kwargs)}")
                print(error)
            time.sleep(delay)

    return wrapper


def get_soup(url: str) -> BeautifulSoup:
    page = requests.get(url).content
    return BeautifulSoup(page, features="html.parser")


@repeat_after_delay_on_error
def get_song_lyrics(song_url: str) -> str:
    return get_soup(song_url).find("div", attrs={"class": "lyrics"}).text


def get_words_counters_sum_from_all_albums(albums_urls: Iterable[str]) -> Counter:
    word_counter = Counter()
    for lyrics in get_all_lyrics_from_songs_from_albums(albums_urls):
        word_counter.update(get_words_counter(lyrics))
    return word_counter


def get_all_lyrics_from_songs_from_albums(albums_urls: Iterable[str]) -> str:
    for album_url in albums_urls:
        for song_url in get_songs_urls_from_album(album_url):
            yield get_song_lyrics(song_url)


@repeat_after_delay_on_error
def get_songs_urls_from_album(album_url: str) -> Iterator[str]:
    if "genius.com/albums" not in album_url:
        raise ValueError("Wrong album url")

    for a in get_soup(album_url).find_all("a", attrs={"class": "u-display_block", "object": None}):
        yield a["href"]


def get_words_counter(lyrics: str) -> Counter:
    return Counter(get_normalized_words(lyrics))


def get_normalized_words(lyrics: str) -> list:
    lyrics = get_text_without_punctuation_marks(lyrics)
    lyrics = lyrics.lower()
    return [word for word in lyrics.split() if is_proper_word(word)]


def get_text_without_punctuation_marks(text: str) -> str:
    for punctuation_mark in '!"+,-.:?„':
        text = text.replace(punctuation_mark, "")
    return text


def is_proper_word(word: str) -> bool:
    return word.isalnum() and not (word.isdigit() or is_lyrics_info_section(word))


def is_lyrics_info_section(text: str) -> bool:
    for section_tag in "[](){}":
        if section_tag in text:
            return True
    return False


if __name__ == "__main__":
    albums = [
        "https://genius.com/albums/Taco-hemingway/Jarmark",
    ]

    file_name = f"lyrics_analysis.txt"
    if os.path.isfile(file_name):
        print("File already exists. Override? y/N")
        while True:
            answer = input().lower()
            if answer == "y":
                break
            if answer == "n" or not answer:
                raise FileExistsError

    counter = get_words_counters_sum_from_all_albums(albums)

    with open(file_name, "w", encoding="utf-8") as analysis_result:
        for key in sorted(counter, key=lambda k: counter[k], reverse=True):
            analysis_result.write(f"{key}: {counter[key]}\n")

    print(f"Analysis saved to {file_name}")
