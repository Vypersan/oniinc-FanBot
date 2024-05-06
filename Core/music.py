import datetime
import time
import discord
from discord import app_commands
import utilities
from discord.ext import commands, tasks
import assets
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
from aiosqlite import IntegrityError

json = utilities.load_json(assets.json_config)
spot_id = json["spotifyID"]
spot_token = json["spotifyToken"]
client_credentials_manager = SpotifyClientCredentials(
    client_id=spot_id, client_secret=spot_token
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
artist_name = "ONI INC"


class oniinc_checker(commands.Cog):
    """User information"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        @tasks.loop(hours=1)
        async def my_check():
            await notify_new_release()

        my_check.start()

        async def notify_new_release():
            db = await utilities.connect_database()
            # Search for the artist
            results = sp.search(q="artist:" + artist_name, type="artist")
            utilities.write_log(f"Request to spotify API sent for {artist_name}")
            items = results["artists"]["items"]
            if len(items) > 0:
                artist = items[0]
                artist_id = artist["id"]

                #   Get the artist's albums
                singles = sp.artist_albums(artist_id, album_type="single")

                # Check for new releases
                for single in singles["items"]:
                    release_date = datetime.strptime(single["release_date"], "%Y-%m-%d")
                    if release_date > datetime.now():
                        for guild in self.bot.guilds:
                            send_channel = await db.execute(
                                "SELECT channelID from notifychannel WHERE guildID = ?",
                                (guild.id,),
                            )
                            send_channel_check = await send_channel.fetchone()
                            if send_channel_check:
                                channel_to_send = await self.bot.fetch_channel(
                                    send_channel_check[0]
                                )
                                await channel_to_send.send(
                                    f"ONI INC RELEASED {single['name']}. Listen now at {single['external_urls']['spotify']}"
                                )
                            else:
                                utilities.write_log(
                                    f"New song out but {guild.id} does not have a channel set up."
                                )
                                pass
                    else:
                        pass
                        utilities.write_log("No new music")
                        return
                try:
                    await db.close()
                except ValueError:
                    pass
            else:
                try:
                    await db.close()
                except ValueError:
                    pass
                utilities.print_warning_line(f"Artist '{artist_name}' not found.")
                utilities.write_log(f"Artist '{artist_name}' not found.")
                return

    @app_commands.command(
        name="setnotify", description="Set up a channel for me to notify for new songs!"
    )
    async def setnotify(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        db = await utilities.connect_database()
        await db.execute(
            "CREATE TABLE IF NOT EXISTS notifychannel (guildID TEXT UNIQUE, channelID text)"
        )
        await db.commit()
        try:
            await db.execute(
                "INSERT INTO notifychannel VALUES (?, ?)",
                (
                    interaction.guild.id,
                    channel.id,
                ),
            )
        except IntegrityError:
            await db.execute(
                f"UPDATE notifychannel SET channelID  = {channel.id} WHERE guildID = ?",
                (interaction.guild.id,),
            )
        await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        return await interaction.response.send_message(
            f"Alright, I will let you know when a new song is released in {channel.mention}."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(oniinc_checker(bot))
