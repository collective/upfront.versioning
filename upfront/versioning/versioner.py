from zope.interface import implements, alsoProvides

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType

from interfaces import IVersioner

class Versioner(object):
    """
    Provide versioning methods
    """
    implements(IVersioner)

    def getWorkspace(self, context):
        pms = getToolByName(context, 'portal_membership')
        if pms.isAnonymousUser():
            raise RuntimeError, "Anonymous users cannot have a workspace"
        member = pms.getAuthenticatedMember()
        home = member.getHomeFolder()
        if 'workspace' not in home.objectIds():
            _createObjectByType('Folder', home, 'workspace', title='Workspace')
        return home.workspace

    def checkout(self, item):
        pass

    def checkin(self, item):
        pass
