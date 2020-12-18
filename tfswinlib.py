#####################################################################################
#
# tfswinlib provides a comfort layer for working with Microsofts
# TeamFoundationServer using the TFS API. It works on CPython (with
# pythonnet) as well as IronPython.
# It has been tested with CPython 2.7.13 and 3.6.1 and IronPython 2.7.5
#
# Version History:
# V1.4.2 (2020-12-18) : improved error handling in print_work_item, and sort the names of the fields before printing
# V1.4.1 (2019-11-06) : had to change the import order
# V1.4.0 (2018-11-23) : support code reviews
# V1.3.1 (2017-11-23) : support version control (access to TFS path items)
# V1.3.0 (2017-11-17) : support version control (checkins)
# V1.2.4 (2017-05-05) : edited the pypi metadata
# V1.2.2 (2017-05-03) : cleaned up the imports
# V1.2.1 (2017-04-26) : resolved a problem with accessing QueryMembership.None
#                       with the help of the friendly pythonnet folks
# V1.2.0 (2017-04-26) : py3 compatibility
# V1.1.0 (2017-03-26) : supports parameter replacement in TFS queries
# V1.0.2 (2016-09-26) : small bugfix
# V1.0.1 (2016-04-30) : small optimization
#
# Remarks:
#
# the routines are compatible with python-tfs (in version 0.1.2) which works via SOAP.
# (Source: https://pypi.python.org/pypi/tfslib)
# You need either IronPython or
# CPYthon with the additional module: pythonnet (tested with 2.1.0)
# Source: https://pypi.python.org/pypi/pythonnet/2.1.0
#

# necessary prework for .Net libraries to access TFS work items
import clr
#import System
import sys
sys.path.append(r"c:\Program Files\Microsoft Visual Studio 11.0\Common7\IDE\PrivateAssemblies")
sys.path.append(r"C:\Program Files (x86)\Microsoft Visual Studio 11.0\Common7\IDE\ReferenceAssemblies\v2.0")
sys.path.append(r"C:\Program Files (x86)\Microsoft Visual Studio 10.0\Common7\IDE\ReferenceAssemblies\v2.0")
import datetime
import logging
import platform

interpreter = platform.python_implementation()
if  interpreter == 'CPython': # python + pythonnet
    try:
        clr.AddReference("Microsoft.TeamFoundation")
    except:
        # things seem to have changed with VS2017:
        sys.path.append(r'C:\Program Files (x86)\Microsoft Visual Studio\2017\TeamExplorer\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer')
        clr.AddReference("Microsoft.VisualStudio.TeamFoundation")
    clr.AddReference("Microsoft.TeamFoundation.Common")
    clr.AddReference("Microsoft.TeamFoundation.WorkItemTracking.Client")
    clr.AddReference("Microsoft.TeamFoundation.VersionControl.Client")
    clr.AddReference('Microsoft.TeamFoundation.Discussion.Client')
elif interpreter == 'IronPython':
    clr.AddReferenceByPartialName("Microsoft.TeamFoundation")
    clr.AddReferenceByPartialName("Microsoft.TeamFoundation.Common")
    clr.AddReferenceByPartialName("Microsoft.TeamFoundation.Client")
    clr.AddReferenceToFile("Microsoft.TeamFoundation.WorkItemTracking.Client.dll")
    clr.AddReferenceToFile("Microsoft.TeamFoundation.VersionControl.Client.dll")
    clr.AddReferenceToFile('Microsoft.TeamFoundation.Discussion.Client.dll')
else:
    print("This program requires either the usage of IronPython or CPython with pythonnet")
    sys.exit(-1)

from Microsoft.TeamFoundation.Server import ICommonStructureService, IGroupSecurityService2, SearchFactor, QueryMembership
from Microsoft.TeamFoundation.Client import TfsTeamProjectCollection, TfsTeamProjectCollectionFactory
from Microsoft.TeamFoundation.VersionControl.Client import VersionControlServer, VersionSpec, RecursionType, DateVersionSpec
from Microsoft.TeamFoundation.WorkItemTracking.Client import WorkItemStore, QueryFolder, Query, WorkItem
from Microsoft.TeamFoundation.Framework.Client import IIdentityManagementService
from Microsoft.TeamFoundation.Discussion.Client import TeamFoundationDiscussionService, DiscussionThread, QueryStoreOptions
from System import InvalidOperationException, DateTime, AsyncCallback

# the following lines are typically found in online source code samples
#from Microsoft.TeamFoundation.Server import *
#from Microsoft.TeamFoundation.Client import *
#from Microsoft.TeamFoundation.VersionControl.Client import *
#from Microsoft.TeamFoundation.WorkItemTracking.Client import *
#from Microsoft.TeamFoundation.Framework.Client import *
#from Microsoft.TeamFoundation.Proxy import *
#from System import *

# the following sample code was taken from
# https://www.timecockpit.com/blog/2013/05/31/TFS-Work-Items-as-Time-Cockpit-Tasks
# with input from
# http://stackoverflow.com/questions/25455085/powershell-connect-to-vso suggests that I don't need this at all

class TfsClient(object):
    def __init__(self, servername, login = None, password = None):
        self.servername = servername
        self._connected = False
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
 
    def connect(self):
        self.uri = TfsTeamProjectCollection.GetFullyQualifiedUriForName(self.servername)    
        self.server = TfsTeamProjectCollectionFactory.GetTeamProjectCollection(self.uri)
        if self.server is None:
            raise InvalidOperationException("Could not get TFS server for " + self.uri + ".")
        self.server.EnsureAuthenticated()
        if not self.server.HasAuthenticated:
            raise InvalidOperationException("TFS could not authenticate.")
        self.wis = self.server.GetService(WorkItemStore)
        self.css = self.server.GetService(ICommonStructureService)
        self.ims = self.server.GetService(IIdentityManagementService)
        self.gss = self.server.GetService(IGroupSecurityService2)
        self.vcs = self.server.GetService(VersionControlServer)
        self.tfds = self.server.GetService(TeamFoundationDiscussionService)
        self._connected = True
        
    def get_list_of_projects(self):
        '''get_list_of_projects will return an array of Microsoft.TeamFoundation.Server.ProjectInfo.
Input: 
Output: Microsoft.TeamFoundation.Server.ProjectInfo[]
'''
        return self.css.ListAllProjects()
    
    def get_list_of_stored_queries_for_project(self, project):
        '''hand over the name of a project (as string), and it will return a list of all stored queries for this project.
Input: project (name of project)
Output: list [['My Queries', [[u'my query1', u"select [System.Id] from WorkItems"]], ...], ['Shared Queries', []]]
'''
        def _list_recursively(startpoint):
            '''startpoint needs to be a QueryHierarchy. From there, it will list all queries recursively.'''
            tempListOfQueries = []
            for query in startpoint:
                if isinstance(query, QueryFolder): 
#                    print query
                    tempListOfQueries.append((query.Name, _list_recursively(query)))
                else:
                    tempListOfQueries.append ((query.Name, query.QueryText))
            return tempListOfQueries
        
        return _list_recursively(self.wis.Projects[project].QueryHierarchy)
    
    def get_list_of_usernames_from_group(self, group):
        '''get_list_of_usernames_from_group retrieves the list of all
user names within that group. This is useful if you want to dynmically 
extract the list of users from the server.
Input: group (string, e.g. "[My Team Project]\\Contributors")
Output: list of user display names ["Last Name1, first Name1", ...]
'''
        sids = self.gss.ReadIdentity(SearchFactor.AccountName, group, QueryMembership.Expanded) 
        users = self.gss.ReadIdentities(SearchFactor.Sid, sids.Members, 
                                        getattr(QueryMembership, 'None'))
        return [user.DisplayName for user in users]
    
    def prepare_parameter_dictionary_for_query(self, projectName=''):
        '''prepare_parameter_dictionary_for_query creates a dictionary with
mappings for the parameters @me and @project that can be used in WIQL queries.
Feed the result as a parameter into the function get_list_of_work_items.
Input: projectName (optional, name of project as a string)
Output: Dictionary {"project" : projectName, "me" : currentUserDisplayName}
'''
        from System import String, Environment
        clr.AddReference('System.Collections')
        from System.Collections.Generic import Dictionary
        # securityService = self.server.GetService(IGroupSecurityService)
        accountName = String.Format("{0}\\{1}", Environment.UserDomainName, Environment.UserName)
        memberInfo = self.gss.ReadIdentity(SearchFactor.AccountName, accountName, 
                                           getattr(QueryMembership, 'None'))
        if memberInfo is not None:
            currentUserDisplayName = memberInfo.DisplayName
        else:
            currentUserDisplayName = Environment.UserName
        tempDict = Dictionary[String, String]()
        tempDict.Add("project",  projectName)
        tempDict.Add("me",  currentUserDisplayName)
        return tempDict
        
    def get_list_of_work_items(self, query, paramsDict=None):
        '''get_list_of_work_items executes the query (in WIQL syntax) against the 
server and returns an array of work items.
Input: query (WIQL as a string, e.g. "SELECT [State] FROM WorkItems WHERE [System.Title] CONTAINS 'bug'")
       paramsDict (optional; can contain parameters for macro lookup, e.g. @me/@project)
Output: Microsoft.TeamFoundation.WorkItemTracking.Client.WorkItemCollection'''
        if paramsDict is None: 
            return self.wis.Query(query)
        query=Query(self.wis, query, paramsDict)
        return query.RunQuery()
    
    def get_work_item(self, itemId, revision = None):
        '''get_work_item retrieves a work item (optionally in a specific revision)
and prints its fields and values.
Input: idemId (int)
       revision (int, optional with default: None)
Output: workItem (and prints out its fields and values)'''        
        if revision is not None:
            return self.wis.GetWorkItem(itemId, revision)
        else:
            return self.wis.GetWorkItem(itemId)

    def print_work_item (self, itemId, revision = None):
        '''print_work_item takes a workitem id and optionally a revision,
fetches the workitem and prints out all Fields. This is more for 
demonstration purposes.
Input: idemId (integer, id of a work item)
       revision (optional, id, revision that should be fetched)
Output: none (prints out the field contents to STDOUT)
'''
        workItem = self.get_work_item(itemId, revision)
        for i in range(workItem.Fields.Count):
            try:
                print("%7d\t%s\t%s" % (workItem.Fields[i].Id,
                                  workItem.Fields[i].Name,
                                  workItem.Fields[i].Value))
            except:# not a good style, but I currently don't know
                # where this is defined: Microsoft.TeamFoundation.WorkItemTracking.Client.ValidationException:
                logging.error('Error accessing field with index %d' % i)
        print ("Numer of attachents: %d" % workItem.Attachments.Count)
        print ("Numer of linked items: %d" % workItem.Links.Count)
        

    def get_work_item_state_history(self, workItem):
        '''get_work_item_state_history retrieves the complete list of unique states of a
work item and when the work item entered that state.
Input: workItem (Microsoft.TeamFoundation.WorkItemTracking.Client.WorkItem)
       revision (int, optional with default: None)
Output: array of [(state1, changedDate1), (state2, changedDate2), ...]'''
        stateHistory = []
        oldState = ''
        for i in range(workItem.Revision):
            newState = workItem.Revisions[i].Fields['System.State'].Value.__str__()
            if newState != oldState:
                stateHistory.append((newState,
                                     workItem.Revisions[i].Fields['State Change Date'].Value.__str__(),
                                     ))
                oldState = newState
        return stateHistory

    def get_work_item_state_duration(self, workitem):
        '''get_work_item_state_duration calculates for each state how long the
work item was in that state.
Input: workItem (Microsoft.TeamFoundation.WorkItemTracking.Client.WorkItem)
Output: array of [(state1, duration1), (state2, duration2), ...]'''
        stateHistory = self.get_work_item_state_history(workitem)
        stateDuration = []
        for i in range(1, len(stateHistory)+1):
            state = stateHistory [i-1][0]
            enterChangeDate = datetime.datetime.strptime(stateHistory [i-1][1], 
                                                         "%d.%m.%Y %H:%M:%S")
            try:
                exitChangeDate = datetime.datetime.strptime(stateHistory [i][1], 
                                                            "%d.%m.%Y %H:%M:%S")
            except IndexError:
                exitChangeDate = datetime.datetime.now() 
            stateDuration.append((state, (exitChangeDate - enterChangeDate).__str__()))
        return stateDuration

    def get_list_of_changesets(self, projectPath, 
                                    versionSpec = VersionSpec.Latest, 
                                    deletionId = 0, 
                                    recursionType=RecursionType.Full, 
                                    user = None, 
                                    versionFrom = None, 
                                    versionTo = None, 
                                    maxCount=999, 
                                    includeChanges = False, 
                                    slotMode = False):
        '''get_list_of_changesets retrieves a list of changesets according to
the mostly optional parameters.
(see https://msdn.microsoft.com/en-us/library/bb138960(v=vs.120).aspx)
Input: projectPath, 
       versionSpec = VersionSpec.Latest, 
       deletionId = 0, 
       recursionType=RecursionType.Full, 
       user = None, 
       versionFrom = None, 
       versionTo = None, 
       maxCount=999, 
       includeChanges = False, 
       slotMode = False
Output: System.Collections.IEnumerable

Example: you can iterate over the results, e.g.:
result = tfs.get_list_of_changesets(path, versionFrom = DateTime.Now.AddHours(-48),
versionTo = DateTime.Now.AddHours(-24))
for ci in result: print ci.ChangesetId, ci.Owner, ci.Comment
'''
        return self.vcs.QueryHistory(projectPath, versionSpec, deletionId, recursionType, 
                                     user, versionFrom, versionTo, maxCount, 
                                     includeChanges, slotMode)

    def get_change_set(self, changesetId, includeChanges=None,
                       includeDownloadInfo = None,
                       includeSourceRenames = None):
        '''get_change_set retrieves the details of a specific changeset.
The optional arguments cannot be combined 
Input: changesetId
       includeChanges (optional)
       includeDownloadInfo (optional)
       includeSourceRenames (optional)
Output: Microsoft.TeamFoundation.VersionControl.Client.Changeset
Example: cs = tfs.get_change_set(268029)
'''
        if includeChanges is None and includeDownloadInfo is None and includeSourceRenames is None:
            return self.vcs.GetChangeset(changesetId)
        elif includeDownloadInfo is None and includeSourceRenames is None:
            return self.vcs.GetChangeset(changesetId, includeChanges)
        elif includeSourceRenames is None:
            return self.vcs.GetChangeset(changesetId, includeChanges, includeDownloadInfo)
        else:
            return self.vcs.GetChangeset(changesetId, includeChanges, includeDownloadInfo, includeSourceRenames)
            
    def get_list_of_items(self, projectPath, recursionType):
        '''get_list_of_items retrieves a list of items from the version
control system.
Input: projectPath (TFS path)
       recursionType (e.g. RecursionType.Full or None or OneLevel as defined by
       Microsoft.TeamFoundation.VersionControl.Client.RecursionType)
Output: Microsoft.TeamFoundation.VersionControl.Client.Item[]
Example: items = get_list_of_items("$/ProjectName", RecursionType.None)
         for item in items:
             print item.ServerItem
'''
        return self.vcs.GetItems(projectPath, recursionType).get_Items()
    
    def get_item(self, projectPath):
        return self.vcs.GetItem(projectPath)
    
    def get_code_review(self, codeReviewId):
        '''get_code_review retrieves a code review (can be a request or a response).
You could e.g. get a list of all review requests, do:
query = """SELECT [System.Id], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'Code Review Request'"""
reviewRequests = tfs.get_list_of_work_items(query) 
and then call get_code_review on each retrieved work item it.
'''
        return self.get_work_item(codeReviewId)

if __name__ == "__main__":
    print ('tfswinlib is a library and does not offer any end user functionality.')

