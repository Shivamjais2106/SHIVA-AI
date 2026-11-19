"""
Central Registry of Action Skills for S.H.I.V.A.
Exposes tools to Gemini's Function Calling engine.
"""

from skills.system_skills import (
    get_system_health,
    open_in_chrome,
    search_google,
    open_portfolio,
    open_social_profile,
    close_browser_tab,
    open_application,
    close_application,
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
from skills.terminal_skills import (
    execute_terminal_command,
)
from skills.media_skills import (
    control_media,
    control_volume,
    open_spotify,
)
from skills.email_skills import (
    open_gmail,
    compose_email_in_browser,
    read_emails,
    send_email,
    get_24h_email_briefing,
    get_morning_briefing,
    get_24h_email_briefing,
    get_morning_briefing,
)
from skills.whatsapp_skills import (
    send_whatsapp_message,
    initiate_whatsapp_call,
    simulate_incoming_whatsapp,
    get_whatsapp_inbox,
    add_known_contact,
    list_known_contacts,
    toggle_whatsapp_auto_responder,
)
from skills.news_skills import (
    get_latest_news,
    get_weather,
    search_web_realtime,
)

# All tool functions exposed to Gemini Brain
ALL_TOOLS = [
    get_system_health,
    open_in_chrome,
    search_google,
    get_latest_news,
    get_weather,
    search_web_realtime,
    open_portfolio,
    open_social_profile,
    close_browser_tab,
    open_application,
    close_application,
    list_projects,
    open_project_in_ide,
    list_files,
    read_file,
    edit_file,
    create_or_write_file,
    safe_delete_path,
    execute_terminal_command,
    control_media,
    control_volume,
    open_spotify,
    open_gmail,
    compose_email_in_browser,
    read_emails,
    send_email,
    get_24h_email_briefing,
    get_morning_briefing,
    send_whatsapp_message,
    initiate_whatsapp_call,
    simulate_incoming_whatsapp,
    get_whatsapp_inbox,
    add_known_contact,
    list_known_contacts,
    toggle_whatsapp_auto_responder,
]

# Mapping name -> callable for execution
TOOL_MAP = {func.__name__: func for func in ALL_TOOLS}
