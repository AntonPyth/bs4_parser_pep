from pathlib import Path

# URL's for parsing
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEPS_NUMS = 'https://peps.python.org/numerical/'
PEP_URL = 'https://peps.python.org/'


# Other constants
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / 'downloads'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
PRETTY = 'pretty'
FILE = 'file'
RESULT = 'results'

# LOGS
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'

# Statuses
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
