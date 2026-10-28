from django.http import QueryDict
from django.test import SimpleTestCase

from pulp_ansible.app.utils import (
    COLLECTION_VERSION_LARGE_FIELDS,
    get_collection_version_deferred_fields,
)


class TestGetCollectionVersionDeferredFields(SimpleTestCase):
    """Test get_collection_version_deferred_fields."""

    def test_no_query_params(self):
        """Without field selection every large field is redacted."""
        self.assertEqual(
            get_collection_version_deferred_fields(QueryDict()),
            list(COLLECTION_VERSION_LARGE_FIELDS),
        )

    def test_fields(self):
        """Only the requested large fields are rendered."""
        self.assertEqual(
            get_collection_version_deferred_fields(QueryDict("fields=docs_blob")),
            ["files", "manifest", "contents"],
        )

    def test_fields_empty(self):
        """An empty fields parameter renders every large field."""
        self.assertEqual(get_collection_version_deferred_fields(QueryDict("fields=")), [])

    def test_exclude_fields(self):
        """Only the excluded large fields are deferred."""
        self.assertEqual(
            get_collection_version_deferred_fields(QueryDict("exclude_fields=docs_blob,files")),
            ["docs_blob", "files"],
        )

    def test_exclude_fields_empty(self):
        """An empty exclude_fields parameter renders every large field."""
        self.assertEqual(
            get_collection_version_deferred_fields(QueryDict("exclude_fields=")),
            [],
        )

    def test_fields_and_exclude_fields(self):
        """fields is an allowlist and exclude_fields removes from it."""
        self.assertEqual(
            get_collection_version_deferred_fields(
                QueryDict("fields=docs_blob,files&exclude_fields=docs_blob")
            ),
            ["docs_blob", "manifest", "contents"],
        )
