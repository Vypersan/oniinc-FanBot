import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):
    """This command."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description="Get a list of all commands you can use."
    )
    async def help(self, interaction: discord.Interaction):
        """help command"""
        return await interaction.response.send_message(
            f"You can find all commands  [HERE](<https://yokaigroup.gg/projects/oni-inc-bot/documentation/>).",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
