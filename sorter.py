import os
import click
import eyed3 as mp3

mp3.log.setLevel("ERROR")   # Отключаем вывод предупреждений. Теперь в консоль будут выводиться только ошибки.


@click.command()
@click.option('-s', '--src_dir', default=os.getcwd(), help='Source directory')
@click.option('-d', '--dst_dir', default=os.getcwd(), help='Destination directory')
@click.option('-n', '--nested', default=False, help='Set "True" for enable searching nested files inside subdirectories')
def sort(src_dir, dst_dir, nested=False):
    """Simple program that sorts mp3-files."""
    n = 0
    for dir, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.mp3'):                       # Если mp3
                f = mp3.load(os.path.join(dir, file))
                if f.tag.album_artist and f.tag.album:      # Если прописаны теги "исполнитель" и "альбом"
                    f.rename('rebase-in-progress')
                    if f.tag.title:                         # Если прописан тег "название"
                        name = f'{f.tag.title} - {f.tag.album_artist} - {f.tag.album}'
                    else:
                        name = f'{file[:-4]} - {f.tag.album_artist} - {f.tag.album}'
                    f.rename(name)
                    os.renames(f.path, os.path.join(dst_dir, f.tag.album_artist, f.tag.album, name + '.mp3'))
                else:
                    print(f'Warning: artist or album not defined for {f.path}')
        if not nested:
            return


if __name__ == '__main__':
    sort()
