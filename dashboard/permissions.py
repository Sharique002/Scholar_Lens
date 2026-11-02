"""Role and permission helpers for Scholar Lens."""


def is_office(user) -> bool:
    """Returns True if user belongs to the Research Office (staff user)."""
    return bool(user and user.is_authenticated and user.is_staff)


def is_dean(user) -> bool:
    """
    Returns True if user is the Dean of Research (member of 'Dean of Research' group
    or superuser).
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='Dean of Research').exists()
