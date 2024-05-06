import datetime
import time
import discord
from discord import app_commands
import utilities
from discord.ext import commands
import platform
import humanize

up_time = time.time()


class userinfo(commands.Cog):
    """User information"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="av", description="Get an user's avatar.")
    @app_commands.describe(
        member="The user you want to get the avater for. Leave empty if you want yours."
    )
    async def av(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        await interaction.response.send_message(member.avatar.url, ephemeral=False)

    @app_commands.command(name="whois", description="Get user information.")
    @app_commands.describe(user="The member you want to view information for.")
    async def whois(
        self, interaction: discord.Interaction, user: discord.Member = None
    ):
        """Check to see who this person is, their roles and other stuff. format: whois @user"""
        if user is None:
            user = interaction.user
        date_format = "%a, %d %b %Y %I:%M %p"
        embed = discord.Embed(color=discord.Color.purple(), description=user.mention)
        embed.set_author(name=str(user), icon_url=user.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Joined:", value=user.joined_at.strftime(date_format))
        members = sorted(interaction.guild.members, key=lambda m: m.joined_at)
        embed.add_field(name="Registered:", value=user.created_at.strftime(date_format))

        if len(user.roles) > 1:
            role_string = " ".join([r.mention for r in user.roles][1:])
            embed.add_field(
                name="Roles: [{}]".format(len(user.roles) - 1),
                value=role_string,
                inline=False,
            )
            embed.set_footer(text="ID: " + str(user.id))
            return await interaction.response.send_message(embed=embed)
        else:
            embed.add_field(name="Roles:", value="None")
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="uptime", description="Check the bot's uptime", auto_locale_strings=True
    )
    async def uptime(self, interaction: discord.Interaction):
        current_time = time.time()
        difference = int(round(current_time - up_time))
        text = str(datetime.timedelta(seconds=difference))

        embed = discord.Embed(colour=interaction.user.top_role.colour)
        embed.add_field(name="Uptime", value=text)
        embed.set_footer(text="I am awake!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="get bot information.")
    async def botinfo(self, interaction: discord.Interaction):
        discord_version = discord.__version__
        python_version = platform.python_version()
        os = platform.system()
        os_version = platform.version()
        total_users = 0
        total_shards = interaction.client.shard_count
        current_shard_id = interaction.client.shard_id
        guilds = len(self.bot.guilds)
        Kitsune = await interaction.client.fetch_user(521028748829786134)
        bot_version = utilities.bot_version
        for guild in interaction.client.guilds:
            total_users += int(guild.member_count)
        embed = discord.Embed(color=discord.Color.green())
        embed.add_field(
            name="Description",
            value="The fan-made discord bot for [ONI INC](<https://open.spotify.com/artist/1dW38AxhFH7xZjV7o3p3l4?si=K67bypkZSQWcoLgjqYEbZQ>). Made for the people who love his music! ",
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=f"**Discord version**: {discord_version}\n**Python Version**: {python_version}\n**OS**: {os}\n**OS Version**: {os_version}\n**Total servers**: {guilds}\n**Bot Version**: {bot_version}\n\n**Total users**: {total_users}\n**Shard count:** {total_shards}\n**Shard ID: {current_shard_id}**",
            inline=False,
        )
        embed.add_field(
            name="Developed by",
            value=f"[{Kitsune.name}](<https://yokaigroup.gg/about/kitsune/>)\n\n[SUPPORT ME](<https://yokaigroup.gg/support-us/>)",
            inline=False,
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="followstatus",
        description="Make the bot post status messages in a channel you decide.",
    )
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(channel="The channel you want to receive updates for.")
    async def followStatus(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Allows people to follow the status channel so they can know when it is down or not."""
        try:
            follow_channel = await interaction.client.fetch_channel(1186257790755418143)
            await follow_channel.follow(destination=channel)
            await interaction.response.send_message(
                f"✅ You will now get status updates in {channel.mention}."
            )
        except Exception as e:
            return await interaction.response.send_message(
                "❌ Sorry failed to follow the status page."
            )

    @app_commands.command(name="guildinfo", description="Get this guild's information.")
    @utilities.check_blacklist()
    async def guildinfo(self, interaction: discord.Interaction):
        """Get info about the guild"""
        guild = await self.bot.fetch_guild(interaction.guild.id)
        embed = discord.Embed(title=f"{guild.name}", description=f"{guild.description}")
        members = interaction.guild.member_count
        embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members:", value=members, inline=False)
        embed.add_field(name="Created at:", value=guild.created_at, inline=False)
        embed.add_field(name="Boost level:", value=guild.premium_tier, inline=False)
        embed.add_field(
            name="Booster count:", value=guild.premium_subscription_count, inline=False
        )
        embed.add_field(
            name="Max Bitrate", value=f"{guild.bitrate_limit} Bits", inline=False
        )
        embed.add_field(name="Server MFA level:", value=guild.mfa_level, inline=False)
        embed.add_field(
            name="Server Verification level:",
            value=str(guild.verification_level).upper(),
            inline=False,
        )
        embed.add_field(name="Role count:", value=len(guild.roles))
        embed.add_field(
            name="Afk timeout:", value=f"{guild.afk_timeout} seconds.", inline=False
        )
        embed.add_field(name="Channels", value=len(interaction.guild.channels))
        await interaction.response.send_message(embed=embed)

    @av.error
    async def on_av_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command.",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @whois.error
    async def on_whois_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command.",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @uptime.error
    async def on_uptime_error(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command.",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @followStatus.error
    async def on_follow_status_eror(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command.",
                ephemeral=True,
            )
        else:
            await utilities.error_handling_global(
                botinteraction=interaction, error=str(error)
            )
            utilities.write_log(
                f"Error occured in {interaction.command.name}. {str(error)}."
            )

    @guildinfo.error
    async def on_guild_info_eror(
        self, interaction: discord.Interaction, error: app_commands.errors
    ):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            return await interaction.response.send_message(
                "You do not have enough permissions to use this command.",
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
    await bot.add_cog(userinfo(bot))
