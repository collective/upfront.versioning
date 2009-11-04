from persistent.dict import PersistentDict

from zope.interface import implements, alsoProvides
from zope.component import adapts
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType

from interfaces import IVersioner, IVersionMetadata

ANNOT_KEY = 'IVersionMetadata'

class Versioner(object):
    """Provide versioning methods"""

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
        # Scan the workspace for item. If it is already checked out then 
        # return it.
        workspace = self.getWorkspace(item)
        for ob in workspace.objectValues():
            if IVersionMetadata(ob).token == item.UID():
                return ob

        # Copy the item
        cp = item.aq_parent.manage_copyObjects([item.id])
        workspace.manage_pasteObjects(cp)
        copy = workspace._getOb(item.id)

        # Initialize IVersionMetadata
        IVersionMetadata(copy).initialize(item)

        return copy

    def checkin(self, item):
        pass

class VersionMetadata(AttributeAnnotations):
    """Manages version metadata on an object"""

    implements(IVersionMetadata)
    adapts(IAttributeAnnotatable)

    def __init__(self, obj):
        self.obj = obj
        self.context = obj
        if not self.has_key(ANNOT_KEY):
            self[ANNOT_KEY] = PersistentDict()

    def initialize(self, item):
        self[ANNOT_KEY].update(
            dict(
                token=item.UID(),
            )
        )

    @property
    def token(self):
        self[ANNOT_KEY]['token']        
