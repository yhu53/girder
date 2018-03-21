#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2015 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import collections
import itertools
import six

from ..models.model_base import Model, AccessControlledModel, _permissionClauses
from ..exceptions import AccessException
from ..constants import AccessType, TEXT_SCORE_SORT_MAX


class AccessControlMixin(object):
    """
    This mixin is intended to be used for resources which aren't access
    controlled by default, but resolve their access controls through other
    resources. As such, the overridden methods retain the same parameters and
    only alter functionality related to access control resolution.

    resourceColl corresponds to the resource collection that needs to be used
    for resolution, for example the Item model has a resourceColl of folder.

    resourceParent corresponds to the field in which the parent resource
    belongs, so for an item it would be the folderId.
    """
    resourceColl = None
    resourceParent = None

    def load(self, id, level=AccessType.ADMIN, user=None, objectId=True,
             force=False, fields=None, exc=False):
        """
        Calls Model.load on the current item, and then attempts to load the
        resourceParent which the user must have access to in order to load this
        model.

        Takes the same parameters as
        :py:func:`girder.models.model_base.AccessControlledModel.load`.
        """
        loadFields = fields
        if not force:
            extraFields = {'attachedToId', 'attachedToType'}
            if self.resourceParent:
                extraFields.add(self.resourceParent)
            loadFields = self._supplementFields(fields, extraFields)

        doc = Model.load(self, id=id, objectId=objectId, fields=loadFields, exc=exc)

        if not force and doc is not None:
            if doc.get(self.resourceParent):
                loadType = self.resourceColl
                loadId = doc[self.resourceParent]
            else:
                loadType = doc.get('attachedToType')
                loadId = doc.get('attachedToId')
            self.model(loadType).load(loadId, level=level, user=user, exc=exc)

            self._removeSupplementalFields(doc, fields)

        return doc

    def hasAccess(self, resource, user=None, level=AccessType.READ):
        """
        Determines if a user has access to a resource based on their access to
        the resourceParent.

        Takes the same parameters as
        :py:func:`girder.models.model_base.AccessControlledModel.hasAccess`.
        """
        resource = self.model(self.resourceColl) \
                       .load(resource[self.resourceParent], force=True)
        return self.model(self.resourceColl).hasAccess(
            resource, user=user, level=level)

    def hasAccessFlags(self, doc, user=None, flags=None):
        """
        See the documentation of AccessControlledModel.hasAccessFlags, which this wraps.
        """
        if not flags:
            return True

        resource = self.model(self.resourceColl).load(doc[self.resourceParent], force=True)
        return self.model(self.resourceColl).hasAccessFlags(resource, user, flags)

    def requireAccess(self, doc, user=None, level=AccessType.READ):
        """
        This wrapper just provides a standard way of throwing an
        access denied exception if the access check fails.
        """
        if not self.hasAccess(doc, user, level):
            if level == AccessType.READ:
                perm = 'Read'
            elif level == AccessType.WRITE:
                perm = 'Write'
            elif level in (AccessType.ADMIN, AccessType.SITE_ADMIN):
                perm = 'Admin'
            else:
                perm = 'Unknown level'
            if user:
                userid = str(user.get('_id', ''))
            else:
                userid = None
            raise AccessException("%s access denied for %s %s (user %s)." %
                                  (perm, self.name, doc.get('_id', 'unknown'),
                                   userid))

    def requireAccessFlags(self, doc, user=None, flags=None):
        """
        See the documentation of AccessControlledModel.requireAccessFlags, which this wraps.
        """
        if not flags:
            return

        resource = self.model(self.resourceColl).load(doc[self.resourceParent], force=True)
        return self.model(self.resourceColl).requireAccessFlags(resource, user, flags)

    def filterResultsByPermission(self, cursor, user, level, limit=0, offset=0,
                                  removeKeys=(), flags=None):
        """
        Yields filtered results from the cursor based on the access control
        existing for the resourceParent.

        Takes the same parameters as
        :py:func:`girder.models.model_base.AccessControlledModel.filterResultsByPermission`.
        """
        # Cache mapping resourceIds -> access granted (bool)
        resourceAccessCache = {}

        def hasAccess(_result):
            resourceId = _result[self.resourceParent]

            # return cached check if it exists
            if resourceId in resourceAccessCache:
                return resourceAccessCache[resourceId]

            # if the resourceId is not cached, check for permission "level"
            # and set the cache
            resource = self.model(self.resourceColl).load(resourceId, force=True)
            val = self.model(self.resourceColl).hasAccess(
                resource, user=user, level=level)

            if flags:
                val = val and self.model(self.resourceColl).hasAccessFlags(
                    resource, user=user, flags=flags)

            resourceAccessCache[resourceId] = val
            return val

        endIndex = offset + limit if limit else None
        filteredCursor = six.moves.filter(hasAccess, cursor)
        for result in itertools.islice(filteredCursor, offset, endIndex):
            for key in removeKeys:
                if key in result:
                    del result[key]
            yield result

    def textSearch(self, query, user=None, filters=None, limit=0, offset=0,
                   sort=None, fields=None, level=AccessType.READ):
        filters, fields = self._textSearchFilters(query, filters, fields)
        cursor = self.findWithPermissions(
            filters, offset=offset, limit=limit, sort=sort, fields=fields,
            user=user, level=level)
        if (sort is None and callable(getattr(cursor, 'count', None)) and
                cursor.count() < TEXT_SCORE_SORT_MAX):
            sort = [('_textScore', {'$meta': 'textScore'})]
            cursor = self.findWithPermissions(
                filters, offset=offset, limit=limit, sort=sort, fields=fields,
                user=user, level=level)
        return cursor

    def prefixSearch(self, query, user=None, filters=None, limit=0, offset=0,
                     sort=None, fields=None, level=AccessType.READ,
                     prefixSearchFields=None):
        """
        Custom override of Model.prefixSearch to also force permission-based
        filtering. The parameters are the same as Model.prefixSearch.

        :param user: The user to apply permission filtering for.
        :type user: dict or None
        :param level: The access level to require.
        :type level: girder.constants.AccessType
        """
        filters = self._prefixSearchFilters(query, filters, prefixSearchFields)

        return self.findWithPermissions(
            filters, offset=offset, limit=limit, sort=sort, fields=fields,
            user=user, level=level)

    def permissionClauses(self, user=None, level=None, prefix=''):
        return _permissionClauses(user, level, prefix)

    def findWithPermissions(self, query=None, offset=0, limit=0, timeout=None, fields=None,
                            sort=None, user=None, level=AccessType.READ, **kwargs):
        """
        Search the collection by a set of parameters, only returning results
        that the combined user and level have permission to access. Passes any
        extra kwargs through to the underlying pymongo.collection.find
        function.

        :param query: The search query (see general MongoDB docs for "find()")
        :type query: dict
        :param offset: The offset into the results
        :type offset: int
        :param limit: Maximum number of documents to return
        :type limit: int
        :param timeout: Cursor timeout in ms. Default is no timeout.
        :type timeout: int
        :param fields: A mask for filtering result documents by key, or None to return the full
            document, passed to MongoDB find() as the `projection` param.
        :type fields: `str, list of strings or tuple of strings for fields to be included from the
            document, or dict for an inclusion or exclusion projection`.
        :param sort: The sort order.
        :type sort: List of (key, order) tuples.
        :param user: The user to check policies against.
        :type user: dict or None
        :param level: The access level.  Explicitly passing None skips doing
            permissions checks.
        :type level: AccessType
        :returns: A pymongo Cursor, CommandCursor, or an iterable.  If a
            CommandCursor, it has been augmented with a count function.
        """
        # If no user is specified and greater than READ access is requested,
        # we won't return anything.  So as to always return a cursor for
        # consistency, we make a query that will return no results
        if user is None and level is not None and level > AccessType.READ:
            query = {'__matchnothing': 'nothing'}
        elif level is not None and (not user or not user['admin']):
            # If the resourceColl isn't an access controlled model that we
            # know how to reach, fall back to performing the ordinary query and
            # then filtering it by permission.  For instance, if a model uses
            # the acl mixin to get acl from a model that itself uses the acl
            # mixin, this will return the correct results, but without the
            # utility of being able perform count().
            #  Note, this also handles models which use attachedToType and
            # attachedToId, since self.model(None) will not be an access
            # controlled model.
            #  This is also the fall-back for Mongo < 3.4, as those versions do
            # not support the aggregation steps that are used.
            if (not isinstance(self.model(self.resourceColl), AccessControlledModel) or
                    not getattr(self, '_dbserver_version', None) or
                    getattr(self, '_dbserver_version', None) < (3, 4)):
                cursor = self.find(query, timeout=timeout, fields=fields, sort=sort, **kwargs)
                return self.filterResultsByPermission(
                    cursor=cursor, user=user, level=level, limit=limit, offset=offset)
            query = query or {}
            initialPipeline = [
                {'$match': query},
                {'$lookup': {
                    'from': self.resourceColl,
                    'localField': self.resourceParent,
                    'foreignField': '_id',
                    'as': '_access'
                }},
                {'$match': self.permissionClauses(user, level, '_access.')},
            ]
            countPipeline = initialPipeline[:] + [
                {'$group': {'_id': None, 'count': {'$sum': 1}}},
            ]
            fullPipeline = initialPipeline[:] + [
                {'$project': {'_access': False}},
            ]
            if sort is not None:
                fullPipeline.append({'$sort': collections.OrderedDict(sort)})
            if fields is not None:
                if any([isinstance(v, bool) for v in fields.values()]):
                    fullPipeline.append({'$project': fields})
                else:
                    fullPipeline.append({'$addFields': fields})
            if offset:
                fullPipeline.append({'$skip': offset})
            if limit:
                fullPipeline.append({'$limit': limit})
            options = {
                'allowDiskUse': True,
            }
            if timeout:
                options['maxTimeMS'] = timeout
            result = self.collection.aggregate(fullPipeline, **options)

            def count():
                try:
                    return next(iter(self.collection.aggregate(countPipeline, **options)))['count']
                except StopIteration:
                    # If there are no values, this won't return the count, in
                    # which case it is zero.
                    return 0

            result.count = count
            return result
        return self.find(query, offset, limit, timeout, fields, sort, **kwargs)
