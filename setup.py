from setuptools import setup, find_packages

include = ['constellation.libs.tools']
requires = ['soundfile', 'playsound', 'tinytag',
            'windows-curses']

setup(
    name='constellation',
    version='0.1.0',
    packages=find_packages(include),
    install_requires=requires)
