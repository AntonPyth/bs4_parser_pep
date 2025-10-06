import logging
import re
from pathlib import Path
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR,
    EXPECTED_STATUS,
    MAIN_DOC_URL,
    PEP_URL,
    PEPS_NUMS,
)
from outputs import control_output
from utils import find_tag, get_response


def fetch_and_parse(session, url):
    """Получает страницу по URL и парсит её."""
    response = get_response(session, url)
    return BeautifulSoup(response.text, features='lxml')


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]

    main_section = find_tag(
        soup,
        'section',
        attrs={'id': 'what-s-new-in-python'}
    )
    if main_section is None:
        raise RuntimeError('Раздел "What\'s New" не найден на странице')

    toctree = find_tag(main_section, 'div', attrs={'class': 'toctree-wrapper'})
    if toctree is None:
        raise RuntimeError('Список версий в "What\'s New" не найден')

    sections_by_python = toctree.find_all('li', attrs={'class': 'toctree-l1'})

    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        if version_a_tag is None or 'href' not in version_a_tag.attrs:
            continue
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        v_resp = session.get(version_link)
        v_resp.encoding = 'utf-8'
        v_soup = BeautifulSoup(v_resp.text, 'lxml')

        h1 = find_tag(v_soup, 'h1')
        dl = find_tag(v_soup, 'dl')
        h1_text = h1.text.strip() if h1 else ''
        dl_text = dl.text.replace('\n', ' ').strip() if dl else ''

        results.append((version_link, h1_text, dl_text))

    # Вывод в терминал для отладки (опционально)
    for row in results[1:]:  # Пропускаем заголовки при печати
        print(*row)

    return results


def latest_versions(session):
    # response = session.get(MAIN_DOC_URL)
    # response.encoding = 'utf-8'
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    if sidebar is None:
        raise RuntimeError('Sidebar not found')

    ul_tags = sidebar.find_all('ul')

    a_tags = None
    for ul in ul_tags:
        if 'All versions' in ul.get_text():
            a_tags = ul.find_all('a')
            break
    if not a_tags:
        raise RuntimeError('Ничего не нашлось')

    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag.get('href', '')
        absolute_link = urljoin(MAIN_DOC_URL, link)
        text_match = re.search(pattern, a_tag.get_text())
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.get_text(), ''
        results.append((absolute_link, version, status))

    for row in results[1:]:  # Пропускаем заголовки при печати
        print(*row)

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    # response = session.get(downloads_url)
    # response.encoding = 'utf-8'
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_tag = find_tag(soup, 'div', attrs={'role': 'main'})
    if main_tag is None:
        raise RuntimeError(
            'Главный блок (role=main) не найден на странице '
            'загрузок'
        )
    table_tag = find_tag(main_tag, 'table', attrs={'class': 'docutils'})
    if table_tag is None:
        raise RuntimeError('Таблица с загрузками не найдена')

    pdf_a4_tag = find_tag(
        table_tag,
        'a',
        attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    if pdf_a4_tag is None:
        raise RuntimeError('Ссылка на pdf-a4.zip не найдена')

    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)

    filename = archive_url.rstrip('/').split('/')[-1]
    print(f'Ссылка на файл: {archive_url}')

    downloads_dir = Path(BASE_DIR) / 'downloads'
    downloads_dir.mkdir(exist_ok=True)

    archive_path = downloads_dir / filename

    # Скачивание архива
    file_resp = session.get(archive_url)
    file_resp.raise_for_status()
    with open(archive_path, 'wb') as f:
        f.write(file_resp.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')

    # return [('Скачанный файл', str(archive_path))]


def pep(session):
    soup = fetch_and_parse(session, PEPS_NUMS)
    tr_tag = soup.find_all('tr')
    results = [('Статус', 'Количество'), ]
    actual_statuses = {}
    total_peps = len(tr_tag) - 1
    log_messages = []
    for i in tqdm(range(1, len(tr_tag))):
        try:
            table_pep_status = find_tag(tr_tag[i], 'abbr').text[1:]
            expected_status = EXPECTED_STATUS[table_pep_status]
            pep_link = urljoin(PEP_URL, tr_tag[i].a['href'])
            soup = fetch_and_parse(session, pep_link)
            pep_card_dl_tag = find_tag(
                soup,
                'dl',
                {'class': 'rfc2822 field-list simple'}
            )
            for tag in pep_card_dl_tag:
                if tag.name == 'dt' and tag.text == 'Status:':
                    pep_card_status = tag.next_sibling.next_sibling.string
                    actual_statuses[pep_card_status] = actual_statuses.get(
                        pep_card_status, 0
                    ) + 1
                    if pep_card_status not in expected_status:
                        log_messages.append(
                            f'Несовпадающие статус для:{pep_link}\n'
                            f'Статус в карточке: {pep_card_status}\n'
                            f'Статус в общей таблице: {expected_status}'
                        )
        except Exception as e:
            log_messages.append(f'Ошибка при выполнении парсера: {e}')
    results.extend(actual_statuses.items())
    results.append(('Total', total_peps))
    for message in log_messages:
        logging.info(message)
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if parser_mode != 'download' and results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
