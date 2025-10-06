class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""


class PageLoadError(Exception):
    """Исключение, при ошибке загрузки страницы."""
    def __init__(self, url, message="Ошибка при загрузке страницы"):
        self.url = url
        self.message = message
        super().__init__(f"{self.message}: {self.url}")


class VersionListNotFoundError(Exception):
    """Ошибка, поиска списка с версиями Python."""
    def __init__(self, message="Список с версиями Python не найден"):
        self.message = message
        super().__init__(self.message)
