import sys
from pathlib import Path
from setuptools import setup, find_packages

if sys.version_info.major != 3:
    raise RuntimeError("This package requires Python 3+")

pkg_name = 'aiosupabase'
gitrepo = 'trisongz/aiosupabase'

root = Path(__file__).parent
version = root.joinpath(f'{pkg_name}/version.py').read_text().split('VERSION = ', 1)[-1].strip().replace('-', '').replace("'", '')

requirements = [
    'aiohttpx',
    'lazyops',
    'postgrest-py==0.10.3',
    'gotrue==0.5.4',
    'realtime==0.0.5',
    'storage3==0.3.5',
]

if sys.version_info.minor < 8:
    requirements.append('typing_extensions')

extras = {}
args = {
    'packages': find_packages(include = [f'{pkg_name}', f'{pkg_name}.*',]),
    'install_requires': requirements,
    'include_package_data': True,
    'long_description': root.joinpath('README.md').read_text(encoding='utf-8'),
    'entry_points': {
        "console_scripts": []
    },
    'extras_require': extras,
}

setup(
    name = pkg_name,
    version = version,
    url=f'https://github.com/{gitrepo}',
    license='MIT License',
    description='Unofficial Asyncronous Python Client for Supabase',
    author='Tri Songz',
    author_email='ts@growthengineai.com',
    long_description_content_type="text/markdown",
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    **args
)