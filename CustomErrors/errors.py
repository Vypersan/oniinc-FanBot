from discord import app_commands


class NotAdminError(app_commands.CheckFailure):
    """Error class for when a user is not a bot admin and tries to execute a command with the `utilities.is_bot_admin()` check"""

    pass


class NotPremiumUser(app_commands.CheckFailure):
    """Error class for when a user is not a premium user."""

    pass
