import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'cryptacular',
    'pyramid',
    'pyramid_beaker',
    'pyramid_jinja2',
    'stucco_evolution',
    'SQLAlchemy'
]

setup(name='stucco_auth',
      version='0.3e-4',
      description='stucco_auth',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      license='BSD',
      author='Daniel Holth',
      author_email='dholth@fastmail.fm',
      url='http://bitbucket.org/dholth/stucco_auth',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires + ['nose'],
      test_suite='nose.collector',
      entry_points="""
      [paste.app_factory]
      demo_app = stucco_auth:demo_app
      [paste.filter_app_factory]
      tm = stucco_auth.tm:make_tm
      """,
      paster_plugins=['pyramid'],
      )
