# import setuptools
from distutils.core import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='tfswinlib-pkg-ergorion',
      version='1.4.3',
      author='Axel Seibert',
      author_email='software at ergorion.com',
      description='tfswinlib provides a comfort layer for working with Microsofts TeamFoundationServer using the TFS API.',
      long_description=long_description,
      long_description_content_type="text/x-rst",
      url='https://github.com/ergorion/tfswinlib',
      py_modules=['tfswinlib'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Environment :: Win32 (MS Windows)",
        "Development Status :: 5 - Production/Stable"
    ],
      python_requires='>=3.0'
      )
