from string import zfill

from persistent.dict import PersistentDict

from zope.interface import implements, alsoProvides
from zope.component import adapts, getUtility
from zope.event import notify
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from plone.i18n.normalizer.interfaces import IURLNormalizer

from interfaces import IVersioner, IVersionMetadata
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
        if 'workspace' not in home.objectIds():
            home.invokeFactory('Folder', id='workspace', title='Workspace')
        return home.workspace

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
        workspace.manage_pasteObjects(cp)
        copy = workspace._getOb(item.id)

        notify(AfterObjectCheckoutEvent(copy, item))

        # Initialize IVersionMetadata
        IVersionMetadata(copy).initialize(item)

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
        folder.manage_pasteObjects(cp)
        ret = folder._getOb(item.id)

        notify(AfterObjectCheckinEvent(ret, original))

        return ret

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
        wf = getToolByName(item, 'portal_workflow')
        self[ANNOT_KEY].update(
            dict(
                token=item.UID(),
                review_state=wf.getInfoFor(item, 'review_state'),
            )
        )

    @property
    def token(self):
        self[ANNOT_KEY].get('token', None)
