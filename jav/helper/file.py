from os import getcwd, remove
from os.path import exists, join, split, splitext
from secrets import token_urlsafe


class NewFile:
    __slots__ = ('ext', 'dir', 'name')

    def __init__(self, ext: str, dirc: str = None):
        self.ext = ext if ext.startswith('.') else f'.{ext}'
        self.dir = dirc if dirc else getcwd()
        self.name = token_urlsafe(16)

    @property
    def filename(self) -> str:
        return f'{self.name}{self.ext}'

    @property
    def fullpath(self) -> str:
        return join(self.dir, self.filename)

    def genpart(self, part: str) -> str:
        return join(self.dir, f'{self.name} part-{part}{self.ext}')

    def remove(self, callback: bool = False) -> None:
        if exists(self.fullpath):
            try:
                remove(self.fullpath)
            except:
                if callback:
                    return None
                print('error menghapus file')
            else:
                if callback:
                    return f'{self.filename} deleted'
                print(f'{self.filename} is deleted')

        return None

    def __repr__(self):
        return self.fullpath


class FilePath(NewFile):

    def __init__(self, filepath: str):
        d, n = split(filepath)
        n, e = splitext(n)
        super().__init__(e, d)
        self.name = n
