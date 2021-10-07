from datetime import datetime, timedelta
from re import findall
from bitmath import Byte


class ErrInputValue(Exception):
    pass


class HTime:
    __slots__ = ('value')

    def __init__(self, second):
        if isinstance(second, str) and ':' in second:
            self.value: timedelta = timedelta(seconds=self._fromstr(second))
        elif isinstance(second, str):
            self.value: timedelta = timedelta(seconds=float(second))
        elif isinstance(second, (float, int)):
            self.value: timedelta = timedelta(seconds=second)
        else:
            raise ErrInputValue(
                f'input anda [ {second} ] error, periksa kembali')

    def __repr__(self):
        return str(self.value).split(".")[0]

    @staticmethod
    def _fromstr(t: str) -> float:
        if '.' not in t:
            t = f'{t}.0'
        kl = (3600, 60, 1)
        r = findall(r'(\d+)', t)
        if len(r) == 5:
            kl = (86400, 3600, 60, 1)
        hs = [int(r[e]) * kl[e] for e in range(len(r)-1)]
        return float(f'{sum(hs)}.{r[-1]}')

    def sepstring(self, sep: str = ':') -> str:
        m = ('s', 'm', 'h', 'd')
        t = findall(r'(\d+)', str(self.value).split('.')[0])
        t.reverse()
        r = [f'{t[w]}{m[w]}' for w in range(len(t))]
        r.reverse()
        return sep.join(r)


class HSize:
    __slots__ = ('value')

    def __init__(self, size):
        self.value: int = size if isinstance(size, int) else int(size)

    def __repr__(self):
        return Byte(self.value).best_prefix().format('{value:.2f} {unit}')


class HDate:
    __slots__ = ('value')

    def __init__(self, date: datetime = None):
        self.value = datetime.now() if date else date

    def __repr__(self):
        return datetime.strftime(self.date, '%a, %d %b %Y %H:%M:%S')


class HNumber:
    __slots__ = ('value')

    def __init__(self, num):
        if isinstance(num, str) and ',' in num:
            self.value = float(num.replace(',',''))
        else:
            self.value = float(num)

    @staticmethod
    def _revdot(st: str) -> str:
        m = st.split('.')
        if len(m) == 1:
            return f'{m[0].replace(",", ".")}'
        return f'{m[0].replace(",", ".")},{m[1]}'

    def sepstring(self, _float: bool = False) -> str:
        return self._revdot(f'{self.value:,.2f}') if _float else self._revdot(f'{self.value:,.0f}')

    def curency(self, mark: str = '', _float: bool = False) -> str:
        return f'{mark} {self.sepstring(_float)}' if mark else self.sepstring(_float)

    def __repr__(self):
        return self.sepstring()
