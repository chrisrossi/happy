from setuptools import setup, find_packages
import sys, os

version = '1.0-dev'

INSTALL_REQUIRES=[
    'WebOb'
]

setup(name='fried',
      version=version,
      description="Collection of disposable web components--an antiframework.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=INSTALL_REQUIRES,
      tests_require=INSTALL_REQUIRES + ['nose', 'coverage'],
      test_suite='fried',
      entry_points={
          }
      )
