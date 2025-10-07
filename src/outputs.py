import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, FILE, PRETTY, RESULT


def control_output(results, cli_args):
    output_handlers = {
        PRETTY: pretty_output,
        FILE: file_output,
    }

    output = cli_args.output
    handler = output_handlers.get(output, default_output)
    handler(results, cli_args)


def default_output(*args):
    results = args[0]
    for row in results:
        print(*row)


def pretty_output(*args):
    results = args[0]
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(*args):
    results, cli_args = args
    results_dir = BASE_DIR / RESULT
    try:
        results_dir.mkdir(exist_ok=True)
    except OSError as e:
        logging.error(f"Ошибка при создании директории: {e}")
        return
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
        writer.writerows(results)
    logging.info('Файл с результатами был сохранён: %s', file_path)
