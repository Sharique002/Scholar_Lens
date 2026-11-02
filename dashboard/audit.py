from .models import AuditEntry


def record(actor, action: str, target, **data) -> AuditEntry:
    """
    Records an institutional audit entry for critical decisions and actions.
    target_type is stored as target._meta.label_lower (e.g. 'researchers.researcherprofile').
    """
    target_type = target._meta.label_lower
    target_id = target.pk
    return AuditEntry.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        data=data
    )
