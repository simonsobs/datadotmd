"""
Tools for sending notifications to users when data and/or metadata changes.
"""

from datetime import datetime
from datadotmd.app.config import settings


def notify_new_data_md_file(update_time: datetime, new_content: str, path: str):
    settings.notifier.notify(
        message=(
            f"*New Data Description for {path}*\n"
            f"> Data description created for {path}\n"
            f"> Time of update: _{update_time.strftime('%Y-%m-%d %H:%M:%S')}_\n"
            f"> View this new data description at:\n"
            f"> {settings.app_base_url}/browse/{path}"
        ),
    )
    return


def notify_changed_data_md_file(update_time: datetime, new_content: str, path: str):
    settings.notifier.notify(
        message=(
            f"*Data Description Updated for {path}*\n"
            f"> Data description updated for {path}\n"
            f"> Time of update: _{update_time.strftime('%Y-%m-%d %H:%M:%S')}_\n"
            f"> View this new data description at:\n"
            f"> {settings.app_base_url}/browse/{path}"
        ),
    )


def notify_data_updated(update_time: datetime, path: str):
    settings.notifier.notify(
        message=(
            f"*Underlying Data Updated at {path}*\n"
            f"> Data was updated at {path} without update to metadata\n"
            f"> Time of update: _{update_time.strftime('%Y-%m-%d %H:%M:%S')}_\n"
            f"> View the data description at:\n"
            f"> {settings.app_base_url}/browse/{path}\n"
            "> _Please consider updating it to match the new data_"
        ),
    )
    return
