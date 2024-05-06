from datetime import datetime
from sqlite3 import IntegrityError
import discord
from discord import app_commands
from typing import Optional
from discord.app_commands import Choice
from discord.ext import commands
import utilities
import io
from CustomErrors.errors import NotAdminError

process = "Starting task {}/2"
current_date_pretty = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
current_date_pretty_text = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")


class Feedback(
    discord.ui.Modal,
    title="feedback",
):
    name = discord.ui.TextInput(
        label="Type:",
        placeholder="Enter your type of feedback. (Ex suggestion, issue etc.)",
        min_length=1,
    )
    feedback = discord.ui.TextInput(
        label="Comment:",
        placeholder="Your comment here.",
        required=True,
        max_length=600,
        style=discord.TextStyle.long,
        min_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        admin = await interaction.client.fetch_channel(1186243956275675166)
        await admin.send(
            f"Feedback by {interaction.user.display_name}\nName: {self.name}\n\n Feedback: **{self.feedback}**"
        )
        return await interaction.response.send_message(
            "Thanks for your feedback! We received it."
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        print(error)
        return await interaction.response.send_message(
            "Oops, something did not go right. Informed the devs."
        )


class Reports(
    discord.ui.Modal,
    title="User report form.",
):
    userid = discord.ui.TextInput(
        label="The user's ID:",
        placeholder="The user's discord ID:",
        min_length=1,
        required=True,
    )
    report = discord.ui.TextInput(
        label="Report description:",
        placeholder="Your report here:",
        required=True,
        max_length=600,
        style=discord.TextStyle.long,
        min_length=10,
    )
    messagelink = discord.ui.TextInput(
        label="Message link (Optional):",
        placeholder="https://discord.com/channels/123456/1345677/13456",
        required=False,
        min_length=10,
    )
    image_link = discord.ui.TextInput(
        label="Image / Video link (Optional):",
        placeholder="https://cdn.discord.com/attachments/12345/12345678/sample.png",
        required=False,
        min_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            reporteduser = await interaction.client.fetch_user(self.userid)
        except discord.errors.HTTPException:
            return await interaction.response.send_message(
                "Please provide a valid user ID!", ephemeral=True
            )
        report_channel = await interaction.client.fetch_channel(1186243956275675166)
        embed = discord.Embed(
            title=f"New user  report by {interaction.user}.", color=discord.Color.red()
        )
        embed.add_field(
            name="User",
            value=f"{reporteduser.mention} ({reporteduser.id})",
            inline=False,
        )
        embed.add_field(name="Description", value=self.report, inline=False)
        embed.add_field(name="Message link", value=self.messagelink, inline=False)
        embed.add_field(name="Image link", value=self.image_link, inline=False)
        embed.set_image(url=self.image_link)
        utilities.print_info_line("New user report received.")
        try:
            await report_channel.send(embed=embed)
        except discord.errors.HTTPException:
            utilities.print_exception_msg(
                f"Failed to set url image for the  report. {discord.errors.HTTPException}. Replaced it with default."
            )
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/1110889660705689631/1110900776630489149/header.png"
            )
            await report_channel.send(embed=embed)
        return await interaction.response.send_message(
            "Thanks for your report! We received it."
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        print(error)
        return await interaction.response.send_message(
            "Oops, something did not go right. Informed the devs."
        )


class admins(commands.Cog):
    """The commands used by devs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="listguilds", description="List all guilds.")
    @utilities.is_bot_admin()
    async def listguilds(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Guilds", color=discord.Color.red())
        i = 0
        with io.StringIO() as f:
            for guild in self.bot.guilds:
                i += 1
                f.writelines(
                    f"{i}\nGUILD NAME: {guild.name}\nGUILD ID: {guild.id}\nMEMBERCOUNT: {guild.member_count}\n----------------\n\n"
                )
            f.seek(0)
            file = discord.File(fp=f, filename=f"{current_date_pretty_text}.txt")
        await interaction.response.send_message(file=file, ephemeral=True)
        f.close()

    @app_commands.command(name="botconf", description="configure the bot.")
    @app_commands.describe(
        action="The action you want to perform.",
        module="The module you wish to load, unloadd or reload. (FolderName.FileName",
        admin="The discord member you want to add, delete as a admin.",
    )
    @utilities.is_bot_admin()
    @app_commands.choices(
        action=[
            Choice(name="Load Module", value="loadm"),
            Choice(name="Unload Module", value="unloadm"),
            Choice(name="Database Setup", value="dbsetup"),
            Choice(name="Add botadmin", value="add_admin"),
            Choice(name="Delete Admin", value="delete_admin"),
            Choice(name="Reload Module", value="reload_module"),
        ]
    )
    async def botconf(
        self,
        interaction: discord.Interaction,
        action: str,
        module: Optional[str] = None,
        admin: Optional[discord.Member] = None,
    ):
        if action == "loadm":
            if not utilities.is_bot_admin():
                return await interaction.response.send_message(
                    "You are not a botadmin.", ephemeral=True
                )
            else:
                if module is not None:
                    try:
                        await self.bot.load_extension(module)
                    except Exception as e:
                        return await interaction.response.send_message(
                            f"{type(e).__name__} - {e}"
                        )
                    return await interaction.response.send_message(f"Loaded `{module}`")
                else:
                    return await interaction.response.send_message(
                        "You did not provide a module."
                    )
        elif action == "unloadm":
            if not utilities.is_bot_admin():
                return await interaction.response.send_message(
                    "You are not a botadmin.", ephemeral=True
                )
            else:
                if module is not None:
                    try:
                        await self.bot.unload_extension(module)
                    except Exception as e:
                        return await interaction.response.send_message(
                            f"{type(e).__name__} - {e}"
                        )
                    return await interaction.response.send_message(f"Unloaded {module}")
        if action == "reload_module":
            if not utilities.is_bot_admin():
                return await interaction.response.send_message(
                    "You are not a botadmin.", ephemeral=True
                )
            else:
                if module is not None:
                    try:
                        await self.bot.unload_extension(module)
                    except Exception as e:
                        return await interaction.response.send_message(
                            f"{type(e).__name__} - {e}"
                        )
                    try:
                        await self.bot.load_extension(module)
                    except Exception as e:
                        return await interaction.response.send_message(
                            f"{type(e).__name__} - {e}"
                        )
                    return await interaction.response.send_message(f"Reloaded {module}")
                else:
                    return await interaction.response.send_message(
                        "You did not provide a module."
                    )

        if action == "dbsetup":
            if not utilities.is_bot_admin():
                return await interaction.response.send_message(
                    "You are not a botadmin."
                )
            else:
                database = await utilities.connect_database()
                await database.execute(
                    "CREATE TABLE IF NOT EXISTS guilds (guildID INTEGER PRIMARY KEY, prefix TEXT)"
                )
                await database.commit()
                await database.execute(
                    "CREATE TABLE IF NOT EXISTS moderationLogs (logid INTEGER PRIMARY KEY, guildid INTEGER, moderationLogType INTEGER, userid INTEGER, moduserid INTEGER, content VARCHAR, duration INTEGER)"
                )
                await database.execute(
                    "CREATE TABLE IF NOT EXISTS logtypes (ID INTEGER PRIMARY KEY, type TEXT)"
                )
                await database.commit()
                await database.execute(
                    "CREATE TABLE IF NOT EXISTS botdevs (userid INTEGER PRIMARY KEY, name TEXT)"
                )

                await database.commit()
                await database.execute(
                    "CREATE TABLE IF NOT EXISTS economy (userid INTEGER PRIMARY KEY, balance BIGINT)"
                )
                await database.commit()
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        1,
                        "warn",
                    ),
                )
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        2,
                        "mute",
                    ),
                )
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        3,
                        "unmute",
                    ),
                )
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        4,
                        "kick",
                    ),
                )
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        5,
                        "softban",
                    ),
                )
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        6,
                        "ban",
                    ),
                )
                await database.execute(
                    "INSERT OR IGNORE INTO logtypes VALUES (?, ?)",
                    (
                        7,
                        "unban",
                    ),
                )
                await database.commit()
                try:
                    await database.close()
                except ValueError:
                    pass
                return await interaction.response.send_message("Done!")
        if action == "add_admin":
            if not utilities.is_bot_admin():
                return await interaction.response.send_message(
                    "You are not a botadmin!", ephemeral=True
                )
            else:
                if admin is not None:
                    database = await utilities.connect_database()
                    try:
                        await database.execute(
                            "INSERT INTO botdevs VALUES (?, ?)",
                            (admin.id, admin.name),
                        )
                    except IntegrityError:
                        return await interaction.response.send_message(
                            "This user is already a bot admin."
                        )
                    await database.commit()
                    try:
                        await database.close()
                    except ValueError:
                        pass
                    return await interaction.response.send_message("Done!")
                else:
                    return await interaction.response.send_message(
                        "You did not provide a admin to add."
                    )
        if action == "delete_admin":
            if not utilities.is_bot_admin():
                return await interaction.response.send_message(
                    "You are not a bot admin.", ephemeral=True
                )
            else:
                if admin is not None:
                    database = await utilities.connect_database()
                    try:
                        await database.execute(
                            f"DELETE FROM botdevs WHERE userid = {admin.id} "
                        )
                        await database.commit()
                    except Exception as e:
                        try:
                            await database.close()
                        except ValueError:
                            pass
                        return await interaction.response.send_message(
                            f"Sorry something went wrong.\n\nTraceback:`{e}`."
                        )
                    try:
                        await database.close()
                    except ValueError:
                        pass
                    return await interaction.response.send_message("Done!")

    @commands.command(name="listadmins")
    async def list_admins(self, ctx):
        database = await utilities.connect_database()
        if not utilities.is_bot_developer(ctx.author.id):
            return await ctx.send_message(
                "No permission to use this command.", ephemeral=True
            )
        message = "Bot admins:\n"
        async with database.execute("SELECT userid, name FROM botdevs") as cursor:
            async for entry in cursor:
                userid, username = entry
                message += f"Dev ID: {userid} -- Dev Name: {username}.\n"

        await ctx.send(message)
        try:
            await database.close()
        except ValueError:
            pass

    @app_commands.command(name="feedback", description="provide feedback!")
    async def feedback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Feedback())

    @app_commands.command(name="reportuser", description="Report a user.")
    @utilities.check_blacklist()
    async def reportuser(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Reports())

    @listguilds.error
    async def on_listguilds_error(
        self, interaction: discord.Interaction, error: discord.app_commands.errors
    ):
        if isinstance(error, NotAdminError):
            return await interaction.response.send_message(
                "Only botadmins can use this command.", ephemeral=True
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @list_admins.error
    async def on_listadmins_error(
        self, interaction: discord.Interaction, error: discord.app_commands.errors
    ):
        if isinstance(error, NotAdminError):
            return await interaction.response.send_message(
                "Only botadmins can use this command.", ephemeral=True
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @botconf.error
    async def on_botconf_error(
        self, interaction: discord.Interaction, error: discord.app_commands.errors
    ):
        if isinstance(error, NotAdminError):
            return await interaction.response.send_message(
                "Only botadmins can use this command.", ephemeral=True
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @feedback.error
    async def on_feedback_error(
        self, interaction: discord.Interaction, error: discord.app_commands.errors
    ):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            return await interaction.response.send_message(
                "Sorry, this command is on cooldown.", ephemeral=True
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @reportuser.error
    async def on_feedback_error(
        self, interaction: discord.Interaction, error: discord.app_commands.errors
    ):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            return await interaction.response.send_message(
                "Sorry, this command is on cooldown.", ephemeral=True
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(admins(bot))
