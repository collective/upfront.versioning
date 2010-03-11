from string import zfill
from random import randint
from DateTime import DateTime

from persistent.dict import PersistentDict
from Acquisition import aq_base
from AccessControl.PermissionRole import rolesForPermissionOn

from zope.interface import implements, alsoProvides, noLongerProvides
from zope.component import adapts, getUtility
from zope.event import notify
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFPlone.utils import _createObjectByType

from interfaces import IVersioner, IVersionMetadata, ICheckedOut, ICheckedIn, \
    IVersioningSettings
from events import BeforeObjectCheckoutEvent, AfterObjectCheckoutEvent, \
    BeforeObjectCheckinEvent, AfterObjectCheckinEvent

ANNOT_KEY = 'IVersionMetadata'

# Permission decorators - grok has something nicer but we do not want an 
# extra dependency.
def requireModifyPortalContent(func):
    def new(self, item):
        member = getToolByName(item, 'portal_membership').getAuthenticatedMember()
        if not member.has_permission(ModifyPortalContent, item):
            return False       
        return func(self, item)
    return new

def requireModifyPortalContentRaises(func):
    def new(self, item):
        member = getToolByName(item, 'portal_membership').getAuthenticatedMember()
        if not member.has_permission(ModifyPortalContent, item):
            raise RuntimeError, "User does not have Modify Portal Content permission"
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

class Versioner(object):
    """Provide versioning methods"""

    implements(IVersioner)

    @requireModifyPortalContent
    @check_types
    @check_children
    def can_start_new_version(self, item):
        parent = item
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)
        return True

    @requireModifyPortalContent
    @check_types
    def can_commit(self, item):
        if not ICheckedOut.providedBy(item):
            return False

        parent = getattr(item, 'aq_parent', None)
        while parent is not None:
            if ICheckedOut.providedBy(parent):
                return False
            parent = getattr(parent, 'aq_parent', None)

        return True

    @requireModifyPortalContentRaises
    def start_new_version(self, item):
        if not self.can_start_new_version(item):
            raise RuntimeError, "Cannot start new version for %s" % item.absolute_url()

        notify(BeforeObjectCheckoutEvent(item))

        adapted = IVersionMetadata(item)
        # If ICheckedIn is not provided then item is not yet subject to 
        # versioning.
        if not ICheckedIn.providedBy(item):

            # Rename item. Use deeper API to avoid permission problems.
            original_id = item.id
            newid = '%s-%s' % (item.id, randint(1,1000000))
            parent = item.aq_parent
            item._notifyOfCopyTo(parent, op=1)
            parent._delObject(item.id, suppress_events=False)
            item = aq_base(item)
            item._setId(newid)
            parent._setObject(newid, item, set_owner=0, suppress_events=False)
            item = parent._getOb(newid)

            # Create a VersionFolder with same id as item's original id
            folder = _createObjectByType(
                'VersionFolder', item.aq_parent, original_id, title=item.Title()
            )
            portal_types = getToolByName(item, 'portal_types')
            fti = portal_types.getTypeInfo('VersionFolder')
            fti._finishConstruction(folder)

            # Initialize IVersionMetadata for item, Since it is the first 
            # version it is initialized from itself.
            IVersionMetadata(item).initialize(item)

            # Add marker interface
            alsoProvides(item, ICheckedIn)

            # Delete item from container
            item._notifyOfCopyTo(folder, op=1)
            item.aq_parent._delObject(item.id, suppress_events=False)
            item = aq_base(item)
            item._setId('%.8d' % IVersionMetadata(item).version)
            folder._setObject(item.id, item, set_owner=0, suppress_events=False)

            item = folder._getOb(item.id)

            # Catalog item
            vc = getToolByName(item, 'upfront_versioning_catalog')
            vc.reindexObject(item)
            pc = getToolByName(item, 'portal_catalog')
            pc.reindexObject(item)

        # Create a sibling for item. The id is computed by incrementing
        # the version stored in the IVersionMetadata adapted item.
        item._notifyOfCopyTo(item.aq_parent, op=0)
        copy = item._getCopy(item.aq_parent)
        # Initialize IVersionMetadata for this copy. This provides a new 
        # version number.
        IVersionMetadata(copy).initialize(item)
        copy._setId('%.8d' % IVersionMetadata(copy).version)
        item.aq_parent._setObject(copy.id, copy, set_owner=1, suppress_events=False)
        copy = item.aq_parent._getOb(copy.id)

        # Put copy and children initial state. We may want to make this 
        # configurable?
        for dontcare, child in [(copy.id, copy)] + copy.ZopeFind(copy, search_sub=1):
            child.notifyWorkflowCreated()

        # Toggle marker interfaces
        if ICheckedIn.providedBy(copy):
            noLongerProvides(copy, ICheckedIn)
        alsoProvides(copy, ICheckedOut)

        # Reindex to update catalog
        copy.reindexObject()

        # Catalog new version and original
        vc = getToolByName(item, 'upfront_versioning_catalog')
        vc.catalog_object(item, skip_interface_check=True)    
        vc.catalog_object(copy)

        notify(AfterObjectCheckoutEvent(copy, item))

        return copy

    @requireModifyPortalContentRaises
    def commit(self, item):
        if not self.can_commit(item):
            raise RuntimeError, "Cannot commit %s" % item.absolute_url()

        # Fetch the original item
        original = None
        token = IVersionMetadata(item).token
        if token is not None:
            original = getToolByName(item, 'reference_catalog').lookupObject(token)
        
        notify(BeforeObjectCheckinEvent(item))

        # Remove and add marker interface
        noLongerProvides(item, ICheckedOut)
        alsoProvides(item, ICheckedIn)

        # Reindex this version
        vc = getToolByName(item, 'upfront_versioning_catalog')
        vc.catalog_object(item)
        item.reindexObject()

        notify(AfterObjectCheckinEvent(item, original))

        return item

class VersionMetadata(AttributeAnnotations):
    """Manages version metadata on an object"""

    implements(IVersionMetadata)
    adapts(IAttributeAnnotatable)

    def __init__(self, obj):
        self.obj = obj
        self.context = obj

    def initialize(self, item):              
        # Ask catalog for highest version number
        vc = getToolByName(item, 'upfront_versioning_catalog')
        version = vc.getHighestVersionNumberOf(item) + 1

        if not self.has_key(ANNOT_KEY):
            self[ANNOT_KEY] = PersistentDict()                
        self[ANNOT_KEY].update(
            dict(
                token=IVersionMetadata(item).token or item.UID(),
                date=DateTime(),
                version=version,
                base_version=IVersionMetadata(item).version,
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
    def base_version(self):        
        if self.has_key(ANNOT_KEY):
            return self[ANNOT_KEY].get('base_version', None)
        return None

    @property
    def date(self):        
        if self.has_key(ANNOT_KEY):
            return self[ANNOT_KEY].get('date', None)
        return None

    def remove(self):
        if self.has_key(ANNOT_KEY):
            del self[ANNOT_KEY]

