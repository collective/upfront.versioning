from string import zfill
from DateTime import DateTime

from persistent.dict import PersistentDict
from Acquisition import aq_base

from zope.interface import implements, alsoProvides, noLongerProvides
from zope.component import adapts, getUtility
from zope.event import notify
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.DCWorkflow.utils import modifyRolesForPermission
from Products.CMFPlone.utils import _createObjectByType
from plone.i18n.normalizer.interfaces import IURLNormalizer

from interfaces import IVersioner, IVersionMetadata, ICheckedOut, ICheckedIn, \
    IVersioningSettings
from events import BeforeObjectCheckoutEvent, AfterObjectCheckoutEvent, \
    BeforeObjectCheckinEvent, AfterObjectCheckinEvent

ANNOT_KEY = 'IVersionMetadata'

# Permission decorators - grok has something nicer but we do not want an 
# extra dependency.
def requireView(func):
    def new(self, item):
        member = getToolByName(item, 'portal_membership').getAuthenticatedMember()
        if not member.has_permission(View, item):
            return False       
        return func(self, item)
    return new

def requireModifyPortalContent(func):
    def new(self, item):
        member = getToolByName(item, 'portal_membership').getAuthenticatedMember()
        if not member.has_permission(ModifyPortalContent, item):
            return False       
        return func(self, item)
    return new

def check_types(func):
    """Check whether context type is versionable"""
    def new(self, item):
        portal = getToolByName(item, 'portal_url').getPortalObject()
        sm = portal.getSiteManager()
        utility = sm.getUtility(IVersioningSettings, 'upfront.versioning-settings')
        if getattr(item, 'portal_type', None) not in utility.versionable_types:
            return False
        return func(self, item)
    return new

def check_children(func):
    """A check which cannot be performed as a guard since it is slow. Calling 
    this decorator on eg. the Plone site will raise because the site contains 
    content marked with ICheckedOut or ICheckedIn . There is also a hard 
    child limit of 30."""
    def new(self, item):
        counter = 0
        for dontcare, child in item.ZopeFind(item, search_sub=1):
            if ICheckedOut.providedBy(child) or ICheckedIn.providedBy(child):
                raise RuntimeError, "Child is marked with ICheckedOut or ICheckedIn"
            if counter > 30:
                raise RuntimeError, "The object contains more than 30 children"
            counter += 1                
        return func(self, item)
    return new

def check_homefolder(func):
    """Return False if member has no home folder, else execute func and return
    its value."""
    def new(self, item):
        pms = getToolByName(item, 'portal_membership')
        if pms.isAnonymousUser():
            return False
        member = pms.getAuthenticatedMember()
        home = member.getHomeFolder()
        if home is None:
            return False
        return func(self, item)
    return new

class Versioner(object):
    """Provide versioning methods"""

    implements(IVersioner)

    def getWorkspace(self, context):
        pms = getToolByName(context, 'portal_membership')
        if pms.isAnonymousUser():
            raise RuntimeError, "Anonymous users cannot have a workspace"
        member = pms.getAuthenticatedMember()
        home = member.getHomeFolder()
        if home is None:
            raise RuntimeError, "Members must have home folders for versioning to function properly"
        if 'workspace' not in home.objectIds():
            home.invokeFactory('Folder', id='workspace', title='Workspace')
        return home.workspace

    @requireView
    @check_types
    @check_homefolder
    def can_derive_copy(self, item):
        parent = item
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)
        return True

    @requireModifyPortalContent
    @check_types
    def can_add_to_repository(self, item):
        parent = item
        while parent is not None:
            if ICheckedOut.providedBy(parent) or ICheckedIn.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)
        return True

    @requireModifyPortalContent
    @check_types
    @check_homefolder
    def can_checkout(self, item):
        if not ICheckedIn.providedBy(item):
            return False

        parent = item
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)
        return True

    @requireModifyPortalContent
    @check_types
    def can_checkin(self, item):
        if not ICheckedOut.providedBy(item):
            return False

        parent = getattr(item, 'aq_parent', None)
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)

        return True

    @requireView
    @check_children
    def derive_copy(self, item):
        if not self.can_derive_copy(item):
            raise RuntimeError, "Cannot derive copy of %s" % item.absolute_url()

        workspace = self.getWorkspace(item)

        # Copy the item
        cp = item.aq_parent.manage_copyObjects([item.id])
        res = workspace.manage_pasteObjects(cp)
        copy = workspace._getOb(res[0]['new_id'])

        # Remove marker interfaces if it applies
        if ICheckedIn.providedBy(copy):
            noLongerProvides(copy, ICheckedIn)

        # Remove IVersionMetadata annotation if it exists
        IVersionMetadata(copy).remove()

        return copy

    @requireModifyPortalContent
    def checkout(self, item):
        if not self.can_checkout(item):
            raise RuntimeError, "Cannot check out %s" % item.absolute_url()

        # Scan the workspace for item. If it is already checked out then 
        # return it.
        workspace = self.getWorkspace(item)
        for ob in workspace.objectValues():
            if IVersionMetadata(ob).token == item.UID():
                return ob

        notify(BeforeObjectCheckoutEvent(item))

        # Copy the item
        cp = item.aq_parent.manage_copyObjects([item.id])
        res = workspace.manage_pasteObjects(cp)
        copy = workspace._getOb(res[0]['new_id'])

        # Initialize IVersionMetadata
        IVersionMetadata(copy).initialize(item)

        # Change View permission and marker interfaces recursively
        if ICheckedIn.providedBy(copy):
            noLongerProvides(copy, ICheckedIn)
        alsoProvides(copy, ICheckedOut)
        modifyRolesForPermission(copy, 'View', ('Manager','Owner'))
        for dontcare, child in copy.ZopeFind(copy, search_sub=1):
            modifyRolesForPermission(child, 'View', ('Manager','Owner'))

        notify(AfterObjectCheckoutEvent(copy, item))

        return copy

    def _checkin(self, item):
        """Used by both add_to_repository and checkin"""

        # todo: use semaphore where appropriate

        # Fetch the original item
        original = None
        token = IVersionMetadata(item).token
        if token is not None:
            original = getToolByName(item, 'reference_catalog').lookupObject(token)

        notify(BeforeObjectCheckinEvent(item))

        # Remove and add marker interface
        noLongerProvides(item, ICheckedOut)
        alsoProvides(item, ICheckedIn)

        # Restore View permission of item and children by using the workflow
        # tool
        wf = getToolByName(item, 'portal_workflow')
        wfs = {}
        for ob in wf.getWorkflowsFor(item):
            if hasattr(aq_base(ob), 'updateRoleMappingsFor'):
                wfs[ob.id] = ob
        wf._recursiveUpdateRoleMappings(item, wfs)

        # Find the folder where these portal type versions are stored
        portal = getToolByName(item, 'portal_url').getPortalObject()
        repository = portal.repository
        pt_id = getUtility(IURLNormalizer).normalize(item.portal_type)
        if pt_id not in repository.objectIds():
            pt_folder = _createObjectByType(
                'VersionFolder', repository, pt_id, title=item.portal_type
            )

        pt_folder = repository._getOb(pt_id)

        # Find the latest version number
        latest_version = 0
        oids = [o for o in pt_folder.objectIds()]
        oids.sort()
        if oids:
            try:
                latest_version = int(oids[-1])
            except ValueError:
                raise RuntimeError, \
                    "Expected an int-able string but found %s" % oids[-1]        
        latest_version += 1

        # Create a folder for the new version
        version_id = zfill(latest_version, 8)
        folder = _createObjectByType(
                'VersionFolder', pt_folder, version_id, title=version_id
        )

        # Move our copy there
        cp = item.aq_parent.manage_cutObjects(ids=[item.id])
        res = folder.manage_pasteObjects(cp)
        checkedin = folder._getOb(res[0]['new_id'])

        # If checked in item's id does not match that of original then rename
        if (original is not None) and (checkedin.id != original.id):
            # setId seems safe but if problems arise use manage_renameObject
            checkedin.setId(original.id)

        # Set version and date as metadata
        IVersionMetadata(checkedin).edit(
            version=int(version_id),
            date=DateTime()
        )

        notify(AfterObjectCheckinEvent(checkedin, original))

        return checkedin

    @requireModifyPortalContent
    @check_children
    def add_to_repository(self, item):
        if not self.can_add_to_repository(item):
            raise RuntimeError, "Cannot add %s to repository" % item.absolute_url()

        # Initialize metadata with self since item is not based on anything
        IVersionMetadata(item).initialize(item)

        return self._checkin(item)

    @requireModifyPortalContent
    def checkin(self, item):
        if not self.can_checkin(item):
            raise RuntimeError, "Cannot check in %s" % item.absolute_url()
        return self._checkin(item)

class VersionMetadata(AttributeAnnotations):
    """Manages version metadata on an object"""

    implements(IVersionMetadata)
    adapts(IAttributeAnnotatable)

    def __init__(self, obj):
        self.obj = obj
        self.context = obj

    def initialize(self, item):        
        """Copy token metadata from item if it is present to preserve chain, 
        else fetch token from item. All other atributes are fetched from 
        item."""

        wf = getToolByName(item, 'portal_workflow')
        token = IVersionMetadata(item).token

        if not self.has_key(ANNOT_KEY):
            self[ANNOT_KEY] = PersistentDict()                
        self[ANNOT_KEY].update(
            dict(
                token=token or item.UID(),
                review_state=wf.getInfoFor(item, 'review_state'),
                date=DateTime(),
            )
        )
 
    def edit(self, **kwargs):
        if not self.has_key(ANNOT_KEY):
            self[ANNOT_KEY] = PersistentDict()                
        self[ANNOT_KEY].update(dict(**kwargs))

    def getPhysicalPath(self):
        return self.context.getPhysicalPath()

    @property
    def token(self):
        if self.has_key(ANNOT_KEY):
            return self[ANNOT_KEY].get('token', None)
        return self.context.UID()

    @property
    def state(self):
        if ICheckedOut.providedBy(self.context):
            return 'checked_out'
        if ICheckedIn.providedBy(self.context):
            return 'checked_in'
        return None

    @property
    def version(self):        
        if self.has_key(ANNOT_KEY):
            return self[ANNOT_KEY].get('version', None)
        return None

    @property
    def date(self):        
        if self.has_key(ANNOT_KEY):
            return self[ANNOT_KEY].get('date', None)
        return None

    def remove(self):
        if self.has_key(ANNOT_KEY):
            del self[ANNOT_KEY]

