import logging

from requests import RequestException

from bs4 import BeautifulSoup

from exceptions import ParserFindTagException


def fetch_and_parse(session, url):
    """Получает страницу по URL и парсит её."""
    response = get_response(session, url)
    return BeautifulSoup(response.text, features='lxml')


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException:
        logging.exception(
            'Возникла ошибка при загрузке страницы %s', url,
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
