long_description =  """\
This is a python package of the Manifolds from snappy, separated out.
"""

import re, sys, subprocess, os, shutil, glob, sysconfig
from setuptools import setup, Command
from setuptools.command.build_py import build_py

sqlite_files = ['manifolds.sqlite',
                'more_manifolds.sqlite',
                'platonic_manifolds.sqlite']

def check_call(args):
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        executable = args[0]
        command = [a for a in args if not a.startswith('-')][-1]
        raise RuntimeError(command + ' failed for ' + executable)


class Clean(Command):
    """
    Removes the usual build/dist/egg-info directories as well as the
    sqlite database files.
    """
    user_options = []
    def initialize_options(self):
        pass 
    def finalize_options(self):
        pass
    def run(self):
        for dir in ['build', 'dist'] + glob.glob('*.egg-info'):
            if os.path.exists(dir):
                shutil.rmtree(dir)
        for file in glob.glob('manifold_src/*.sqlite'):
            os.remove(file)


class BuildPy(build_py):
    """
    Rebuilds the sqlite database files if needed.
    """
    def initialize_options(self):
        build_py.initialize_options(self)
        os.chdir('manifold_src')        
        csv_source_files = glob.glob(
            os.path.join('original_manifold_sources', '*.csv'))
        # When there are no csv files, we are in an sdist tarball
        if len(csv_source_files) != 0:
            if self.force:
                for file in glob.glob('*.sqlite'):
                    os.remove(file)
            print('Rebuilding stale sqlite databases from csv sources...')
            check_call([sys.executable, 'make_sqlite_db.py'])
        os.chdir('..')

class Release(Command):
    user_options = [('install', 'i', 'install the release into each Python')]
    def initialize_options(self):
        self.install = False
    def finalize_options(self):
        pass
    def run(self):
        pythons = os.environ.get('RELEASE_PYTHONS', sys.executable).split(',')
        check_call([pythons[0], 'setup.py', 'clean'])
        check_call([pythons[0], 'setup.py', 'bdist_wheel', '--universal'])
        check_call([pythons[0], 'setup.py', 'sdist'])
        if self.install:
            for python in pythons:
                check_call([python, 'setup.py', 'pip_install', '--no-build-wheel'])


class PipInstall(Command):
    user_options = [('no-build-wheel', 'n', 'assume wheel has already been built')]
    def initialize_options(self):
        self.no_build_wheel = False
    def finalize_options(self):
        pass
    def run(self): 
        python = sys.executable
        check_call([python, 'setup.py', 'build'])
        if not self.no_build_wheel:
            check_call([python, 'setup.py', 'bdist_wheel', '--universal'])
        egginfo = 'snappy_manifolds.egg-info'
        if os.path.exists(egginfo):
            shutil.rmtree(egginfo)
        wheels = glob.glob('dist' + os.sep + '*.whl')
        new_wheel = max(wheels, key=os.path.getmtime)            
        check_call([python, '-m', 'pip', 'install', '--upgrade',
                    '--upgrade-strategy', 'only-if-needed',
                    new_wheel])

class Test(Command):
    user_options = []
    def initialize_options(self):
        pass 
    def finalize_options(self):
        pass
    def run(self):
        build_lib_dir = os.path.join(
            'build',
            'lib.{platform}-{version_info[0]}.{version_info[1]}'.format(
                platform=sysconfig.get_platform(),
                version_info=sys.version_info)
        )
        sys.path.insert(0, build_lib_dir)
        from snappy_manifolds.test import run_tests
        sys.exit(run_tests())

    
# Get version number from module
version = re.search("__version__ = '(.*)'",
                    open('python_src/__init__.py').read()).group(1)

setup(
    name = 'snappy_manifolds',
    version = version,
    description = 'Database of snappy manifolds',
    long_description = long_description,
    url = 'https://bitbucket.org/t3m/snappy_manifolds',
    author = 'Marc Culler and Nathan M. Dunfield and Mattias Goerner and Malik Obeidin',
    author_email = 'snappy-help@computop.org, mobeidin@illiois.edu',
    license='GPLv2+',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: C',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Mathematics',
        ],

    packages = ['snappy_manifolds', 'snappy_manifolds/sqlite_files'],
    package_dir = {'snappy_manifolds':'python_src',
                   'snappy_manifolds/sqlite_files':'manifold_src'},
    package_data = {'snappy_manifolds/sqlite_files': sqlite_files},
    ext_modules = [],
    zip_safe = False,
    cmdclass = {'release': Release,
                'build_py': BuildPy,
                'clean': Clean,
                'pip_install':PipInstall,
                'test':Test
    },
)

