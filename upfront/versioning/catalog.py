from AccessControl import ClassSecurityInfo

from Products.CMFPlone.CatalogTool import CatalogTool

from interfaces import ICheckedOut, ICheckedIn, IVersionMetadata

# Helper class
class ZCExtra:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class VersioningCatalog(CatalogTool):
    """Catalog items that have passed through the versioning tool"""

    security = ClassSecurityInfo()

    def __init__(self, *args, **kwargs):
        CatalogTool.__init__(self, *args, **kwargs)

        # Create indexes
        for name, type, extra in \
            (
                ('token', 'FieldIndex', None),         
                ('state', 'FieldIndex', None),
                ('path', 'ExtendedPathIndex', ZCExtra(doc_attr='getPhysicalPath')),
                ('version', 'FieldIndex', None),
            ):
            if not name in self.indexes():
                self.manage_addIndex(name, type, extra=extra)

        # Create metadata 
        for meta in ('version',):        
            if meta not in self.schema():
                self.manage_addColumn(meta)

    def catalog_object(self, obj, uid=None, idxs=None, update_metadata=1, pghandler=None, skip_interface_check=False):
        """If skip_interface_check then only catalog obj if it provides 
        ICheckedOut or ICheckedIn"""
        if not skip_interface_check:
            if not (ICheckedOut.providedBy(obj) or ICheckedIn.providedBy(obj)):
                return
        CatalogTool.catalog_object(
            self, IVersionMetadata(obj), uid, idxs, update_metadata, pghandler
        )

    def isCatalogued(self, uid):
        return self._catalog.uids.has_key(uid)

    def getVersionsOf(self, obj):
        """Return all versions of object identified by token"""
        if not (ICheckedOut.providedBy(obj) or ICheckedIn.providedBy(obj)):
            return []
        return self(token=IVersionMetadata(obj).token)

    def getHighestVersionNumberOf(self, obj):
        """Return highest version number of object identified by token"""
        brains = self(token=IVersionMetadata(obj).token, sort_on='version')
        if brains:
            return brains[-1].version
        return 0

    def getLatestVersionOf(self, obj):
        """Return latest version of object identified by token"""
        brains = self(
            token=IVersionMetadata(obj).token, 
            sort_on='version',
            state='checked_in'
        )
        if brains:
            return brains[-1].getObject()
        return None            
