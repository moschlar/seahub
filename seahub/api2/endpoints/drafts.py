# Copyright (c) 2012-2016 Seafile Ltd.
import os
import json
import logging
import posixpath

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from seaserv import seafile_api, edit_repo
from pysearpc import SearpcError
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Count
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from seahub.api2.authentication import TokenAuthentication
from seahub.api2.endpoints.utils import add_org_context
from seahub.api2.throttling import UserRateThrottle
from seahub.api2.utils import api_error
from seahub.constants import PERMISSION_READ_WRITE
from seahub.drafts.models import Draft, DraftFileExist, DraftFileConflict
from seahub.views import check_folder_permission
from seahub.utils import gen_file_get_url

logger = logging.getLogger(__name__)

HTTP_520_OPERATION_FAILED = 520


class DraftsView(APIView):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    throttle_classes = (UserRateThrottle, )

    def get(self, request, format=None):
        """List all user drafts.
        """
        username = request.user.username
        data = [x.to_dict() for x in Draft.objects.filter(username=username)]

        return Response({'data': data})

    @add_org_context
    def post(self, request, org_id, format=None):
        """Create a file draft.
        """
        repo_id = request.POST.get('repo_id', '')
        file_path = request.POST.get('file_path', '')

        repo = seafile_api.get_repo(repo_id)
        if not repo:
            error_msg = 'Library %s not found.' % repo_id
            return api_error(status.HTTP_404_NOT_FOUND, error_msg)

        file_id = seafile_api.get_file_id_by_path(repo.id, file_path)
        if not file_id:
            return api_error(status.HTTP_404_NOT_FOUND,
                             "File %s not found" % file_path)

        # perm check
        perm = check_folder_permission(request, repo.id, file_path)
        if perm != PERMISSION_READ_WRITE:
            error_msg = 'Permission denied.'
            return api_error(status.HTTP_403_FORBIDDEN, error_msg)

        username = request.user.username

        try:
            d = Draft.objects.add(username, repo, file_path, file_id)

            return Response(d.to_dict())
        except (DraftFileExist, IntegrityError):
            return api_error(status.HTTP_409_CONFLICT, 'Draft already exists.')


class DraftView(APIView):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    throttle_classes = (UserRateThrottle, )

    def put(self, request, pk, format=None):
        """Publish a draft.
        """
        op = request.data.get('operation', '')
        if op != 'publish':
            return api_error(status.HTTP_400_BAD_REQUEST,
                             'Operation %s invalid.')

        try:
            d = Draft.objects.get(pk=pk)
        except Draft.DoesNotExist:
            return api_error(status.HTTP_404_NOT_FOUND,
                             'Draft %s not found.' % pk)

        # perm check
        if d.username != request.user.username:
            return api_error(status.HTTP_403_FORBIDDEN,
                             'Permission denied.')

        try:
            d.publish()
            d.delete()
            return Response(status.HTTP_200_OK)
        except (DraftFileConflict, IntegrityError):
            return api_error(status.HTTP_409_CONFLICT,
                             'There is a conflict between the draft and the original file')

    def delete(self, request, pk, format=None):
        """Delete a draft.
        """
        try:
            d = Draft.objects.get(pk=pk)
        except Draft.DoesNotExist:
            return api_error(status.HTTP_404_NOT_FOUND,
                             'Draft %s not found.' % pk)

        # perm check
        if d.username != request.user.username:
            return api_error(status.HTTP_403_FORBIDDEN,
                             'Permission denied.')

        d.delete()

        return Response(status.HTTP_200_OK)
