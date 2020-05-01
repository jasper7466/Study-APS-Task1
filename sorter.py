import os
import click
import eyed3 as mp3


@click.command()
@click.option('-s', '--src_dir', default=os.getcwd(), help='Source directory')
@click.option('-d', '--dst_dir', default=os.getcwd(), help='Destination directory')
def sort(src_dir, dst_dir):
    """Simple program that sorts mp3-files."""
    print(src_dir)
    print(dst_dir)


if __name__ == '__main__':
    sort()
