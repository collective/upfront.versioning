from AccessControl import ClassSecurityInfo
from zope.interface import implements

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.Archetypes.atapi import *

from interfaces import IVersionFolder
from upfront.versioning.interfaces import IVersionMetadata

schema = Schema((
),
)
VersionFolder_schema = BaseFolder.schema.copy() + schema.copy()

class VersionFolder(BaseFolder, BrowserDefaultMixin):
    """
    """
    security = ClassSecurityInfo()
    implements(IVersionFolder)

    meta_type = 'VersionFolder'
    archetype_name = 'Version Folder'
    _at_rename_after_creation = True

    schema = VersionFolder_schema

    def getLatestVersion(self):
        """ Return the latest version
        """ 
        versions = [IVersionMetadata(obj) for obj in self.objectValues()]
        versions.sort(lambda a,b: cmp(a.version, b.version))
        return versions[-1]



registerType(VersionFolder, 'upfront.versioning')
