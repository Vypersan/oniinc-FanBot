import json
import sqlite3
from colorama import Fore
import aiosqlite
import discord
from datetime import datetime
from discord import app_commands
from CustomErrors import errors
import os

current_date_pretty = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
logname = datetime.now()
logname_pretty = logname.strftime("%d-%m-%Y")
timestamp = logname
bot_version = "0.1"
database_file_path = "./database.db"


async def connect_database():
    return await aiosqlite.connect(database_file_path)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def is_bot_admin():
    async def predicate(interaction: discord.Interaction):
        if is_bot_developer(interaction.user.id):
            return True

    return app_commands.check(predicate)


def is_bot_developer(member_id):
    database = sqlite3.connect(database_file_path)
    try:
        listdevs = database.execute(f"SELECT * FROM botdevs WHERE userid = {member_id}")
        returndevs = listdevs.fetchall()
        if not returndevs:
            database.close()
            raise errors.NotAdminError("You fucking baffoon")
        else:
            database.close()
            return True
    except ValueError:
        pass


async def get_prefix(_bot, message):
    for guild in _bot.guilds:
        db = await aiosqlite.connect(database_file_path)
        try:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS guilds (guildID INT PRIMARY KEY, prefix text)"
            )
            await db.commit()
        except ValueError:
            pass
        async with db.execute(
            "SELECT prefix FROM guilds WHERE guildID = ?", (guild.id,)
        ) as cursor:
            async for entry in cursor:
                prefix = entry
                return prefix
    try:
        await db.close()
    except ValueError:
        pass


async def on_guild_join(guild):
    database = await aiosqlite.connect(database_file_path)
    try:
        await database.execute(
            "CREATE TABLE IF NOT EXISTS guilds (guildID INT PRIMARY KEY, prefix text)"
        )
        await database.commit()
        await database.execute(
            "INSERT OR IGNORE INTO guilds VALUES (?, ?)", (guild.id, "ks-")
        )
        await database.commit()
        await database.close()
    except ValueError:
        pass


def create_embed(title, color):
    """Creates a Discord embed and returns it (for potential additional modification)"""
    embed = discord.Embed(title=title, color=color)
    return embed


def embed_add_field(embed, title, content, inline=True):
    """Helper function to add an additional field to an embed"""
    embed.add_field(name=title, value=content, inline=inline)


def create_simple_embed(title, color, field_title, field_content):
    """Creates a simple embed with only 1 field"""
    embed = create_embed(title, color)
    embed_add_field(embed, field_title, field_content)
    return embed


def write_log(message):
    """Writes information to the log file of the current day."""
    logs_folder = "./logs"
    if not os.path.isdir(logs_folder):
        os.mkdir(logs_folder)
    with open(f"{logs_folder}/{logname_pretty}.log", "a+") as f:
        f.writelines(f"[{current_date_pretty}]    {message}\n")
        f.close()
    f.close()
    print(Fore.GREEN + "[INFO]    " + Fore.RESET + "Saved log information")


def print_info_line(message):
    """Prints a fancy info message."""
    print(Fore.GREEN + "[INFO]    " + Fore.RESET + message)


def print_warning_line(message):
    """Prints a fancy warning message"""
    print(Fore.YELLOW + "[WARNING]   " + Fore.RESET + message)


def print_exception_msg(message):
    """Prints a fancy exception message."""
    print(Fore.RED + "[ERROR]    " + Fore.RESET + message)


def check_blacklist():
    """Check used by the bot to see if a user is blacklisted. If check failed will inform the user about the blacklist.Uses `is_blacklisted()`"""

    async def precheck(interaction: discord.Interaction):
        if is_blacklisted(interaction.user.id):
            return False
        return True

    return app_commands.check(precheck)


def is_blacklisted(memberid):
    """Database check for blacklisted bot users."""
    database = sqlite3.connect(database_file_path)
    database.execute(
        "CREATE TABLE IF NOT EXISTS blacklist (memberid INTEGER PRIMARY KEY, name TEXT, number TEXT, reason TEXT, duration TEXT)"
    )
    database.commit()
    try:
        list_users = database.execute(
            "SELECT * FROM blacklist WHERE memberid = ?", (memberid,)
        )
        return_users = list_users.fetchall()
        if return_users:
            database.close()
            return True
        else:
            database.close()
            return False
    except ValueError:
        pass


async def error_handling_global(botinteraction: discord.Interaction, error: str):
    """Basic error handling that forwards errors to a channel in our dev server."""
    dev_channel = await botinteraction.client.fetch_channel(1212780223872106556)
    command_user = await botinteraction.client.fetch_user(botinteraction.user.id)
    embed = create_simple_embed(
        title=f"Error in {botinteraction.command.name}.",
        color=discord.Color.red(),
        field_title=f"Issued by {command_user.id} ({command_user.name}) on {logname_pretty}",
        field_content=f"`Traceback:`\n{error}",
    )
    print_exception_msg(error)
    await botinteraction.response.send_message(
        "A error occured with this command. Developers have been informed."
    )
    write_log(
        f"Error in {botinteraction.command.name}. Issued by {command_user.name}. Traceback: {error}"
    )
    return await dev_channel.send(embed=embed)
