import discord
from discord.ext import commands
import utilities as utils
from datetime import datetime

current_date_pretty = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


class eventlist(commands.Cog):
    """Events and listeners"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        tree = self.bot.tree

    @commands.Cog.listener()
    async def on_command(self, command):
        utils.write_log(f"{command.command} by {command.author}")
        utils.print_info_line(f"{command.command} issued by {command.author}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        utils.write_log(f"{interaction.command.name} issued by {interaction.user}.")
        utils.print_info_line(
            f"{interaction.command.name} issued by {interaction.user}."
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            utils.print_exception_msg(
                f"Invalid command was issued by {ctx.author}. Traceback: {error}."
            )
            utils.write_log(
                f"{ctx.author} issued a invalid command. Traceback: {error}."
            )
            return await ctx.reply("Sorry this command does not exist.")
        if isinstance(error, commands.MissingPermissions):
            utils.print_exception_msg(
                f"User missing permissions for the {ctx.command} that was issued in {ctx.guild.name}."
            )
            utils.write_log(f"{ctx.author} is  missing permission(s). {error}.")
            await ctx.reply(
                f"You are missing permissions in this server to execute this command {error}."
            )
        else:
            utils.print_exception_msg(f"Invalid command issued. Traceback: {error}.")
            utils.write_log(
                f"{ctx.author} issued {ctx.command} but something went wrong. {error}."
            )
            await ctx.reply(f"Sorry, something went wrong. `{error}`.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(eventlist(bot))
