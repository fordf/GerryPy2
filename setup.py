
from setuptools import setup, find_packages

# here = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(here, 'README.md')) as f:
#     README = f.read()

requires = [
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'waitress',
    'psycopg2',
    'Flask',
    'Flask-SocketIO',
    'eventlet',
    'GeoAlchemy2'
]

# tests_require = [
#     'WebTest >= 1.3.1',  # py3 compat
#     'pytest',  # includes virtualenv
#     'pytest-cov',
#     'tox',
#     'faker',
#     'pyramid_ipython',
#     'ipython'
# ]

setup(name='gerrypy2',
      version='0.0',
      description='Rebuild of GerryPy using websockets',
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Flask",
      ],
      author='Avery, Patrick, Jordan, Julien, Ford',
      author_email='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      # extras_require={
      #     'testing': tests_require,
      # },
      install_requires=requires,
      )
