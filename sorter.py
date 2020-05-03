import os                   # Модуль для работы с файловой системой
import click                # Модуль для реализации CLI
import eyed3 as mp3         # Модуль для парсинга mp3-тегов
from colorama import Fore   # Модуль для кроccплатформенного форматирования
from colorama import init   # консольного вывода


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


def mp3_processor(path, all_ver=False):
    """
    Function `mp3_processor(path).`
    Analyzes ID3 tags of file from `path` and generate new path according some rules.
    """
    try:
        f = mp3.load(path)  # Файл
    except PermissionError:
        print(Fore.RED + f'Недостаточно прав для чтения файла {path}')
    else:
        t = f.tag           # Тег
        result = path       # По умолчанию как результат возвращаем исходный путь
        if not all_ver and (t.version[0] < 2):  # Фильтруем по версии (если фильтр включен)
            print(Fore.YELLOW + f'Предупреждение: Недопустимая версия тега ID3 для {path}')
            return result
        if t.artist and t.album:    # Если оба тега не пусты, формируем новый путь
            album = t.album.lstrip().rstrip()
            artist = t.artist.lstrip().rstrip()
            title = t.title.lstrip().rstrip() if t.title else os.path.basename(path)[:-4]
            result = os.path.join(artist, album, f'{title} - {artist} - {album + ".mp3"}')
        else:                       # Если хотя бы 1 пуст - выводим сообщение
            print(Fore.YELLOW + f'Предупреждение: Теги "исполнитель" или "альбом" не определены для {path}')
        return result


def move(src, dst, notify=True):
    """
    Function `move(src, dst, notify).`
    Moves files from `src` path to `dst` path.
    To disable console logging - clear `notify` flag (set `False`).
    """
    if src == dst:  # Проверяем на идентичность путей
        return False
    try:
        try:
            os.renames(src, dst)        # Пытаемся переместить файл
        except FileExistsError:         # Если в директории назначения он уже существует
            os.replace(src, dst)        # Делаем замену
            d = os.path.dirname(src)    # Получаем путь к папке, откуда забрали файл
            if not os.listdir(d):       # Проверяем на "пустоту", т.к. метод replace не удаляет за собой пустые папки
                os.removedirs(d)        # Если файлов нет - удаляем
    except PermissionError:             # Если нет прав для перемещения
        print(Fore.RED + f'Недостаточно прав доступа для перемещения {src} -> {dst}')
        return False
    else:
        if notify:  # Если вызов с флагом "notify", то
            print(Fore.GREEN + f'{src} -> {dst};')  # выводим сообщение в лог
        return True


@click.command()
@click.option('-s', '--src_dir', default=os.getcwd(), help='Source directory')
@click.option('-d', '--dst_dir', default=os.getcwd(), help='Destination directory')
@click.option('-n', '--nested', default=False, help='Searching nested files inside subdirectories. Set "True" to enable')
@click.option('-c', '--create', default=False, help='Auto create destination directory. Set "True" to enable ')
@click.option('-a', '--all_ver', default=False, help='Analyze all ID3 versions (not only V2+). Set "True" to enable ')
def sort(src_dir, dst_dir, nested=False, create=False, all_ver=False):
    """
    Simple program that sorts mp3-files.
    Analyzes files ID3-tags data and moves them from `src_dir` into new directories, sorted by `artist` and `album` like:

    <dst_dir>/<Artist_1>/<Album_1>/Track_1 - Artist_1 - Album_1.mp3
    <dst_dir>/<Artist_1>/<Album_1>/Track_2 - Artist_1 - Album_1.mp3
    <dst_dir>/<Artist_1>/<Album_2>/Track_3 - Artist_1 - Album_2.mp3
    <dst_dir>/<Artist_2>/<Album_3>/Track_4 - Artist_2 - Album_3.mp3
    ... etc.
    """
    total = 0   # Файлов всего
    audio = 0   # Файлов mp3
    moved = 0   # Файлов перемещено

    # Предварительные проверки. Позволяют не начинать итерирование, если не выполняются обязательные условия
    if not os.path.isdir(src_dir):                  # Проверяем исходный путь на директорию
        if not allowed_x(src_dir, 'exist'):         # Проверяем наличие исходной директории,
            return                                  # Если она не существует - выходим
        else:                                       # Если существует, но не директория
            print(Fore.RED + f'Путь {src_dir} не является директорией')     # Выводим сообщение
            return                                  # и выходим

    if not allowed_x(dst_dir, 'exist'):             # Проверяем наличие директории назначения, если её нет и
        if not create:                              # если вызваны без флага автосоздания директории
            print(Fore.YELLOW + 'Хотите создать директорию [y - да / n - выход]?',  end=' ')   # предлагаем создать
            if input() != 'y':
                return                              # Если пользователь не хочет создавать - выходим
    else:
        if not allowed_x(dst_dir, 'write'):         # Если директория назначения существует,
            return                                  # но прав на запись в неё не имеем - выходим

    # Основной алгоритм
    for d, dirs, files in os.walk(src_dir):         # Итерируемся по дереву
        if not allowed_x(d, 'write'):               # Проверяем разрешение на запись в папке (чтобы переименовать файл),
            continue                                # если его нету - идём в следующую директорию
        for file in files:                          # Итерируемся по файлам
            total += 1
            if file.endswith('.mp3'):               # Если формат - mp3
                audio += 1
                old = os.path.join(d, file)         # Получаем "старый" путь
                new = os.path.join(dst_dir, mp3_processor(old, all_ver))     # Формируем новый путь
                if move(old, new):                  # Пробуем переместить файл
                    moved += 1
        if not nested:                              # Если запустились в режиме "поверхностного поиска" - выходим,
            break                                   # т.к. корневую директорию уже проверили

    print(Fore.BLUE + f'''===========================
Статистика
===========================
Обнаружено файлов всего: {total}
Из них mp3-файлов: {audio}
Перемещено: {moved}
Не удалось переместить: {audio - moved}
===========================
Done.
    ''')


if __name__ == '__main__':
    init(autoreset=True)        # Инициализация с автосбросом цвета текста на значение по умолчанию после вызова print()
    mp3.log.setLevel("ERROR")   # Отключаем вывод предупреждений. Теперь в консоль будут выводиться только ошибки.
    sort()                      # Запуск основной функции
