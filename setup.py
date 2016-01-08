#!/usr/bin/env python3

from distutils.core import setup

setup(name='flask-mediabrowser',
      version='0.0.1',
      description='HTTP media browsing and streaming/transcoding',
      author='Yves Fischer',
      author_email='yvesf+mediabrowser@xapek.org',
      url='https://www.xapek.org/git/yvesf/flask-mediabrowser',
      packages=['mediabrowser'],
      include_package_data=True,  # use MANIFEST.in during install
      scripts=['flask-mediabrowser'],
      install_requires=['Flask==0.10.1']
      )
