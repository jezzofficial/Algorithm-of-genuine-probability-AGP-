import argparse
import datetime
import json
import os
import sys

from agp_core import pick

try:
    import colorama
    R, G, Y, B, W = (
        colorama.Fore.RED,
        colorama.Fore.GREEN,
        colorama.Fore.YELLOW,
        colorama.Fore.BLUE,
        colorama.Fore.WHITE,
    )
except ImportError:
    R = G = Y = B = W = ""


TEXTS = {
    "ru": {
        "prog": "AGP — генератор случайного ответа с перекосом бакетов",
        "elements_help": "исходные варианты (можно указать несколько)",
        "file_help": "читать варианты из текстового файла (по одному на строку)",
        "zero_help": "интерактивный ввод до символа 0, без указания количества",
        "count_help": "сколько чисел строить на основе сида (по умолчанию 10000)",
        "lang_help": "язык интерфейса: ru или en",
        "history_help": "файл истории (по умолчанию history.jsonl)",
        "no_history_help": "не сохранять результат в историю",
        "count_prompt": "Сколько элементов? (int): ",
        "count_again": "Нужно целое число. Попробуйте ещё раз.",
        "count_positive": "Нужно хотя бы 1. Попробуйте ещё раз.",
        "elem_prompt": "Элемент {i}: ",
        "zero_hint": "Вводите элементы по одному. Введите 0, чтобы закончить.",
        "zero_elem_prefix": "Элемент {i} (",
        "zero_elem_suffix": " — завершить): ",
        "no_elements": "Не введено ни одного элемента. Запустите программу ещё раз.",
        "empty_skipped": "Пустая строка пропущена.",
        "dup_warn": "Внимание: элемент «{el}» уже есть в списке.",
        "interrupted": "Прервано пользователем.",
        "eof_note": "Конец ввода.",
        "file_read_err": "Не удалось прочитать файл «{path}»: {err}",
        "seed_line": "Сгенерированный сид:",
        "buckets_line": "Размеры бакетов:",
        "winner_line": "Победитель:",
        "history_saved": "Результат сохранён в истории: {path}",
        "history_err": "Не удалось записать историю в «{path}»: {err}",
    },
    "en": {
        "prog": "AGP — biased-bucket random answer generator",
        "elements_help": "source variants (several allowed)",
        "file_help": "read variants from a text file (one per line)",
        "zero_help": "interactive input until 0, without a count",
        "count_help": "how many numbers to build from the seed (default 10000)",
        "lang_help": "interface language: ru or en",
        "history_help": "history file (default history.jsonl)",
        "no_history_help": "do not save the result to history",
        "count_prompt": "How many elements? (int): ",
        "count_again": "An integer is required. Try again.",
        "count_positive": "At least 1 is required. Try again.",
        "elem_prompt": "Element {i}: ",
        "zero_hint": "Enter elements one by one. Enter 0 to finish.",
        "zero_elem_prefix": "Element {i} (",
        "zero_elem_suffix": " — finish): ",
        "no_elements": "No elements entered. Run the program again.",
        "empty_skipped": "Empty line skipped.",
        "dup_warn": "Warning: element «{el}» is already in the list.",
        "interrupted": "Interrupted by user.",
        "eof_note": "End of input.",
        "file_read_err": "Cannot read file «{path}»: {err}",
        "seed_line": "Generated seed:",
        "buckets_line": "Bucket sizes:",
        "winner_line": "Winner:",
        "history_saved": "Result appended to history: {path}",
        "history_err": "Cannot write history to «{path}»: {err}",
    },
}


def detect_lang(argv):
    tokens = list(argv) if argv is not None else sys.argv[1:]
    for i, tok in enumerate(tokens):
        if tok in ("-l", "--lang") and i + 1 < len(tokens):
            value = tokens[i + 1]
            return value if value in TEXTS else "ru"
        if tok.startswith("--lang="):
            value = tok.split("=", 1)[1]
            return value if value in TEXTS else "ru"
    return "ru"


def _positive_int(value):
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if n < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return n


def build_parser(t, force_mode=None):
    parser = argparse.ArgumentParser(prog="AGP", description=t["prog"])
    parser.add_argument("elements", nargs="*", help=t["elements_help"])
    parser.add_argument("-f", "--file", metavar="PATH", help=t["file_help"])
    parser.add_argument("--zero", action="store_true", help=t["zero_help"])
    parser.add_argument(
        "--count", type=_positive_int, default=10000, metavar="N",
        help=t["count_help"],
    )
    parser.add_argument(
        "-l", "--lang", choices=sorted(TEXTS), default=None, help=t["lang_help"],
    )
    parser.add_argument("--history", metavar="PATH", help=t["history_help"])
    parser.add_argument("--no-history", action="store_true", help=t["no_history_help"])
    if force_mode == "zero":
        parser.set_defaults(zero=True)
    return parser


def duplicates_of(elements):
    seen = set()
    dups = set()
    for el in elements:
        if el in seen:
            dups.add(el)
        seen.add(el)
    return dups


def read_from_file(path):
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\r\n") for line in f]


def read_until_zero(t):
    print(B + t["zero_hint"] + W)
    elements = []
    i = 1
    while True:
        try:
            prompt = (
                B + t["zero_elem_prefix"].format(i=i)
                + G + "0" + B + t["zero_elem_suffix"] + W
            )
            el = input(prompt)
        except EOFError:
            print()
            print(t["eof_note"])
            break
        if el.strip() == "0":
            break
        if not el.strip():
            print(R + t["empty_skipped"] + W)
            continue
        if el in elements:
            print(Y + t["dup_warn"].format(el=el) + W)
        elements.append(el)
        i += 1
    return elements


def read_by_count(t):
    while True:
        try:
            raw = input(B + t["count_prompt"] + W)
        except EOFError:
            print()
            print(t["eof_note"])
            return []
        try:
            n = int(raw)
        except ValueError:
            print(R + t["count_again"] + W)
            continue
        if n < 1:
            print(R + t["count_positive"] + W)
            continue
        break

    elements = []
    i = 1
    while len(elements) < n:
        try:
            el = input(t["elem_prompt"].format(i=i))
        except EOFError:
            print()
            print(t["eof_note"])
            break
        if not el.strip():
            print(R + t["empty_skipped"] + W)
            continue
        if el in elements:
            print(Y + t["dup_warn"].format(el=el) + W)
        elements.append(el)
        i += 1
    return elements


def _gather(args, t):
    if args.file:
        raw = read_from_file(args.file)
        elements = [el for el in raw if el.strip()]
        if len(elements) != len(raw):
            print(Y + t["empty_skipped"] + W)
        return "file", elements
    if args.elements:
        return "cli", list(args.elements)
    if args.zero:
        return "zero", read_until_zero(t)
    return "count", read_by_count(t)


def append_history(path, record):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv=None, force_mode=None):
    lang = detect_lang(argv)
    t = TEXTS[lang]
    parser = build_parser(t, force_mode=force_mode)
    args = parser.parse_args(argv)
    if args.lang:
        t = TEXTS[args.lang]

    try:
        source, elements = _gather(args, t)
    except KeyboardInterrupt:
        print()
        print(R + t["interrupted"] + W)
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(R + t["file_read_err"].format(path=args.file, err=e) + W)
        return 1

    if not elements:
        print(R + t["no_elements"] + W)
        return 1

    if source in ("file", "cli"):
        for el in sorted(duplicates_of(elements)):
            print(Y + t["dup_warn"].format(el=el) + W)

    try:
        winner, seed, buckets = pick(elements, count=args.count)
    except ValueError as e:
        print(R + str(e) + W)
        return 1

    print('-----------')
    print(G + t["seed_line"] + W, seed)
    print(Y + t["buckets_line"] + W, [len(b) for b in buckets])
    print('-----------')
    print(t["winner_line"], winner)

    if not args.no_history:
        record = {
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "source": source,
            "elements": elements,
            "seed": seed,
            "bucket_sizes": [len(b) for b in buckets],
            "winner": winner,
        }
        path = args.history or "history.jsonl"
        try:
            append_history(path, record)
            print(t["history_saved"].format(path=path))
        except OSError as e:
            print(Y + t["history_err"].format(path=path, err=e) + W, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
