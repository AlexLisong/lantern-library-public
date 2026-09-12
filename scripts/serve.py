"""Serve the ebook locally with byte ranges for reliable audio seeking."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1] / 'dist'

class ReaderHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_head(self):
        self.byte_range = None
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        stream = open(path, 'rb')
        size = os.fstat(stream.fileno()).st_size
        requested = self.headers.get('Range')
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested or '')
        if match and (match[1] or match[2]):
            start = int(match[1]) if match[1] else max(0, size-int(match[2]))
            end = min(size-1, int(match[2])) if match[1] and match[2] else size-1
            if start >= size or end < start:
                stream.close()
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return None
            self.byte_range = (start, end)
            self.send_response(206)
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.send_header('Content-Length', str(end-start+1))
            stream.seek(start)
        else:
            self.send_response(200)
            self.send_header('Content-Length', str(size))
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        remaining = self.byte_range[1]-self.byte_range[0]+1
        while remaining:
            chunk = source.read(min(65536, remaining))
            if not chunk:break
            outputfile.write(chunk)
            remaining -= len(chunk)

if __name__ == '__main__':
    print('Lantern Library: http://localhost:8766', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8766), ReaderHandler).serve_forever()
