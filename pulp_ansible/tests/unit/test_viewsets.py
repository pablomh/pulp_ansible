from unittest import mock

from django.http import QueryDict
from django.test import TestCase

from pulp_ansible.app.utils import COLLECTION_VERSION_LARGE_FIELDS
from pulp_ansible.app.viewsets import CollectionVersionViewSet


class TestCollectionVersionViewSetQueryset(TestCase):
    """Test that CollectionVersionViewSet defers the large JSON fields."""

    def _select_clause(self, method="GET", query_string=""):
        view = CollectionVersionViewSet()
        view.action = "list"
        view.request = mock.Mock(method=method, query_params=QueryDict(query_string))
        return str(view.get_queryset().query).split(" FROM ")[0]

    def test_get_defers_large_fields(self):
        """The large JSON fields are not selected when they are not rendered."""
        select = self._select_clause()
        for field in COLLECTION_VERSION_LARGE_FIELDS:
            self.assertNotIn(field, select)

    def test_get_keeps_requested_large_field(self):
        """A large field listed in fields is selected."""
        select = self._select_clause(query_string="fields=docs_blob")
        self.assertIn("docs_blob", select)
        for field in ("files", "manifest", "contents"):
            self.assertNotIn(field, select)

    def test_post_does_not_defer_large_fields(self):
        """Non-GET requests keep all fields selected."""
        select = self._select_clause(method="POST")
        for field in COLLECTION_VERSION_LARGE_FIELDS:
            self.assertIn(field, select)
