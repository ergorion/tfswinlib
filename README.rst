---------
tfswinlib
---------

tfswinlib provides a comfort layer for working with Microsofts TeamFoundationServer using the TFS API.

It has been tested with CPython 2.7.13, 3.6.1, 3.7.4 and IronPython 2.7.5
It support the Windows plattform only.

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

How to get started
------------------

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
    # when you want to access single fields, you can either access it directly:
    print (wi.State)
    # or the more general way:
    print (wi.Fields['State'].Value)
    # and the number of Fields....
    print (wi.Fields.Count)
    # when you need the links of a work item:
    links = wi.Links
    # you can iterate over this list, e.g.:
    for link in links:
        try:
            print (' %s --> %s' % (link.LinkTypeEnd.Name, link.RelatedWorkItemId))
        except:
            print (link.ArtifactLinkType.Name)
    # similarly, it is easy to access the attachments:
    attachments = wi.Attachments


Retrieving a list of WorkItems 
------------------------------

Before you can work on a single wi, you need to find it. And often you want to
retrieve a list of work items that all satisfy a certain condition:

::
    
    # if you need to find work items, you can execute a WIQL query:
    query = """SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Feature'"""
    workItems = tfs.get_list_of_work_items(query)

    # you can then iterate over this list either with a counter:
    for i in range(workItems.Count): print (workItems[i].Id)
    # or:
    for wi in workItems: print (wi.Id)


You get all the features of WIQL (retrieving all types of work items, or
using the ASOF operator):

::
    
    # for historical analysis or reports, you can execute a WIQL query:
    # I assume that the date format depends on your regional settings, here you can
    # see my date format (European format). 
    ccbDate = '01.12.2020'
	query = """SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Feature' asof '%s'""" % ccbDate
	workItems = tfs.get_list_of_work_items(query)


Code Reviews
------------

Code Reviews basically are work items of a special type. You can retrieve a list of all
code review requests (as seen in the example above). And from there, you can follow e.g.
the links from each requests to also see the responses.

::

	query = """SELECT [System.Id], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'Code Review Request'"""
	workItems = tfs.get_list_of_work_items(query)	
    # let's assume you have a code review request in variable crr:
    crr = workItems[0]
    requester = crr.CreatedBy
    state = crr.State
 	shelveset = crr.Fields['Associated Context'].Value
    codeState = crr.Fields['Closed Status Code'].Value
    # it seems that the field names tend to change; so, maybe you need to play around a bit:
    criteria = crr.Fields['Acceptance Criteria'].Value
    # if you do not know the names, this code snippet might help you:
    print (sorted([field.Name for field in crr.Fields]))
    # you can then find the Code Review Responses via the links:
    for link in crr.Links:
        print (link.LinkTypeEnd.Name, link.RelatedWorkItemId)
    # when you follow those links, you can find out e.g. the type of
    # the link and continue appropriately:
    response = tfs.get_code_review(link.RelatedWorkItemId)
    print (response.Type.Name)


Change Sets
-----------

For change sets, there are two functions available:

::

	# if you want to retrieve a list of changesets, then there is:
	changesetList = tfs.get_list_of_changesets('$/<yourpathhere>')
	# and you can iterate over the changeset list as usual:
	for ci in changesetList: print ci.ChangesetId, ci.Owner, ci.Comment
	
	# you can also use more advanced queries:
	changesetList = tfs.get_list_of_changesets('$/<yourpathhere>', versionFrom = tfswinlib.DateVersionSpec(DateTime.Now.AddHours(-48)))
	
	# and you can retrieve a specific changeset:
	cs = tfs.get_change_set(4711)
	print cs.Comment

Some helper functions
---------------------

During development, I found a couple of helper functions to be quite useful:

::

    # first, as a reminder, a function that I mentioned above:
    # a method to simply print each available field of a work item:
    tfs.print_work_item (323356)
    # when you need to work with the history of states of a work items:
    stateHistory = tfs.get_work_item_state_history(wi.Id)
    # or rather how long the work item was in each state:
    stateDuration = tfs.get_work_item_state_duration(wi.Id)
    # get a list of available projects:
    listOfProjects = tfs.get_list_of_projects()
    # from this list you can find the name of your project
    for i in range(len(listOfProjects)): print (projects[i].Name)
    # and with this you can e.g. retrieve the stored queries for that project:
    storedQueries = tfs.get_list_of_stored_queries_for_project(projectName)

    # some queries contain macros, e.g. @me or @project; they are expanded on the server
    # and need to be handed over to the get_list_of_work_items function:
    params = tfs.prepare_parameter_dictionary_for_query()
    workItems = tfs.get_list_of_work_items(query, params)

    # it can also be useful to find out which users belong to a certain group:
    userNames = tfs.get_list_of_usernames_from_group("[My Team Project]\\Contributors")


Advanced functions
------------------

tfswinlib makes available the most commonly used methods of the TFS api in a simplified manner.
As we store the service access points in your TFS handle, you can access any available
TFS api method. Thus, you have access to the full universe of the TFS API, e.g. VersionControlServer
or IdentityManagementServer.

Here is the list:

- tfs.wis: WorkItemStore
- tfs.css: CommonStructureService
- tfs.ims: IdentityManagementService
- tfs.gss: GroupSecurityService2
- tfs.vcs: VersionControlServer
- tfs.tfds: TeamFoundationDiscussionService

Anything missing? Let me know...

  
Author
------
This software has been written by `Axel Seibert <http://www.ergorion.com>`_.


