# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2020 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import select
import socket
import threading
import wave

try:
    import nacl.secret
    from nacl.exceptions import CryptoError
except ImportError:
    pass

log = logging.getLogger(__name__)

__all__ = [
    'AudioSink',
    'WaveSink'
]

class AudioSink:
    def __del__(self):
        self.cleanup()

    def write(self, data):
        raise NotImplementedError

    def cleanup(self):
        pass


class WaveSink(AudioSink):
    def __init__(self, destination):
        self._file = wave.open(destination, 'wb')
        self._file.setnchannels(Decoder.CHANNELS)
        self._file.setsampwidth(Decoder.SAMPLE_SIZE//Decoder.CHANNELS)
        self._file.setframerate(Decoder.SAMPLING_RATE)

    def write(self, data):
        self._file.writeframes(data)

    def cleanup(self):
        try:
            self._file.close()
        except:
            pass

class AudioReader(threading.Thread):
    def __init__(self, sink, client, *, after=None):
        super().__init__(daemon=True)
        self.sink = sink
        self.client = client
        self.after = after

        if after is not None and not callable(after):
            raise TypeError('Expected a callable for the "after" parameter.')

        self.after = after

        self._current_error = None
        self._end = threading.Event()
        self._decoder_lock = threading.Lock()

        self.decoder = BufferedDecoder(self)
        self.decoder.start()

        # TODO: inject sink functions

