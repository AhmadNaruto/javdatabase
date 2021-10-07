import json
import subprocess as sp
from asyncio import (create_subprocess_exec, create_task, iscoroutinefunction,
                     run, sleep)
from asyncio.subprocess import PIPE, Process
from dataclasses import dataclass
from re import compile
from typing import Callable

from rich.progress import Progress

from .humanize import HSize, HTime

"""
Output from ffmpeg with optin ( -progress pipe:1)
===========
frame=120
fps=23.20
stream_0_0_q=-1.0
bitrate= 746.1kbits/s
total_size=363749
out_time_us=3900065
out_time_ms=3900065
out_time=00:00:03.900065
dup_frames=0
drop_frames=0
speed=0.754x
progress=end
"""
pattern = compile(
    r'(frame|fps|bitrate|total_size|out_time|speed|progress)\=\s?(\S+)'
)

cmd_collection = {
    'm3u8_option': [
        '-protocol_whitelist','file,http,https,tcp,tls,crypto',
        '-allowed_extensions', 'ALL'
    ],
    'get_frames': [
        '-select_streams', 'v:0',
        '-count_packets',
        '-show_entries', 'stream=nb_read_packets',
        '-of', 'csv=p=0',
        '-of', 'json'
    ]
}


@dataclass(frozen=True)
class Result:
    frame: int
    fps: float
    bitrate: float
    total_size: HSize
    video_time: HTime
    speed: float
    finished: bool


class FProgress(dict):
    __slots__ = ()

    def __init__(self, data):
        super().__init__(data)

    @property
    def to_object(self):
        return Result(
            frame=int(self.get('frame')),
            fps=float(self.get('fps')),
            bitrate=float(0 if self.get('bitrate') in ('N/A', None)
                          else self.get('bitrate').replace('kbits/s', '')),
            total_size=HSize(self.get('total_size')),
            video_time=HTime(self.get('out_time')),
            speed=float(0 if self.get('speed') ==
                        'N/A' else self.get('speed').replace('x', '')),
            finished=True if self.get('progress') == 'end' else False
        )


class Downloader:
    __slots__ = ("file","_cmd","_option","outname","_result", "_process")

    def __init__(self, filein:str=None, fileout:str=None, option: list = [], cmd_args: list = ['-c', 'copy']):
        self.file = filein
        self._cmd = cmd_args
        self._option = option
        self.outname = fileout
        self._result: FProgress = FProgress({
            'frame': 0,
            'fps': 00.00,
            'bitrate': '0.0kbits/s',
            'total_size': 0,
            'out_time': '00:00:01.00000',
            'speed': '0x',
            'progress': 'continue'
        })
        self._process: Process = None
    
    def filein(self, files):
        self.file = files
        return self

    def fileout(self, files):
        self.outname = files
        return self

    def option(self, option:list):
        self._option = option
        return self

    def extra(self, cmd):
        self._cmd = cmd
        return self

    async def aclose(self):
        await self._process.terminate()

    def _get_totalframe(self):
        data = sp.run([
            'ffprobe', '-v', 'error', *cmd_collection['get_frames'], self.file
        ], stdout=sp.PIPE).stdout
        mdict = json.loads(data)  # Convert data from JSON string to dictionary
        # Get the total number of frames.
        return int(mdict['streams'][0]['nb_read_packets'])

    async def execute(self, rich_progres: str = None, callback=None, delay=1):
        self._process = await create_subprocess_exec(
            *['ffmpeg', '-y', '-v', 'error', *self._option, '-i', self.file, *
                self._cmd, '-progress', 'pipe:1', self.outname],
            stdout=PIPE
        )
        if self._process.returncode is not None:
            raise Exception('[error] bad command')

        create_task(self.progress_reader())
        if rich_progres:
            await self._richexecute(rich_progres, delay)
        else:
            await self._getprocess(callback, delay)

    async def _richexecute(self, rich_str, delay):
        with Progress() as proc:
            bar = proc.add_task(rich_str, total=self._get_totalframe())
            while not proc.finished:
                proc.update(bar, completed=int(self._result['frame']))
                await sleep(delay)

    async def _getprocess(self, callback: Callable = None, delay=1):
        while True:

            if isinstance(callback, Callable):
                create_task(callback(Result(*self._result.values()))) if iscoroutinefunction(
                    callback) else callback(Result(*self._result.values()))
            else:
                # print(self._result)
                print(self._result.to_object)

            if self._result.to_object.finished:
                break

            await sleep(delay)
        """
        if self._process.returncode == 0:
            pass
        else:
            raise Exception('terjadi error di prosess')
        """
    async def _readstdout(self):
        if self._process.stdout.at_eof():
            return None
        r = []
        for _ in range(12):
            t = await self._process.stdout.readline()
            r.append(t.decode())
        return ' '.join(r)

    async def progress_reader(self):
        while True:
            progress_text = await self._readstdout()
            if progress_text in (None, ''):
                break
            # print(progress_text)
            self._result.update({
                key: value for key, value in pattern.findall(progress_text) if key != ''
            })

            if self._process.returncode is not None:
                break


if __name__ == '__main__':
    files = 'mardigu.mkv'
    goman = Downloader(files, 'test.mp4', ['-c', 'copy'])
    """
    def get_totalframe():
        data = sp.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-count_packets',
            '-show_entries', 'stream=nb_read_packets',
            '-of', 'csv=p=0',
            '-of', 'json', files
        ], stdout=sp.PIPE).stdout
        mdict = json.loads(data)  # Convert data from JSON string to dictionary
        # Get the total number of frames.
        return int(mdict['streams'][0]['nb_read_packets'])
    """
    def cla(pa):
        print(pa)

    run(goman.execute())

    # print(goman._process.returncode)
