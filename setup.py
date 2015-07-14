import os

from setuptools import setup


README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='robopycode',
    version='2.0',
    packages=['robopycode'],
    include_package_data=True,
    license='BSD License',
    description='The package allows you to create Tank Battlezone game for programmers.',
    long_description=README,
    url='https://github.com/suguby/robopycode',
    author='Shandrinov Vadim',
    author_email='suguby@gmail.com',
    classifiers=[
        'Development Status :: 2.0 - RC',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        # 'robogame_engine==git+git@github.com:suguby/robogame_engine.git#egg=0.2',
    ]
)
