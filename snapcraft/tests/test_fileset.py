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


class FilepathPrefixesTestCase(tests.TestCase):
    def test_basic_prefix(self):
        filepath = Filepath('tmp1/tmp2/tmp3')
        prefixes = filepath._get_prefixes()
        expected = ['tmp1/tmp2', 'tmp1']

        self.assertEqual(expected, prefixes)

    def test_single_prefix(self):
        filepath = Filepath('tmp1/tmp2')
        prefixes = filepath._get_prefixes()
        expected = ['tmp1']

        self.assertEqual(expected, prefixes)

    def test_no_prefixes(self):
        filepath = Filepath('tmp1')
        prefixes = filepath._get_prefixes()
        expected = []

        self.assertEqual(expected, prefixes)


class FilepathMatchTestCase(tests.TestCase):
    def test_include_and_exclude_match(self):
        fp1 = Filepath('-tmp')
        fp2 = Filepath('tmp')

        self.assertEqual(fp1, fp2)

    def test_prefix_does_not_match(self):
        fp1 = Filepath('tmp')
        fp2 = Filepath('tmpdir')

        self.assertNotEqual(fp1, fp2)

    def test_directories_match(self):
        fp1 = Filepath('tmp')
        fp2 = Filepath('tmp/')

        self.assertEqual(fp1, fp2)


class FilepathTestCase(tests.TestCase):
    scenarios = [
        ('Basic file', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {},
            'expected': {
                'files': ['stage/tmp', 'prime/tmp'],
            },
        }),
        ('Basic exclude file', {
            'filepath': '-tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp'],
            },
            'updates': {},
            'expected': {
                'not-files': ['stage/tmp', 'prime/tmp'],
            },
        }),
        ('Basic directory', {
            'filepath': 'tmp',
            'is_dir': True,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {},
            'expected': {
                'files': ['stage/tmp/testing', 'prime/tmp/testing'],
            },
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
        ('Organize a directory to a new name', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {
                'organize': {'tmp': 'new'},
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
        ('Organize a directory into a new directory', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp/testing'],
            },
            'updates': {
                'organize': {'tmp': 'new/'},
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
        ('Organize a directory into a new directory with a common prefix', {
            'filepath': 'tmp',
            'is_dir': False,
            'create': {
                'files': ['tmp/testing', 'tmpdir/testing2'],
            },
            'updates': {
                'organize': {'tmp': 'new/'},
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
                                      filepath.install_file)
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

        self.assertTrue(install_path, PathExists())
        if not filepath.is_exclude:
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


class FilesetScenariosTestCase(tests.TestCase):
    scenarios = [
        ('Simple fileset', {
            'filesets': [
                {
                    'filepaths': ['tmp'],
                }
            ],
            'create': {
                'files': ['tmp'],
            },
            'expected': {
                'files': ['stage/tmp', 'prime/tmp'],
            }
        }),
        ('Combined filesets', {
            'filesets': [
                {
                    'filepaths': ['tmp'],
                },
                {
                    'filepaths': ['tmp2'],
                },
            ],
            'create': {
                'files': ['tmp', 'tmp2'],
            },
            'expected': {
                'files': ['stage/tmp', 'prime/tmp',
                          'stage/tmp2', 'prime/tmp2'],
            },
        }),
        ('Combined star and specific filesets', {
            'filesets': [
                {
                    'filepaths': ['*'],
                },
                {
                    'filepaths': ['tmp2'],
                },
            ],
            'create': {
                'files': ['tmp', 'tmp2'],
            },
            'expected': {
                'files': ['stage/tmp', 'prime/tmp',
                          'stage/tmp2', 'prime/tmp2'],
            },
        }),
        ('Combined star and exclude filesets', {
            'filesets': [
                {
                    'filepaths': ['*'],
                },
                {
                    'filepaths': ['-tmp2'],
                },
            ],
            'create': {
                'files': ['tmp', 'tmp2'],
            },
            'expected': {
                'files': ['stage/tmp', 'prime/tmp'],
                'not-files': ['stage/tmp2', 'prime/tmp2'],
            },
        }),
        ('Combined dir/star and exclude filesets', {
            'filesets': [
                {
                    'filepaths': ['tmp/*'],
                },
                {
                    'filepaths': ['-tmp/tmp2'],
                },
            ],
            'create': {
                'files': ['tmp/tmp1', 'tmp/tmp2'],
            },
            'expected': {
                'files': ['stage/tmp/tmp1', 'prime/tmp/tmp1'],
                'not-files': ['stage/tmp/tmp2', 'prime/tmp/tmp2'],
            },
        }),
        ('Combined specific and exclude filesets', {
            'filesets': [
                {
                    'filepaths': ['tmp', 'tmp2'],
                },
                {
                    'filepaths': ['-tmp2'],
                },
            ],
            'create': {
                'files': ['tmp', 'tmp2'],
            },
            'expected': {
                'files': ['stage/tmp', 'prime/tmp'],
                'not-files': ['stage/tmp2', 'prime/tmp2'],
            },
        }),
    ]

    def _create_files_and_dirs(self):
        files_to_create = self.create.get('files', [])
        dirs_to_create = self.create.get('dirs', [])

        for file_to_create in files_to_create:
            file_to_create = os.path.join('install', file_to_create)
            os.makedirs(os.path.dirname(file_to_create), exist_ok=True)
            with open(file_to_create, 'w') as fp:
                fp.write('testing')

        for dir_to_create in dirs_to_create:
            os.makedirs(dir_to_create, exist_ok=True)

    def test_scenarios(self):
        logging.getLogger().setLevel(logging.DEBUG)
        filesets = self.filesets
        fs_list = []

        os.makedirs('install')
        os.makedirs('stage')
        os.makedirs('prime')

        # create files and directories needed for the test scenario
        self._create_files_and_dirs()

        combined_fileset = Fileset()
        for fileset in filesets:

            # create the fileset
            fs = Fileset()

            # add filepaths
            for filepath in fileset.get('filepaths', []):
                fs.add(filepath)

            fs_list.append(fs)
            combined_fileset += fs

        # perform fileset steps
        combined_fileset.organize(fileset.get('organize', {}))
        combined_fileset.stage()
        combined_fileset.prime()

        # Check that expected files exist
        for fs in fs_list:
            for fp in fs.files:
                if fp.install_file and fp.install_file[0] != '-':
                    self.assertTrue(fp.install_path, PathExists())
                    self.assertThat(fp.stage_path, PathExists())
                    self.assertThat(fp.prime_path, PathExists())

        # check that expected files and directories exist.
        expected_files = self.expected.get('files', [])
        expected_dirs = self.expected.get('dirs', [])

        for expected_file in expected_files:
            self.assertThat(expected_file, FileExists())

        for expected_dir in expected_dirs:
            self.assertThat(expected_dir, DirExists())

        # check that not expected files and directories do not exist.
        not_expected_files = fileset.get(
            'expected', {'files': []}).get('not-files', [])
        not_expected_dirs = fileset.get(
            'expected', {'dirs': []}).get('not-dirs', [])

        for not_expected_file in not_expected_files:
            self.assertThat(not_expected_file, Not(FileExists()))

        for not_expected_dir in not_expected_dirs:
            self.assertThat(expected_dir, Not(DirExists()))


class FilesetCombinationScenariosTestCase(tests.TestCase):

    scenarios = [
        ('Fileset basic', {
            'filesets': [
                {'filepaths': ['testing']},
            ],
            'expected_files_count': 1,
        }),
        ('Fileset add', {
            'filesets': [
                {'filepaths': ['testing']},
                {'filepaths': ['testing2']},
            ],
            'expected_files_count': 2,
        }),
        ('Fileset sub', {
            'filesets': [
                {'filepaths': ['testing', 'testing2']},
                {'filepaths': ['testing2'], 'type': 'sub'},
            ],
            'expected_files_count': 1,
        }),
    ]

    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        super().setUp()

    def test_scenarios(self):

        os.makedirs('install')
        os.makedirs('stage')
        os.makedirs('prime')

        combined = Fileset()
        for fileset in self.filesets:
            filepaths = fileset.get('filepaths', [])
            fs_type = fileset.get('type', 'add')

            # Create the install files
            for filepath in filepaths:
                src = os.path.join('install', filepath)
                with open(src, 'w') as fp:
                    fp.write('testing')

            # Create the fileset
            fs = Fileset(*filepaths)
            if fs_type == 'add':
                combined += fs
            elif fs_type == 'sub':
                combined -= fs
        self.assertEqual(self.expected_files_count, len(combined.files))

        combined.stage()
        for fp in combined.files:
            self.assertThat(fp.install_path, PathExists())
            self.assertThat(fp.stage_path, PathExists())
