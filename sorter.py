import os
import click
import eyed3 as mp3

mp3.log.setLevel("ERROR")   # Отключаем вывод предупреждений. Теперь в консоль будут выводиться только ошибки.


def check_exist(path):  # Работает на Win норм
    return os.access(path, os.F_OK)


def check_read(path):   # Работает на Win норм
    try:
        with open(path) as file:
            temp = file.read()
            file.write('t')
    except PermissionError:
        return False
    return True


def allowed_x(path, *args, notify=True):
    checks = {
        'exist': [os.F_OK, f'Путь {path} не существует'],
        'read': [os.R_OK, f'Недостаточно прав для чтения из {path}'],
        'write': [os.W_OK, f'Недостаточно прав для записи в {path}'],
        'execute': [os.X_OK, f'Недостаточно прав для запуска на выполнение {path}']
    }
    for check in args:
        if not os.access(path, checks[check][0]):
            if notify:
                print(checks[check][1])
            return False
    return True


def mp3_processor(path):
    f = mp3.load(path)
    t = f.tag
    if t.album_artist and t.album:
        result = f'{t.title if t.title else os.path.basename(path)[:-4]} - {t.album_artist} - {t.album + ".mp3"}'
        result = os.path.join(t.album_artist, t.album, result)
    else:
        print(f'Warning: Tags "artist" or "album" not defined for {path}')
        result = path
    return result


def move(src, dst, notify=True):
    try:
        os.renames(src, dst)        # Пытаемся переместить файл
    except FileExistsError:         # Если в директории назначения он уже существует
        os.replace(src, dst)        # Делаем замену
        d = os.path.dirname(src)    # Получаем путь к папке
        if not os.listdir(d):       # Проверяем на "пустоту", т.к. метод replace не удаляет за собой пустые папки
            os.removedirs(d)        # Если файлов нет - удаляем
    finally:
        if notify:
            print(f'{src} -> {dst}')    # Выводим сообщение в лог

@click.command()
@click.option('-s', '--src_dir', default=os.getcwd(), help='Source directory')
@click.option('-d', '--dst_dir', default=os.getcwd(), help='Destination directory')
@click.option('-n', '--nested', default=False, help='Set "True" to enable searching nested files inside subdirectories')
def sort(src_dir, dst_dir, nested=False):
    """Simple program that sorts mp3-files."""
    if not allowed_x(src_dir, 'exist'):             # Проверяем наличие исходной директории,
        return                                      # если она не существует - выходим
    if not allowed_x(dst_dir, 'exist'):             # Проверяем наличие директории назначения, если её нет - то
        if input('Хотите создать директорию [y - да / n - выход]? ') != 'y':    # предлагаем создать
            return                                  # Если пользователь не хочет создавать - выходим
    else:
        if not allowed_x(dst_dir, 'write'):         # Если директория назначения существует,
            return                                  # но прав на запись не имеем - выходим

    for d, dirs, files in os.walk(src_dir):         # Итерируемся по дереву
        if not allowed_x(d, 'write'):               # Проверяем разрещение на запись в папке (чтобы переименовать файл),
            continue                                # если его нету - идём в следующую директорию
        for file in files:                          # Итерируемся по файлам
            if file.endswith('.mp3'):               # Если формат - mp3
                old = os.path.join(d, file)         # Получаем "старый" путь
                new = os.path.join(dst_dir, mp3_processor(old))     # Формируем новый путь
                move(old, new)                      # Перемещаем файл
        if not nested:                              # Если запустились в режиме поверхностного поиска - выходим
            return


if __name__ == '__main__':
    sort()
