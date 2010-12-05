import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
'cryptacular',
'ponzi_evolution',
'pyramid',
'pyramid_beaker',
'pyramid_formish',
'WebError',
]

setup(name='ponzi_auth',
      version='0.0',
      description='ponzi_auth',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Daniel Holth',
      author_email='dholth@fastmail.fm',
      url='http://bitbucket.org/dholth/ponzi_auth',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="ponzi_auth",
      entry_points = """\
      [paste.app_factory]
      main = ponzi_auth:main
      """,
      paster_plugins=['pyramid'],
      )

