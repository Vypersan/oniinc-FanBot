from argparse import ArgumentParser
from typing import Optional
import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy
from discord.ext.commands.errors import ExtensionAlreadyLoaded
import assets
import utilities
from datetime import datetime
import logging
import platform
import os
from discord.app_commands.errors import MissingPermissions

parser = ArgumentParser(description="Run bot in live mode.")
parser.add_argument("--live", action="store_true")
parser.add_argument(
    "--disablelog", action="store_true", help="Disable the custom logger"
)
parser.add_argument("--info", action="store_true", help="Information about the bot ")
args = parser.parse_args()

if args.info:
    utilities.print_info_line(
        f"\nBOT VERSION: {utilities.bot_version}\nPYTHON VERSION: {platform.python_version()}\nDISCORD VERSION: {discord.__version__}"
    )
    exit()

dev_mode = not args.live
appID = 860992699783839814 if dev_mode else 1236751027818987620

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
# Normal server 981259218122338354  |||||| Dev server 1038431009676460082
MY_GUILD = discord.Object(id=1038431009676460082)


class oniinc(commands.Bot):
    def __init__(self, intents=intents):
        super().__init__(
            intents=intents,
            command_prefix=commands.when_mentioned,
            application_id=appID,
            description="Demon unit 13, fuck your speakers.",
        )

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=MY_GUILD)

    async def on_ready(self):
        utilities.print_info_line(f"{self.user} has connected to the gateaway")
        for extension in assets.modules:
            try:
                await bot.load_extension(extension)
            except ExtensionAlreadyLoaded:
                if not args.disablelog:
                    utilities.write_log(
                        f"Could not load {extension} as it is already loaded."
                    )
                utilities.print_warning_line(
                    f"Could not load {extension} as it is already loaded."
                )
            if not args.disablelog:
                utilities.print_info_line(f"Loaded {extension}")
                utilities.write_log(f"Loaded {extension}")
        await bot.change_presence(
            activity=discord.Game(
                name=f"Watching {len(self.guilds)} servers with {len(self.users)} users "
            )
        )
        if not args.disablelog:
            utilities.print_info_line(f"Loaded Everything and bot is online")
            current_date_pretty = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            utilities.write_log(f"{self.user} is online from {current_date_pretty}")


bot = oniinc(intents=intents)
bot.remove_command("help")


"""
*sync -> global sync
*sync guild -> sync current guild
*sync copy -> copies all global app commands to current guild and syncs
*sync delete -> clears all commands from the current guild target and syncs (removes guild commands)
*sync id_1 id_2 -> sync  guilds with 1 and 2
"""


@bot.command(name="synccmd")
@utilities.is_bot_admin()
async def sync(
    ctx: Context, guilds: Greedy[discord.Object], spec: Optional[str] = None
) -> None:
    if not guilds:
        if spec == "guild":
            synced = await ctx.bot.tree.sync()
        elif spec == "copy":
            ctx.bot.tree.copy_global_to(guild=MY_GUILD)
            synced = await ctx.bot.tree.sync()
        elif spec == "delete":
            ctx.bot.tree.clear_commands()
            await ctx.bot.tree.sync()
            synced = []
        else:
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
            if not args.disablelog:
                utilities.print_info_line(
                    f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
                )
        return
    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1
    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


json_folder = "./jsonfiles"

if not os.path.isdir(json_folder):
    os.mkdir(json_folder)
if not os.path.isfile(assets.json_config):
    utilities.print_exception_msg("Config file not found!")
    exit()

json = utilities.load_json(assets.json_config)
token = json["dev_token"] if dev_mode else json["token"]

if not os.path.isfile(utilities.database_file_path):
    utilities.print_exception_msg("Database file not found")
    exit()


try:
    if args.disablelog:
        utilities.print_warning_line(
            "Disabled Custom cli logger. Raw errors/output will now be put to the console too."
        )
        bot.run(token)
    else:
        utilities.print_warning_line("Custom logger enabled.")
        handler = discord.utils.setup_logging(level=logging.WARNING, root=False)
        bot.run(token, log_handler=handler)
except KeyboardInterrupt:
    utilities.write_log("Bot shutdown.")
    utilities.print_warning_line("Exit")
    exit()


@sync.error
async def on_fbauth_error(
    interaction: discord.Interaction, error: discord.app_commands.errors
):
    if isinstance(error, MissingPermissions):
        return await interaction.response.send_message(
            "You do not have enough permissions to use this command", ephemeral=True
        )
    else:
        await utilities.error_handling_global(
            botinteraction=interaction, error=str(error)
        )
        utilities.write_log(
            f"Error occured in {interaction.command.name}. {str(error)}"
        )
