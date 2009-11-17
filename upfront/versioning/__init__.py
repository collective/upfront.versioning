from zope.i18nmessageid import MessageFactory

from Products.Archetypes.atapi import *
from Products.Archetypes import listTypes
from Products.Archetypes.atapi import *
from Products.CMFCore import utils as cmfutils

from config import DEFAULT_ADD_CONTENT_PERMISSION, ADD_CONTENT_PERMISSIONS

_ = MessageFactory('upfront.versioning')

def initialize(context):
    """initialize product (called by zope)"""

    # imports packages and types for registration
    import content

    # Initialize portal content
    all_content_types, all_constructors, all_ftis = process_types(
        listTypes('upfront.versioning'),
        'upfront.versioning')

    cmfutils.ContentInit(
        'upfront.versioning' + ' Content',
        content_types      = all_content_types,
        permission         = DEFAULT_ADD_CONTENT_PERMISSION,
        extra_constructors = all_constructors,
        fti                = all_ftis,
        ).initialize(context)

    # Give it some extra permissions to control them on a per class limit
    for i in range(0,len(all_content_types)):
        klassname=all_content_types[i].__name__
        if not klassname in ADD_CONTENT_PERMISSIONS:
            continue

        context.registerClass(meta_type   = all_ftis[i]['meta_type'],
                              constructors= (all_constructors[i],),
                              permission  = ADD_CONTENT_PERMISSIONS[klassname])
