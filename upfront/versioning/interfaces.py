from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent
from zope.annotation.interfaces import IAnnotations

class IVersioner(Interface):
    """Interface for utility which provides versioning methods"""

    def getWorkspace(context):
        """If the authenticated member does not have a workspace then create 
        one. Return the workspace.
        
        A context is needed to be able to find the membership tool."""

    def can_derive_copy(item):
        """Return true if item and none of its parents provide ICheckedOut, 
        false otherwise."""         

    def can_add_to_repository(item):
        """Return true if (1) item and none of its parents provide either 
        ICheckedOut or ICheckedIn and (2) IAddToRepositoryPrecondition utility 
        returns true, false otherwise."""
         
    def can_checkout(item):
        """Return true if ICheckedIn interface is provided by item and 
        ICheckedOut not by any parent, false otherwise."""

    def can_checkin(item):
        """Return true if (1) ICheckedOut interface is provided by item and not 
        by any parent, false otherwise."""

    def derive_copy(item):
        """Copy item to authenticated member's workspace. Return copied 
        item."""

    def checkout(item):
        """Checkout item to authenticated member's workspace. Returns
        checked out item."""

    def checkin(item):
        """Checkin item from authenticated member's workspace to 
        repository. Return checked in item."""

class IAddToRepositoryPrecondition(Interface):
    """Interface for utility which evaluates whether an item may be added to
    the repository. Third-party products should implement this for custom 
    behaviour."""

class ICheckedOut(Interface):
    """Marker interface applied to an object on checkout"""

class ICheckedIn(Interface):
    """Marker interface applied to an object on checkin"""

class IVersionMetadata(IAnnotations):
    """Interface for adapter which manages version metadata on an object """

    def initialize(item):
        """Set values obtained from item"""

    def edit(**kwargs):
        """Update values from kwargs"""

    def getPhysicalPath(self):
        """Compatibility method so adapted object can be catalogued"""

    def token():
        """Return an identifier that can be used to find the original item.
        The word 'token' is used since UID is Archetypes specific and we want 
        to be agnostic."""

    def state():
        """Return 'checked_out' if context implements ICheckedOut or return 
        'checked_in' if context implements ICheckedIn."""

    def version():
        """Return version info if possible, None otherwise"""

    def date():
        """Return date info if possible, None otherwise"""

    def remove():
        """Remove the IVersionMetadata annotation"""

class IVersioningEvent(IObjectEvent):
    """Base class for versioning events"""

class IBeforeObjectDeriveEvent(IVersioningEvent):
    pass

class IAfterObjectDeriveEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")

class IBeforeObjectCheckoutEvent(IVersioningEvent):
    pass

class IAfterObjectCheckoutEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")

class IBeforeObjectCheckinEvent(IVersioningEvent):
    pass

class IAfterObjectCheckinEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")

class IVersioningSettings(Interface):
    """Interface for persistent utility which stores product settings"""
