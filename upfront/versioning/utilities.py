from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty

from OFS.SimpleItem import SimpleItem

from interfaces import IVersioningSettings

class VersioningSettings(SimpleItem):
    """Store product settings"""

    implements(IVersioningSettings)

    versionable_types = ['Document']
