from Products.CMFCore.permissions import setDefaultRoles, AddPortalContent

DEFAULT_ADD_CONTENT_PERMISSION = AddPortalContent
setDefaultRoles(DEFAULT_ADD_CONTENT_PERMISSION, ('Manager', 'Owner'))
ADD_CONTENT_PERMISSIONS = { 
    'VersionFolder': 'Add Version Folder',
}
