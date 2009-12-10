from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent
from zope.annotation.interfaces import IAnnotations

class IVersioner(Interface):
    """Interface for utility which provides versioning methods"""
         
    def can_start_new_version(item):
        """Return true if ICheckedOut is not provided by item or any ancestor, 
        false otherwise."""

    def can_commit(item):
        """Return true if (1) ICheckedOut interface is provided by item and not 
        by any parent, false otherwise."""

    def start_new_version(item):
        """Create a new version of item. 
        
        If item is not yet versioned then it becomes the first version. The
        second version is created and returned.

        If the item is already versioned then a new version is created and 
        returned.
        """

    def commit(item):
        """Make item the current item, ie. the one returned by searches. Return 
        item."""

class ICheckedOut(Interface):
    """Marker interface applied to an object on checkout"""

class ICheckedIn(Interface):
    """Marker interface applied to an object on checkin"""

class IVersionMetadata(IAnnotations):
    """Interface for adapter which manages version metadata on an object """

    def initialize(item):
        """Copy token metadata from item if it is present to preserve chain, 
        else fetch token from item. 
        
        If version metadata is present on item then increment that version as 
        the version, else set it to one.
        
        All other attributes are fetched from item."""

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
