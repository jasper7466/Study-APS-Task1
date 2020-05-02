import os
import click
import eyed3 as mp3
from colorama import Fore   # Модуль для кросплатформенного форматирования
from colorama import init   # консольного вывода


def check_exist(path):  # Работает на Win
    return os.access(path, os.F_OK)


def check_read(path):   # Работает на Win только для файлов
    try:
        with open(path) as file:
            temp = file.read()
    except PermissionError:
        return False
    return True


def allowed_x(path, *args, notify=True):    # Проверка прав доступа. На ОС Windows работает частично
    """
    Function allowed_x(path, *args, notify=True)
    Checks access to files and directories.
    Types of access (*args): 'exist', 'read', 'write', 'execute'.
    Returns `True` if `path` passed all specified checks.
    To disable console logging - clear `notify` flag (set `False`).
    """
    checks = {
        'exist': [os.F_OK, f'Путь {path} не существует'],
        'read': [os.R_OK, f'Недостаточно прав для чтения из {path}'],
        'write': [os.W_OK, f'Недостаточно прав для записи в {path}'],
        'execute': [os.X_OK, f'Недостаточно прав для запуска на выполнение {path}']
    }
    for check in args:
        if not os.access(path, checks[check][0]):
            if notify:
                print(Fore.RED + checks[check][1])
            return False
    return True


def mp3_processor(path):
    """
    Function `mp3_processor(path).`
    Analyzes ID3 tags of file from `path` and generate new path according some rules.
    """
    f = mp3.load(path)  # Файл
    t = f.tag           # Тег
    if t.album_artist and t.album:  # Если оба тега не пусты, формируем новый путь
        result = f'{t.title if t.title else os.path.basename(path)[:-4]} - {t.album_artist} - {t.album + ".mp3"}'
        result = os.path.join(t.album_artist, t.album, result)
    else:                           # Если хотя бы 1 пуст - выводим сообщение
        print(Fore.RED + f'Warning: Tags "artist" or "album" not defined for {path}')
        result = path               # Как результат вернём исходный путь
    return result


def move(src, dst, notify=True):
    """
    Function `move(src, dst, notify).`
    Moves files from `src` path to `dst` path.
    To disable console logging - clear `notify` flag (set `False`).
    """
    try:
        os.renames(src, dst)        # Пытаемся переместить файл
    except FileExistsError:         # Если в директории назначения он уже существует
        os.replace(src, dst)        # Делаем замену
        d = os.path.dirname(src)    # Получаем путь к папке, откуда забрали файл
        if not os.listdir(d):       # Проверяем на "пустоту", т.к. метод replace не удаляет за собой пустые папки
            os.removedirs(d)        # Если файлов нет - удаляем
    finally:
        if notify:                                  # Если вызов с флагом "notify", то
            print(Fore.GREEN + f'{src} -> {dst}')   # выводим сообщение в лог


@click.command()
@click.option('-s', '--src_dir', default=os.getcwd(), help='Source directory')
@click.option('-d', '--dst_dir', default=os.getcwd(), help='Destination directory')
@click.option('-n', '--nested', default=False, help='Searching nested files inside subdirectories. Set "True" to enable')
@click.option('-c', '--create', default=False, help='Auto create destination directory. Set "True" to enable ')
def sort(src_dir, dst_dir, nested=False, create=False):
    """Simple program that sorts mp3-files."""

    # Предварительные проверки
    if not os.path.isdir(src_dir):                  # Проверяем исходный путь на директорию
        if not allowed_x(src_dir, 'exist'):         # Проверяем наличие исходной директории,
            return                                  # Если она не существует - выходим
        else:                                       # Если существует, но не директория
            print(Fore.RED + f'Путь {src_dir} не является директорией')
        return

    if not allowed_x(dst_dir, 'exist'):             # Проверяем наличие директории назначения, если её нет - то
        if not create:                              # Если без вызваны флага автосоздания директории
            print(Fore.YELLOW + 'Хотите создать директорию [y - да / n - выход]?',  end=' ')   # предлагаем создать
            if input() != 'y':
                return                              # Если пользователь не хочет создавать - выходим
    else:
        if not allowed_x(dst_dir, 'write'):         # Если директория назначения существует,
            return                                  # но прав на записьв неё не имеем - выходим

    # Основной алгоритм
    for d, dirs, files in os.walk(src_dir):         # Итерируемся по дереву
        if not allowed_x(d, 'write'):               # Проверяем разрешение на запись в папке (чтобы переименовать файл),
            continue                                # если его нету - идём в следующую директорию
        for file in files:                          # Итерируемся по файлам
            if file.endswith('.mp3'):               # Если формат - mp3
                old = os.path.join(d, file)         # Получаем "старый" путь
                new = os.path.join(dst_dir, mp3_processor(old))     # Формируем новый путь
                if new != old:                      # Проверяем на идентичность путей
                    move(old, new)                  # Перемещаем файл, если они различны
        if not nested:                              # Если запустились в режиме "поверхностного поиска" - выходим,
            return                                  # т.к. корневую директорию уже проверили


if __name__ == '__main__':
    init(autoreset=True)        # Инициализация с автосбросом цвета текста на значение по умолчанию после вызова print()
    mp3.log.setLevel("ERROR")   # Отключаем вывод предупреждений. Теперь в консоль будут выводиться только ошибки.
    sort()                      # Запуск основной функции
