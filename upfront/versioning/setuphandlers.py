from zope.app.component.interfaces import ISite

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType

from catalog import VersioningCatalog

import logging
logger = logging.getLogger('upfront.versioning')

def isNotUpfrontVersioningProfile(context):
    return context.readDataFile("upfrontversioning_marker.txt") is None

def postInstall(context):
    if isNotUpfrontVersioningProfile(context): return 
    site = context.getSite()

    # Create repository
    if 'repository' not in site.objectIds():
        folder = _createObjectByType(
            'VersionFolder', site, 'repository', title='Repository'
        )

    # Create catalog
    id = 'upfront_versioning_catalog'
    if id not in site.objectIds():
        c = VersioningCatalog()
        c.id = id
        c.title = 'Upfront Versioning Catalog'
        site._setObject(id, c)
    catalog = site._getOb(id) 
