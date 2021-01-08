import os
import json

import pygal
from pygal.style import Style
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from pytmangadex import Mangadex

retry = Retry(total=4, status_forcelist=[500], backoff_factor=0.3)
session = requests.Session()
mangadex = Mangadex()
mangadex.session.mount('https://mangadex.org', HTTPAdapter(max_retries=retry))


def main(manga_id):
    progress = 0

    manga = mangadex.get_manga(manga_id)
    print(f'Starting {manga.title}')

    if os.path.isfile(f'{manga_id}.json'):
        with open(f'{manga_id}.json') as f:
            chapter_to_page_count = {float(key): value for key, value in json.load(f).items()}
    else:
        # Map chapters to ids, 9097 is MangaPlus, and page count is not available for it
        # Select the chapter with the most views to get better accuracy
        chapters_to_ids = {}
        for chapter in manga.chapters:
            if not chapter['chapter']:
                # Oneshots probably
                continue
            chapter_num = float(chapter['chapter'])
            if chapter['groups'][0] != 9097:
                if chapter['views'] > chapters_to_ids.get(chapter_num, {}).get('views', 0):
                    chapters_to_ids[chapter_num] = chapter

        # Sort and extract id
        chapters_to_ids = {key: value['id'] for key, value in sorted(chapters_to_ids.items())}

        chapter_to_page_count = {}
        for chapter, id_ in chapters_to_ids.items():
            chapter_to_page_count[chapter] = len(mangadex.get_chapter(id_).pages) - 1  # Group credits page
            progress += 1
            print(f'\rProgress: {progress}/{len(chapters_to_ids)}', end='')
        print('\n')

        with open(f'{manga_id}.json', 'w') as f:
            json.dump(chapter_to_page_count, f)

    return manga.title, [x for x in chapter_to_page_count.items() if not (int(x[0]) != x[0] and x[1] < 10)]


if __name__ == '__main__':
    chart_style = Style(title_font_size=30)
    for id_ in [607, 429, 39, 5, 3056, 7139, 82, 12714, 35, 558,
                2334, 286, 6770, 8436, 13502, 19531, 939, 18198, 1073, 84]:

        name, page_count = main(id_)

        conf = pygal.Config(title=name,
                            y_title='Page Count',
                            x_title='Chapter',
                            show_legend=False,
                            style=chart_style,
                            width=2000)

        chart = pygal.XY(config=conf)
        chart.add(name, page_count)
        chart.render_in_browser()
        chart.render_to_file(f'{name}.svg')
        chart.render_to_png(f'{name}.png')
