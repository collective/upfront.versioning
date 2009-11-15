from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent
from zope.annotation.interfaces import IAnnotations

class IVersioner(Interface):
    """Interface for utility which provides versioning methods"""

    def getWorkspace(context):
        """If the authenticated member does not have a workspace then create 
        one. Return the workspace.
        
        A context is needed to be able to find the membership tool.
        """

    def can_checkout(item):
        """Return true if ICheckedOut interface is not provided by item or 
        any parent, false otherwise.
        
        todo: how to prevent attempt to checkout Plone site?"""

    def can_checkin(item):
        """Return true if ICheckedOut interface is provided by item and not 
        by any parent, false otherwise."""

    def checkout(item):
        """Checkout item to authenticated member's workspace. Returns 
        checked out item.
        """

    def checkin(item):
        """Checkin item from authenticated member's workspace to 
        repository. Returns checked in item.
        """

class ICheckedOut(Interface):
    """Marker interface applied to an object on checkout"""

class ICheckedIn(Interface):
    """Marker interface applied to an object on checkin"""

class IVersionMetadata(IAnnotations):
    """Interface for adapter which manages version metadata on an object """

    def initialize(item):
        """Set values obtained from item"""

    def getPhysicalPath(self):
        """Compatibility method so adapted object can be catalogued"""

    def token():
        """Return an identifier that can be used to find the original item.
        The word 'token' is used since UID is Archetypes specific and we want 
        to be agnostic.
        """

    def state():
        """Return 'checked_out' if context implements ICheckedOut or return 
        'checked_in' if context implements ICheckedIn."""

    def version():
        """Return version info from parent id if possible, None otherwise"""

class IVersioningEvent(IObjectEvent):
    """Base class for versioning events"""

class IBeforeObjectCheckoutEvent(IVersioningEvent):
    pass

class IAfterObjectCheckoutEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")

class IBeforeObjectCheckinEvent(IVersioningEvent):
    pass

class IAfterObjectCheckinEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")
