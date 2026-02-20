"""
Tools for sending notifications to users when data and/or metadata changes.
"""

from datetime import datetime
from datadotmd.app.config import settings


def notify_new_data_md_file(update_time: datetime, new_content: str, path: str):
    settings.notifier.notify(
        title=f"New Data Description for {path}",
        message=(
            f"Data description created for {path} at {update_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"View this new data description at: {settings.app_base_url}/browse/{path}"
        ),
    )
    return


def notify_changed_data_md_file(update_time: datetime, new_content: str, path: str):
    settings.notifier.notify(
        title=f"Data Description Updated for {path}",
        message=(
            f"Data description updated for {path} at {update_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"View this new data description at: {settings.app_base_url}/browse/{path}"
        ),
    )


def notify_data_updated(update_time: datetime, path: str):
    settings.notifier.notify(
        title=f"Underlying Data Updated at {path}",
        message=(
            f"Data was updated at {path} without update to metadata at {update_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"View the data description at: {settings.app_base_url}/browse/{path} and consider updating it to match the new data."
        ),
    )
    return
