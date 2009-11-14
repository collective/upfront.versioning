from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType

from catalog import VersioningCatalog

import logging
logger = logging.getLogger('upfront.versioning')

def postInstall(context):
    site = context.getSite()

    # Create repository
    if 'repository' not in site.objectIds():
        folder = _createObjectByType(
            'Large Plone Folder', site, 'repository', title='Repository'
        )
        # Publish it
        site.portal_workflow.doActionFor(folder, 'publish')

    # Create catalog
    id = 'upfront_versioning_catalog'
    if id not in site.objectIds():
        c = VersioningCatalog()
        c.id = id
        c.title = 'Upfront Versioning Catalog'
        site._setObject(id, c)
    catalog = site._getOb(id) 
