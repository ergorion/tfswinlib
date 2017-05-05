---------
tfswinlib
---------

tfswinlib provides a comfort layer for working with Microsofts TeamFoundationServer using the TFS API.

It has been tested with CPython 2.7.13 and 3.6.1 and IronPython 2.7.5

Remarks
-------
I tried to keep the interface compatible with (`python-tfs <https://pypi.python.org/pypi/tfslib>`_, 
in version 0.1.2) which works via SOAP.
That boils down to the class name (TfsClient), its __init__ parameters and the get_work_item method.

Prerequisites
-------------
If you are running CPython, you will need the additional module
`pythonnet <https://pypi.python.org/pypi/pythonnet/>`_ (tested with 2.1.0). IronPython does not
need this module.

And of course you need the TFS assemblies from e.g. VisualStudio to talk to the TFS server.

Sample Code
-----------

::

import tfswinlib
tfs = tfswinlib.TfsClient("http://<your_server_here>:<port>/tfs/<your collection>")
tfs.connect()
# retrieve a work item by its id
wi = tfs.get_work_item(323356)
# retrieve a work item by its id and revision
wi = tfs.get_work_item(323356, 4)
# and there is a method to simply print each available field of a work item:
tfs.print_work_item (323356)

# if you need to find work items, you can execute a WIQL query:
workItems = tfs.get_list_of_work_items(query)

# when you need to work with the history of states of a work items:
stateHistory = tfs.get_work_item_state_history(323356)
# or rather how long the work item was in each state:
stateDuration = tfs.get_work_item_state_duration(323356)

# there are a couple of helper functions available as well
listOfProjects = tfs.get_list_of_projects()
# from this list you can find the name of your project
storedQueries = tfs.get_list_of_stored_queries_for_project(projectName)

# some queries contain macros, e.g. @me or @project; they are expanded on the server
# and need to be handed over to the get_list_of_work_items function:
params = tfs.prepare_parameter_dictionary_for_query()
workItems = tfs.get_list_of_work_items(query, params)

# it can also be useful to find out which users belong to a certain group:
userNames = tfs.get_list_of_usernames_from_group("[My Team Project]\\Contributors")

Author
------
This software has been written by `Axel Seibert <http://www.ergorion.com>`_.


