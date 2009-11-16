from string import zfill

from persistent.dict import PersistentDict
from Acquisition import aq_base

from zope.interface import implements, alsoProvides, noLongerProvides
from zope.component import adapts, getUtility
from zope.event import notify
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from Products.CMFCore.utils import getToolByName
from Products.DCWorkflow.utils import modifyRolesForPermission
from Products.CMFPlone.utils import _createObjectByType
from plone.i18n.normalizer.interfaces import IURLNormalizer

from interfaces import IVersioner, IVersionMetadata, ICheckedOut, ICheckedIn
from events import BeforeObjectCheckoutEvent, AfterObjectCheckoutEvent, \
    BeforeObjectCheckinEvent, AfterObjectCheckinEvent

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
        if home is None:
            raise RuntimeError, "Members must have home folders for versioning to function properly"
        if 'workspace' not in home.objectIds():
            home.invokeFactory('Folder', id='workspace', title='Workspace')
        return home.workspace

    def can_checkout(self, item):
        parent = item
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)
        return True

    def can_checkin(self, item):
        if not ICheckedOut.providedBy(item):
            return False

        parent = getattr(item, 'aq_parent', None)
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)

        return True
      
    def checkout(self, item):
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

    def checkin(self, item):
        # todo: use semaphore where appropriate
        # todo: version folders are sparse like with SVN, but that does
        # allow multiple checkins in a single transaction

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
            _createObjectByType(
                'Large Plone Folder', repository, pt_id, title=item.portal_type
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
                'Folder', pt_folder, version_id, title=version_id
        )

        # Move our copy there
        cp = item.aq_parent.manage_cutObjects(ids=[item.id])
        res = folder.manage_pasteObjects(cp)
        checkedin = folder._getOb(res[0]['new_id'])

        # If checked in item's id does not match that of original then rename
        if (original is not None) and (checkedin.id != original.id):
            # setId seems safe but if problems arise use manage_renameObject
            checkedin.setId(original.id)

        notify(AfterObjectCheckinEvent(checkedin, original))

        return checkedin

class VersionMetadata(AttributeAnnotations):
    """Manages version metadata on an object"""

    implements(IVersionMetadata)
    adapts(IAttributeAnnotatable)

    def __init__(self, obj):
        self.obj = obj
        self.context = obj

    def initialize(self, item):        
        """Copy annotation info from item if it is present to preserve chain, 
        else fetch attributes from item."""

        if not self.has_key(ANNOT_KEY):
            self[ANNOT_KEY] = PersistentDict()                

        adapted = IVersionMetadata(item)
        if adapted.has_key(ANNOT_KEY):
            self[ANNOT_KEY] = adapted[ANNOT_KEY]
        else:
            wf = getToolByName(item, 'portal_workflow')
            self[ANNOT_KEY].update(
                dict(
                    token=item.UID(),
                    review_state=wf.getInfoFor(item, 'review_state'),
                )
            )
  
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
        parent = self.context.aq_parent
        try:
            i = int(parent.id)
            return i
        except ValueError:
            return None
