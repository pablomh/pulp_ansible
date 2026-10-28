from contextvars import ContextVar

from django.conf import settings
from django.db.models import CharField, OuterRef, Q, Subquery
from django.db.models.functions import Cast, JSONObject

from pulpcore.plugin.models import RepositoryContent, RepositoryVersion, Task

_collection_deferred_fields = ContextVar("collection_deferred_fields", default=[])

COLLECTION_VERSION_LARGE_FIELDS = ("docs_blob", "files", "manifest", "contents")


def set_collection_deferred_fields(fields):
    """Set which CollectionVersion fields to defer."""
    _collection_deferred_fields.set(fields)


def get_collection_deferred_fields():
    """Get the list of CollectionVersion fields to defer."""
    return _collection_deferred_fields.get()


def _query_field_names(query_params, arg_name):
    delimiter = getattr(settings, "DRF_QUERYFIELDS_DELIMITER", ",")
    return {
        name for value in query_params.getlist(arg_name) for name in value.split(delimiter) if name
    }


def get_collection_version_deferred_fields(query_params):
    """Get the large CollectionVersion fields that this request will not render.

    Mirrors CollectionVersionSerializer's redaction of ``fields`` and ``exclude_fields``,
    including the handling of empty query parameters.
    """
    include_arg = getattr(settings, "DRF_QUERYFIELDS_INCLUDE_ARG_NAME", "fields")
    exclude_arg = getattr(settings, "DRF_QUERYFIELDS_EXCLUDE_ARG_NAME", "exclude_fields")
    if include_arg not in query_params and exclude_arg not in query_params:
        return list(COLLECTION_VERSION_LARGE_FIELDS)
    include = _query_field_names(query_params, include_arg)
    exclude = _query_field_names(query_params, exclude_arg)
    return [
        field
        for field in COLLECTION_VERSION_LARGE_FIELDS
        if field in exclude or (include and field not in include)
    ]


def filter_content_for_repo_version(qs, repo_version):
    """
    Returns the given queryset, but filtered to only include content
    from the specified repository version.

    qs: Content queryset. Must be a model that is or inherits from
        pulpcore.plugin.models.Content
    repo_version: repository version to return content from

    This generally seems to be faster than repo_version.get_content()
    """

    repo_version_qs = RepositoryVersion.objects.filter(
        repository=repo_version.repository_id, number__lte=repo_version.number
    ).values_list("pk")

    f = (
        Q(repository=repo_version.repository_id)
        & Q(version_added__in=repo_version_qs)
        & Q(Q(version_removed=None) | ~Q(version_removed__in=repo_version_qs))
    )
    content_rel = RepositoryContent.objects.filter(f)

    return qs.filter(pk__in=content_rel.values_list("content_id"))


def get_queryset_annotated_with_last_sync_task(qs):
    last_task = (
        Task.objects.filter(
            name__contains="sync",
            reserved_resources_record__icontains=Cast(OuterRef("pk"), output_field=CharField()),
        )
        .values(
            json=JSONObject(
                pk="pk",
                state="state",
                pulp_created="pulp_created",
                finished_at="finished_at",
                error="error",
            )
        )
        .order_by("-pulp_created")[:1]
    )

    return qs.annotate(last_sync_task=Subquery(last_task))
