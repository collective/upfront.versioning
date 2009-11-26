Introduction 
============ 
A versioning system that allows users to check out or derive an item to a 
workspace, edit it and commit it back to a repository.

A checked out version is only visible to the user who checked it out or a
manager. Catalog queries for content always transparently return the latest
committed item. It is possible to query for older versions.

Note that the product cannot function unless user folders are enabled in the 
Site Setup section of the Plone site.

Terminology 
=========== 
Workspace: a folder where a user checks out items to
Repository: an area that contains committed versions of items 

Operation 
========= 
upfront.versioning introduces four operations surfaces as actions in the Plone
site.  These are "Add to repository", "Derive copy", "Checkout" and "Checkin".
Detailed descriptions of each operation are in interfaces.py and edge cases are
covered in the test suite. A more practical explanation of each operation
follows.

Since upfront.versioning is completely componentized and customizable with ZCML
and a configlet the explanation only applies to the product in its default
configuration.

A. A new unversioned item is added to the repository

Items are never created directly in the repository. Instead, they can live
anywhere and be added to the repository by the "Add to repository" action. The
pre-condition for this action to be available is that the item must be
anonymously visible. In a typical Plone site this means the item must be
published.

As a manager create a page and publish it. The "Add to repository" action is
available.  As a member create a page and submit it for review. When a manager
publishes it the "Add to repository" action is available.

B. A copy of any item is derived

This operation enables you to to base a new item on any existing item without
it being considered as another version of the existing item. This is useful
when creating a derivative work or when the user does not have permission to
checkout an item. 

As any type of authenticated user browse to any item. The "Derive copy" action
is available. The item is copied and stripped from comments. The copy in the
workspace is subject to the same behaviour as in A.

C. An item is checked out from the repository

If the user has the Modify Portal Content permission on an item in the
repository he may checkout the item to his workspace. Comments are stripped
from the checked out item (now referred to as the working copy or copy). The
copy and any potential children have exactly the same review state as the
original and all workflow transitions are locked while checked out. The user
can checkin the copy at any stage.

D. An item is checked in to the repository

The item is moved from the workspace into a new position in the repository.
For example, if the original is in /repository/document/00000002/an-item then
the new version is moved to /repository/document/00000003/an-item. It may even
be moved to 00000005 since the versions are sparse just like SVN. Older 
versions of the item are expired so as not to show up in queries and the 
checked in version is un-expired if needed

User interface 
============== 
The product is configured at @@upfront.versioning-settings.

A versions viewlet is present at the bottom of every item that (a) is of a
portal type configured to be subject to versioning and (b) has version
information.  It is loaded lazily with ajax since it can be slow.

Implementation 
============== 
Versioning is realized through a combination of marker interfaces, annotations 
and a versioning catalog. The catalog is strictly speaking not necessary for 
versioning to function but it does make useful UI possible.
