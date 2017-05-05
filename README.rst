tfswinlib
---------

tfswinlib provides a comfort layer for working with Microsofts TeamFoundationServer using the TFS API.

It has been tested with CPython 2.7.13 and 3.6.1 and IronPython 2.7.5

Remarks
-------
The routines are compatible with (`python-tfs <https://pypi.python.org/pypi/tfslib>`_, 
in version 0.1.2) which works via SOAP.
In other words, this library can be a drop-in replacement when you want to move from the SOAP
interface to the .Net API.

Prerequisites
-------------
If you are running CPython, you will need the additional module
`pythonnet <https://pypi.python.org/pypi/pythonnet/>`_ (tested with 2.1.0). IronPython does not
need this module.

and of course you need the TFS assemblies from e.g. VisualStudio to talk to the TFS server.

Author
------

This software has been written by `Axel Seibert <http://www.ergorion.com>`_.

