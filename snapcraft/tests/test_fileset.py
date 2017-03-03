# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2017 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import glob
import logging
import os

from snapcraft import tests
from snapcraft.fileset import Filepath, Fileset

from testtools.matchers import (
    DirExists,
    FileExists,
    Not,
    PathExists,
)


class FilepathTestCase(tests.TestCase):
    scenarios = [
        ('Basic filepath', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {},
            'expected': {},
        }),
        ('Setting install file', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['blah'],
            },
            'updates': {
                'install_file': 'blah',
            },
            'expected': {},
        }),
        ('Setting stage file', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {
                'stage_file': 'blah',
            },
            'expected': {},
        }),
        ('Basic install directory', {
            'filepath': 'tmp',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {},
            'expected': {},
        }),
        ('Setting install file with directory', {
            'filepath': 'tmp',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing', 'blah/testing'],
            },
            'updates': {
                'install_file': 'blah',
            },
            'expected': {
                'files': [
                    'stage/blah/testing',
                    'prime/blah/testing',
                ],
                'dirs': [
                    'stage/blah',
                    'prime/blah',
                ],
                'not-files': ['stage/tmp/testing'],
                'not-dirs': ['stage/tmp'],
            }
        }),
        ('Setting stage file to directory', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {
                'stage_file': 'blah/',
            },
            'expected': {
                'files': [
                    'stage/blah/tmp',
                    'prime/blah/tmp',
                ],
                'dirs': [
                    'stage/blah',
                    'prime/blah',
                ],
            }

        }),
        ('Stage dot directory to a new directory', {
            'filepath': '.',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {
                'stage_file': 'new',
            },
            'expected': {
                'files': [
                    'stage/new/tmp/testing',
                    'prime/new/tmp/testing',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                    'stage/new/tmp',
                    'prime/new/tmp',
                ],
            }

        }),
        ('Stage star directory to a new directory', {
            'filepath': '*',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {
                'stage_file': 'new',
            },
            'expected': {
                'files': [
                    'stage/new/tmp/testing',
                    'prime/new/tmp/testing',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                    'stage/new/tmp',
                    'prime/new/tmp',
                ],
            }

        }),
        ('Stage current directory to a new directory', {
            'filepath': '',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {
                'stage_file': 'new',
            },
            'expected': {
                'files': [
                    'stage/new/tmp/testing',
                    'prime/new/tmp/testing',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                    'stage/new/tmp',
                    'prime/new/tmp',
                ],
            }

        }),
        ('Organize basic', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {
                'organize': {'tmp': 'new-tmp'},
            },
            'expected': {
                'files': [
                    'stage/new-tmp',
                    'prime/new-tmp',
                ],
            }

        }),
        ('Organize into a directory', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {
                'organize': {'tmp': 'new/'},
            },
            'expected': {
                'files': [
                    'stage/new/tmp',
                    'prime/new/tmp',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                ]
            }

        }),
        ('Organize into a directory with a new name', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {
                'organize': {'tmp': 'new/new-tmp'},
            },
            'expected': {
                'files': [
                    'stage/new/new-tmp',
                    'prime/new/new-tmp',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                ]
            }

        }),
        ('Organize star into a directory', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {
                'organize': {'*': 'new'},
            },
            'expected': {
                'files': [
                    'stage/new/tmp',
                    'prime/new/tmp',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                ]
            }

        }),
        ('Organize dir/star into a directory', {
            'filepath': 'tmp',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {
                'organize': {'tmp/*': 'new'},
            },
            'expected': {
                'files': [
                    'stage/new/testing',
                    'prime/new/testing',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                ]
            }

        }),
        ('Organize dir1/dir2/star into a directory', {
            'filepath': 'temp/tmp',
            'is_dir': True,
            'create': {
                'files': ['temp/tmp/testing'],
            },
            'updates': {
                'organize': {'temp/tmp/*': 'new'},
            },
            'expected': {
                'files': [
                    'stage/new/testing',
                    'prime/new/testing',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                ]
            }

        }),
        ('Organize several directories into a directory', {
            'filepath': '*',
            'is_dir': True,
            'create': {
                'files': ['dir1/tmp/testing1',
                          'dir2/subdir/testing2'],
            },
            'updates': {
                'organize': {'*/*': 'new'}
            },
            'expected': {
                'files': [
                    'stage/new/tmp/testing1',
                    'stage/new/subdir/testing2',
                ],
                'dirs': [
                    'stage/new',
                    'stage/new/tmp',
                    'stage/new/subdir',
                ]
            }

        }),
        ('Organize dir1/star with a sub directory into a directory', {
            'filepath': '*',
            'is_dir': True,
            'create': {
                'files': ['temp/tmp/testing'],
            },
            'updates': {
                'organize': {'temp/*': 'new'},
            },
            'expected': {
                'files': [
                    'stage/new/tmp/testing',
                    'prime/new/tmp/testing',
                ],
                'dirs': [
                    'stage/new',
                    'prime/new',
                    'stage/new/tmp',
                    'prime/new/tmp',
                ]
            }

        }),
    ]

    def test_scenarios(self):
        logging.getLogger().setLevel(logging.DEBUG)
        filepath = Filepath(self.filepath)

        install_file = self.updates.get('install_file',
                                        filepath.install_file)
        filepath.install_file = install_file

        stage_file = self.updates.get('stage_file',
                                      filepath.stage_file)
        filepath.stage_file = stage_file

        expected_files = self.expected.get('files', [])
        expected_dirs = self.expected.get('dirs', [])
        not_expected_files = self.expected.get('not-files', [])
        not_expected_dirs = self.expected.get('not-dirs', [])

        self.assertEqual('install', filepath.install_dir)
        self.assertEqual('stage', filepath.stage_dir)
        self.assertEqual('prime', filepath.prime_dir)

        self.assertEqual(filepath.install_file, install_file)
        self.assertEqual(filepath.stage_file, stage_file)

        self.assertEqual(os.path.join('install', install_file),
                         filepath.install_path)
        self.assertEqual(os.path.join('stage', stage_file),
                         filepath.stage_path)
        self.assertEqual(os.path.join('prime', stage_file),
                         filepath.prime_path)

        os.makedirs('install')
        os.makedirs('stage')
        os.makedirs('prime')

        files_to_create = self.create.get('files', [])
        dirs_to_create = self.create.get('dirs', [])

        for file_to_create in files_to_create:
            file_to_create = os.path.join('install', file_to_create)
            os.makedirs(os.path.dirname(file_to_create), exist_ok=True)
            with open(file_to_create, 'w') as fp:
                fp.write('testing')

        for dir_to_create in dirs_to_create:
            os.makedirs(dir_to_create, exist_ok=True)

        organize_fs = self.updates.get('organize', {})
        if organize_fs:
            entries = organize_fs.keys()
            self.assertEqual(1, len(entries))

            filepath.organize(*(organize_fs.popitem()))
        filepath.stage()
        filepath.prime()

        install_path = filepath.install_path.strip('/')
        stage_path = filepath.stage_path.strip('/')
        prime_path = filepath.prime_path.strip('/')

        self.assertTrue(glob.glob(install_path))
        self.assertThat(stage_path, PathExists())
        self.assertThat(prime_path, PathExists())

        for expected_file in expected_files:
            self.assertThat(expected_file, FileExists())

        for expected_dir in expected_dirs:
            self.assertThat(expected_dir, DirExists())

        for not_expected_file in not_expected_files:
            self.assertThat(not_expected_file, Not(FileExists()))

        for not_expected_dir in not_expected_dirs:
            self.assertThat(not_expected_dir, Not(DirExists()))


class FilepathSymlinkTestCase(tests.TestCase):

    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        super().setUp()

    def test_stage_filepath_symlink_only(self):
        os.makedirs('install')
        os.makedirs('stage')
        os.makedirs('prime')

        src = os.path.join('install', 'testing')
        link = os.path.join('install', 'test-link')
        dst = os.path.join('stage', 'test-link')
        with open(src, 'w') as fp:
            fp.write('testing')

        os.chdir('install')
        os.symlink(os.path.basename(src), os.path.basename(link))
        os.chdir('..')

        filepath = Filepath('test-link', follow_symlinks=False)

        filepath.stage()

        self.assertTrue(os.path.islink(dst))

    def test_stage_filepath_follow_symlink(self):
        os.makedirs('install')
        os.makedirs('stage')
        os.makedirs('prime')

        src = os.path.join('install', 'testing')
        link = os.path.join('install', 'test-link')
        dst = os.path.join('stage', 'test-link')
        with open(src, 'w') as fp:
            fp.write('testing')

        os.chdir('install')
        os.symlink(os.path.basename(src), os.path.basename(link))
        os.chdir('..')

        filepath = Filepath('test-link', follow_symlinks=True)

        filepath.stage()

        self.assertTrue(not os.path.islink(dst))
        self.assertTrue(os.path.exists(dst))


class FilesetTestCase(tests.TestCase):

    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        super().setUp()

    def test_fileset_basic(self):
        filepath = Filepath('testing')
        fileset = Fileset()
        fileset.add(filepath)

        os.makedirs('install')
        os.makedirs('stage')
        os.makedirs('prime')

        src = os.path.join('install', 'testing')
        dst = os.path.join('stage', 'testing')
        with open(src, 'w') as fp:
            fp.write('testing')

        fileset.stage()

        self.assertThat(src, FileExists())
        self.assertThat(dst, FileExists())
