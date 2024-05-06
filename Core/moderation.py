import re
import sqlite3
import discord
import discord.errors
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions
import utilities
import datetime

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}
current_date_pretty = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def log_counter():
    db = sqlite3.connect(utilities.database_file_path)
    cur = db.cursor()
    cur.execute("SELECT COUNT (*) FROM moderationLogs")
    global new_case
    result = cur.fetchone()
    new_case = result[0] + 1
    return new_case


def log_converter(type):
    global newtype
    if type == 1:
        newtype = "warn"
        return newtype
    elif type == 2:
        newtype = "mute"
        return newtype
    elif type == 3:
        newtype = "unmute"
        return newtype
    elif type == 4:
        newtype = "kick"
        return newtype
    elif type == 5:
        newtype = "softban"
        return newtype
    elif type == 6:
        newtype = "ban"
        return newtype
    elif type == 7:
        newtype = "unban"
        return newtype


class TimeConverter(commands.Converter):
    async def convert(argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k] * float(v)
            except KeyError:
                raise commands.BadArgument(
                    "{} is an invalid time-key! h/m/s/d are valid!".format(k)
                )
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        return time


class moderation(commands.Cog):
    """Moderation commands for people who do not behave."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="modlogs", description="See the moderation logs of a user."
    )
    @app_commands.describe(memberid="The discord ID of the member you want to check.")
    @commands.has_permissions(kick_members=True)
    async def modlogs(self, interaction: discord.Interaction, memberid: str):
        db = await utilities.connect_database()
        if str(memberid).lower().__contains__("<"):
            memberid = memberid.replace("<", "").replace(">", "").replace("@", "")
        try:
            member = await interaction.guild.fetch_member(memberid)
        except discord.errors.NotFound:
            return await interaction.response.send_message("That is not a valid user.")
        if member.global_name is not None:
            name = member.global_name
        else:
            name = member.display_name
        modlog_embed = discord.Embed(title=f"Showing logs for {member.id} ({name}):")
        select = await db.execute(
            f"SELECT * FROM moderationLogs WHERE guildid = ?", (interaction.guild.id,)
        )
        select_fetch = await select.fetchall()
        if len(select_fetch) < 1:
            modlog_embed.title = "No logs found!"
            modlog_embed.color = discord.Color.red()
            modlog_embed.description = "This user does not have any logs."
            try:
                await db.close()
            except ValueError:
                pass
            return await interaction.response.send_message(embed=modlog_embed)
        else:
            async with db.execute(
                f"SELECT logid, moderationLogType, userid, moduserid, content, duration FROM moderationLogs WHERE guildid = {interaction.guild.id} AND userid = {member.id}",
            ) as f:
                async for entry in f:
                    logid, Logtype, userid, moduserid, content, duration = entry
                    ModerationLogType = log_converter(Logtype)
                    get_user = await interaction.guild.fetch_member(userid)
                    get_mod = await interaction.guild.fetch_member(moduserid)
                    if duration == 0:
                        modlog_embed.add_field(
                            name=f"Case {logid}",
                            value=f"**User:** {userid} ({get_user.mention})\n**Moderator**: {moduserid} ({get_mod.mention})\n**Type**: {ModerationLogType}\n**Reason**: {content}",
                            inline=False,
                        )
                    else:
                        modlog_embed.add_field(
                            name=f"Case {logid}",
                            value=f"**User:** {userid} ({get_user.mention})\n**Moderator**: {moduserid} ({get_mod.mention})\n**Type**: {ModerationLogType}\n**Reason**: {content}\n**Duration**: {duration}",
                            inline=False,
                        )
            try:
                await db.close()
            except ValueError:
                pass
            return await interaction.response.send_message(embed=modlog_embed)

    @app_commands.command(name="warn", description="Warn a user.")
    @app_commands.describe(
        memberid="The ID / @mention of the user you want to warn.",
        reason="The reason of warning that member.",
    )
    @commands.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, memberid: str, reason: str):
        db = await utilities.connect_database()
        if str(memberid).lower().__contains__("<"):
            memberid = memberid.replace("<", "").replace(">", "").replace("@", "")
        try:
            member = await interaction.guild.fetch_member(memberid)
        except discord.errors.NotFound:
            return await interaction.response.send_message("That is not a valid user.")
        warn_embed = discord.Embed()
        if member == self.bot:
            warn_embed.description = f"❌ I can not warn myself."
            warn_embed.color = discord.Color.red()
        elif member == interaction.user:
            warn_embed.description = "❌ You can not warn yourself."
            warn_embed.color = discord.Color.red()
        elif interaction.user.top_role < member.top_role:
            warn_embed.description = "❌ This user has a higher role then you."
            warn_embed.color = discord.Color.red()
        else:
            case_id = log_counter()
            await db.execute(
                "INSERT INTO moderationLogs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    case_id,
                    interaction.guild.id,
                    1,
                    member.id,
                    interaction.user.id,
                    reason,
                    0,
                ),
            )
            await db.commit()
            warn_embed.color = discord.Color.green()
            try:
                await member.send(
                    f"You got warned in {interaction.guild.name}  for: `{reason}`."
                )
            except discord.errors.HTTPException:
                warn_embed.description = f"Logged warning for {member.mention} with reason: {reason}. but I could not dm them."
            warn_embed.description = f"Warned {member.mention} for {reason}"
        try:
            await db.close()
        except ValueError:
            pass
        return await interaction.response.send_message(embed=warn_embed)

    @app_commands.command(
        name="delcase", description="Remove a case from a user's log."
    )
    @app_commands.describe(
        caseno="The case number you wish to delete, you can check that in the modlogs."
    )
    @commands.has_permissions(kick_members=True)
    async def delcase(self, interaction: discord.Interaction, caseno: int):
        db = await utilities.connect_database()
        select = await db.execute(
            f"SELECT * FROM moderationLogs WHERE logid = {caseno} AND guildid = {interaction.guild.id}"
        )
        select_result = await select.fetchall()
        delcase_embed = discord.Embed()
        if not select_result:
            delcase_embed.color = discord.Color.red()
            delcase_embed.description = "No case like that exists."
        else:
            delcase_embed.color = discord.Color.green()
            delcase_embed.description = f"✅ Deleted case {caseno}"
            await db.execute(
                f"DELETE FROM moderationLogs WHERE logid = {caseno} AND guildid = {interaction.guild.id}"
            )
            await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        return await interaction.response.send_message(embed=delcase_embed)

    @app_commands.command(name="ban", description="ban a user.")
    @app_commands.describe(
        memberid="The user ID or @mention of the user you want to ban.",
        reason="The reason you want to ban this user for.",
    )
    @commands.has_permissions(ban_members=True)
    async def ban_user(
        self, interaction: discord.Interaction, memberid: str, reason: str
    ):
        if str(memberid).lower().__contains__("<"):
            memberid = memberid.replace("<", "").replace(">", "").replace("@", "")
        try:
            member = await interaction.guild.fetch_member(memberid)
        except discord.errors.NotFound:
            return await interaction.response.send_message("That is not a valid user.")
        db = await utilities.connect_database()
        banned_emebed = discord.Embed()
        if member == self.bot:
            banned_emebed.description = "I can not ban myself."
            banned_emebed.color = discord.Color.red()
        elif member == interaction.user:
            banned_emebed.description = "You can not ban yourself."
            banned_emebed.color = discord.Color.red()
        try:
            await interaction.guild.ban(
                user=member, reason=reason, delete_message_days=7
            )
        except discord.errors.NotFound:
            return await interaction.response.send_message(
                "Sorry something went wrong."
            )
        new_case = log_counter()
        await db.execute(
            "INSERT INTO moderationLogs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                new_case,
                interaction.guild.id,
                6,
                member.id,
                interaction.user.id,
                reason,
                0,
            ),
        )
        await db.commit()
        try:
            await member.send(
                f"You got banned in {interaction.guild.name} for {reason}. "
            )
        except discord.errors.HTTPException:
            banned_emebed.description = f"Banned {member.mention} ({member.id}) for {reason}. But I could not dm them."
        banned_emebed.color = discord.Color.green()
        banned_emebed.description = (
            f"Banned {member.mention} ({member.id}) for {reason}."
        )
        await interaction.response.send_message(embed=banned_emebed)
        try:
            return await db.close()
        except ValueError:
            return

    @app_commands.command(name="kick", description="kick a user with the given reason.")
    @utilities.check_blacklist()
    @app_commands.describe(
        memberid="the user ID OR the @ of the member you want to kick",
        reason="The reason as to why you want to kick a user.",
    )
    async def kick(
        self, interaction: discord.Interaction, memberid: str, reason: str = None
    ):
        if str(memberid).lower().__contains__("<"):
            memberid = memberid.replace("<", "").replace(">", "").replace("@", "")
        try:
            member = await interaction.guild.fetch_member(memberid)
        except discord.errors.NotFound:
            return await interaction.response.send_message("That is not a valid user.")
        db = await utilities.connect_database()
        user_kick_embed = discord.Embed(
            title=f"You have been kicked from {interaction.guild.id}",
            color=discord.Color.red(),
            description=reason,
        )
        kick_embed = discord.Embed()
        if member == self.bot:
            kick_embed.description = "I can not kick myself."
            kick_embed.color = discord.Color.red()
        elif member == interaction.user:
            kick_embed.description = "You can not kick yourself."
            kick_embed.color = discord.Color.red()
        try:
            await interaction.guild.kick(user=member, reason=reason)
        except discord.errors.NotFound as e:
            utilities.write_log(f"Error in kick. {e}")
            kick_embed.description = "Sorry something went wrong."
            utilities.error_handling_global(botinteraction=interaction, error=str(e))
        new_case = log_counter()
        await db.execute(
            "INSERT INTO moderationLogs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                new_case,
                interaction.guild.id,
                4,
                member.id,
                reason,
                0,
            ),
        )
        await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        try:
            await member.send(embed=user_kick_embed)
        except discord.errors.Forbidden:
            kick_embed.color = discord.Color.orange()
            kick_embed.description = (
                f"Kicked {member.name} for {reason}. But I could not dm them. "
            )
        kick_embed.color = discord.Color.green()
        kick_embed.description = (
            f"Kicked {member.name} for {reason}. They have been informed in dms."
        )
        return await interaction.response.send_message(embed=kick_embed)

    @app_commands.command(
        name="unban", description="unban a user with the given reason."
    )
    @app_commands.describe(
        memberid="The user ID or @mention of the user you want to unban",
        reason="The reason you want to unban this user for.",
    )
    @commands.has_permissions(ban_members=True)
    async def unban_user(
        self, interaction: discord.Interaction, memberid: str, reason: str
    ):
        if str(memberid).lower().__contains__("<"):
            memberid = memberid.replace("<", "").replace(">", "").replace("@", "")
        try:
            member = await interaction.client.fetch_user(memberid)
        except discord.errors.NotFound:
            return await interaction.response.send_message("That is not a valid user.")
        db = await utilities.connect_database()
        unbanned_emebed = discord.Embed()
        if member == self.bot:
            unbanned_emebed.description = "I can not unban myself."
            unbanned_emebed.color = discord.Color.red()
        elif member == interaction.user:
            unbanned_emebed.description = "You can not unban yourself."
            unbanned_emebed.color = discord.Color.red()
        try:
            await interaction.guild.unban(user=member, reason=reason)
        except discord.errors.NotFound:
            return await interaction.response.send_message(
                "Sorry something went wrong."
            )
        new_case = log_counter()
        await db.execute(
            "INSERT INTO moderationLogs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                new_case,
                interaction.guild.id,
                7,
                member.id,
                interaction.user.id,
                reason,
                0,
            ),
        )
        await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        try:
            await member.send(
                f"You got unbanned in {interaction.guild.name} for {reason}. "
            )
        except discord.errors.HTTPException:
            unbanned_emebed.description = f"Unbanned {member.mention} ({member.id}) for {reason}. But I could not dm them."
        unbanned_emebed.color = discord.Color.green()
        unbanned_emebed.description = (
            f"Unbanned {member.mention} ({member.id}) for {reason}."
        )
        return await interaction.response.send_message(embed=unbanned_emebed)

    @app_commands.command(
        name="mute", description="Mute a user with the given time and reason."
    )
    @app_commands.describe(
        memberid="The user ID or @member of the person you want to mute.",
        duration="The amount you want to mute them for. Max 14d. (14 days)",
        reason="The reason you want to mute them.",
    )
    @commands.has_permissions(kick_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        memberid: str,
        duration: str,
        reason: str,
    ):
        if str(memberid).lower().__contains__("<"):
            memberid = memberid.replace("<", "").replace(">", "").replace("@", "")
        try:
            member = await interaction.guild.fetch_member(memberid)
        except discord.errors.NotFound:
            return await interaction.response.send_message("That is not a valid user.")
        db = await utilities.connect_database()
        Mute_embed = discord.Embed()
        if member == self.bot:
            Mute_embed.description = "I can not mute myself."
            Mute_embed.color = discord.Color.red()
        elif member == interaction.user:
            Mute_embed.description = "You can not mute yourself."
            Mute_embed.color = discord.Color.red()
        new_case = log_counter()
        try:
            mute_duration = await TimeConverter.convert(duration)
            time_mute = datetime.timedelta(seconds=mute_duration)
        except commands.BadArgument:
            Mute_embed.description = f"{duration} is not a valid key. Please use the following format: 1s for 1 second, 1m for 1 minute, 1h for 1 hour and 1d for one day."
        Mute_embed.description = f"Muted {member.mention} ({member.id}) for {duration}. With the reason: `{reason}`."
        await member.timeout(time_mute, reason=reason)
        await db.execute(
            "INSERT INTO moderationLogs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                new_case,
                interaction.guild.id,
                2,
                member.id,
                interaction.user.id,
                reason,
                duration,
            ),
        )
        await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        return await interaction.response.send_message(embed=Mute_embed)

    @modlogs.error
    async def on_modlog_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, MissingPermissions):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command!",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @warn.error
    async def on_warn_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.errors.Forbidden):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command!",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @delcase.error
    async def on_delcase_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.errors.Forbidden):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command!",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @ban_user.error
    async def on_ban_user_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.errors.Forbidden):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command!",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @unban_user.error
    async def on_unban_user_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.errors.Forbidden):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command!",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @mute.error
    async def on_mute_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.errors.Forbidden):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command!",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(moderation(bot))
