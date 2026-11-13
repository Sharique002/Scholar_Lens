# scholar_lens package

# Vendor-safe ExclusionConstraint for database engine portability (PostgreSQL vs SQLite)
try:
    from django.contrib.postgres.constraints import ExclusionConstraint
    _orig_constraint_sql = ExclusionConstraint.constraint_sql
    def _safe_constraint_sql(self, model, schema_editor):
        if schema_editor.connection.vendor != 'postgresql':
            return None
        return _orig_constraint_sql(self, model, schema_editor)
    ExclusionConstraint.constraint_sql = _safe_constraint_sql
except Exception:
    pass
