"""
Central Registry of Action Skills for S.H.I.V.A.
Exposes tools to Gemini's Function Calling engine.
"""

from skills.system_skills import (
    get_system_health,
    open_in_chrome,
    search_google,
    open_social_profile,
    open_application,
)
from skills.project_skills import (
    list_projects,
    open_project_in_ide,
)
from skills.file_skills import (
    list_files,
    read_file,
    edit_file,
    create_or_write_file,
    safe_delete_path,
)

# All tool functions exposed to Gemini Brain
ALL_TOOLS = [
    get_system_health,
    open_in_chrome,
    search_google,
    open_social_profile,
    open_application,
    list_projects,
    open_project_in_ide,
    list_files,
    read_file,
    edit_file,
    create_or_write_file,
    safe_delete_path,
]

# Mapping name -> callable for execution
TOOL_MAP = {func.__name__: func for func in ALL_TOOLS}

