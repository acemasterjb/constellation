from setuptools import setup

include = ['constellation.libs.tools', 'constellation']
requires = ['soundfile', 'playsound', 'tinytag',
            'windows-curses', 'keyboard']

setup(
    name='constellation',
    version='0.1.0',
    packages=include,
    install_requires=requires)
