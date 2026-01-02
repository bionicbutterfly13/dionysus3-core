import os
import sys


def test_project_root_is_added_to_sys_path():
    import scripts.setup_meta_cognition_schema as schema_script

    root = os.path.abspath(os.path.join(os.path.dirname(schema_script.__file__), ".."))
    original_sys_path = list(sys.path)

    try:
        sys.path = [p for p in sys.path if os.path.abspath(p) != root]
        assert root not in sys.path

        schema_script.ensure_project_root_on_path()

        assert root in sys.path
    finally:
        sys.path = original_sys_path
