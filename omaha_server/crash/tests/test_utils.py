# coding: utf8

"""
This software is licensed under the Apache 2 license, quoted below.

Copyright 2014 Crystalnix Limited

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
"""

import os

from mock import patch

from django import test
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse

from crash.utils import (
    get_stacktrace,
    add_signature_to_frame,
    parse_stacktrace,
    get_signature,
    send_stacktrace_sentry,
)

from crash.models import Crash
from test_stacktrace_to_json import stacktrace


BASE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(BASE_DIR, 'testdata')
SYMBOLS_PATH = os.path.join(TEST_DATA_DIR, 'symbols')
CRASH_DUMP_PATH = os.path.join(TEST_DATA_DIR, '7b05e196-7e23-416b-bd13-99287924e214.dmp')
STACKTRACE_PATH = os.path.join(TEST_DATA_DIR, 'stacktrace.txt')


class ShTest(test.TestCase):
    def test_get_stacktrace(self):
        with open(STACKTRACE_PATH, 'rb') as f:
            stacktrace = f.read()

        rezult, stderr = get_stacktrace(CRASH_DUMP_PATH)

        self.assertEqual(rezult, stacktrace)


class SignatureTest(test.TestCase):
    test_data = [
        ({'frame': 0,
          'module': 'bad.dll',
          'function': 'Func(A * a,B b)',
          'file': 'hg:hg.m.org/repo/name:dname/fname:rev',
          'line': 576},
         {'function': 'Func(A* a, B b)',
          'short_signature': 'Func',
          'line': 576,
          'file': 'hg:hg.m.org/repo/name:dname/fname:rev',
          'frame': 0,
          'signature': 'Func(A* a, B b)',
          'module': 'bad.dll'}),
        ({'file': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
          'frame': 0,
          'function': 'crashedFunc()',
          'line': 34,
          'module': 'BreakpadTestApp.exe'},
         {'file': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
          'frame': 0,
          'function': 'crashedFunc()',
          'line': 34,
          'module': 'BreakpadTestApp.exe',
          'short_signature': 'crashedFunc',
          'signature': 'crashedFunc()'})
    ]

    def test_add_signature_to_frame(self):
        for i in self.test_data:
            self.assertDictEqual(add_signature_to_frame(i[0]), i[1])

    def test_parse_stacktrace(self):
        stacktrace_dict = parse_stacktrace(stacktrace)
        self.assertDictEqual(stacktrace_dict['crashing_thread']['frames'][0],
                             {'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                              'frame': 0,
                              'function': 'crashedFunc()',
                              'lineno': 34,
                              'filename': 'BreakpadTestApp.exe',
                              'short_signature': 'crashedFunc',
                              'signature': 'crashedFunc()'})

    def test_get_signature(self):
        self.assertEqual(get_signature(parse_stacktrace(stacktrace)), 'crashedFunc()')


class SendStackTraceTest(test.TestCase):
    @patch('crash.utils.client')
    @test.override_settings(HOST_NAME='example.com')
    def test_send_stacktrace_sentry(self, mock_client):
        meta = dict(
            lang='en',
            version='1.0.0.1',
        )
        crash = Crash(
            pk=123,
            upload_file_minidump=SimpleUploadedFile('./dump.dat', False),
            stacktrace=stacktrace,
            stacktrace_json=parse_stacktrace(stacktrace),
            appid='{D0AB2EBC-931B-4013-9FEB-C9C4C2225C8C}',
            userid='{2882CF9B-D9C2-4edb-9AAF-8ED5FCF366F7}',
            meta=meta,
            signature='signature',
        )

        send_stacktrace_sentry(crash)

        extra = {
            'crash_admin_panel_url': 'http://{}{}'.format(
                'example.com',
                reverse('admin:crash_crash_change', args=(crash.pk,))),
            'crashdump_url': crash.upload_file_minidump.url,
            'lang': 'en',
            'version': '1.0.0.1'}

        data = {
            'sentry.interfaces.User': {
                'id': '{2882CF9B-D9C2-4edb-9AAF-8ED5FCF366F7}'
            },
            'sentry.interfaces.Exception': {
                'values': [
                    {'stacktrace': {
                        'frames': [
                            {'function': 'crashedFunc()',
                             'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                             'short_signature': 'crashedFunc',
                             'frame': 0,
                             'filename': 'BreakpadTestApp.exe',
                             'lineno': 34,
                             'signature': 'crashedFunc()'},
                            {'function': 'deeperFunc()',
                             'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                             'short_signature': 'deeperFunc',
                             'frame': 1,
                             'filename': 'BreakpadTestApp.exe',
                             'lineno': 39,
                             'signature': 'deeperFunc()'},
                            {'function': 'deepFunc()',
                             'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                             'short_signature': 'deepFunc',
                             'frame': 2,
                             'filename': 'BreakpadTestApp.exe',
                             'lineno': 44,
                             'signature': 'deepFunc()'},
                            {'function': 'anotherFunc()',
                             'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                             'short_signature': 'anotherFunc',
                             'frame': 3,
                             'filename': 'BreakpadTestApp.exe',
                             'lineno': 49,
                             'signature': 'anotherFunc()'},
                            {'function': 'someFunc()',
                             'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                             'short_signature': 'someFunc',
                             'frame': 4,
                             'filename': 'BreakpadTestApp.exe',
                             'lineno': 54,
                             'signature': 'someFunc()'}, {
                                'function': 'func()',
                                'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                                'short_signature': 'func',
                                'frame': 5,
                                'filename': 'BreakpadTestApp.exe',
                                'lineno': 59,
                                'signature': 'func()'},
                            {'function': 'wmain',
                             'abs_path': 'c:\\work\x08reakpadtestapp\x08reakpadtestapp\x08reakpadtestapp.cpp',
                             'short_signature': 'wmain',
                             'frame': 6,
                             'filename': 'BreakpadTestApp.exe',
                             'lineno': 84,
                             'signature': 'wmain'}, {
                                'function': '__tmainCRTStartup',
                                'abs_path': 'f:\\dd\x0bctools\\crt_bld\\self_x86\\crt\\src\\crtexe.c',
                                'short_signature': '__tmainCRTStartup',
                                'frame': 7,
                                'filename': 'BreakpadTestApp.exe',
                                'lineno': 579,
                                'signature': '__tmainCRTStartup'},
                            {'frame': 8,
                             'module_offset': '0x13676',
                             'signature': 'kernel32.dll@0x13676',
                             'short_signature': 'kernel32.dll@0x13676',
                             'filename': 'kernel32.dll'},
                            {'frame': 9,
                             'module_offset': '0x39d41',
                             'signature': 'ntdll.dll@0x39d41',
                             'short_signature': 'ntdll.dll@0x39d41',
                             'filename': 'ntdll.dll'}],
                        'total_frames': 11, 'threads_index': 0},
                     'type': 'EXCEPTION_ACCESS_VIOLATION_WRITE',
                     'value': '0x0'}
                ]
            }
        }

        tags = {
            'cpu_arch': 'x86',
            'cpu_count': 4,
            'appid': '{D0AB2EBC-931B-4013-9FEB-C9C4C2225C8C}',
            'cpu_info': 'GenuineIntel family 6 model 42 stepping 7',
            'os': 'Windows NT',
            'os_ver': '6.1.7600'
        }

        mock_client.capture.assert_called_once_with(
            'raven.events.Message', message='signature',
            extra=extra,
            data=data,
            tags=tags,
        )
