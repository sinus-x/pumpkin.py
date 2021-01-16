import traceback
from typing import Tuple

import discord
from discord.ext import commands

from core import text, utils

tr = text.Translator(__file__).translate


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # FIXME What is this doing?
        if hasattr(ctx.command, "on_error") or hasattr(ctx.command, "on_command_error"):
            return

        # Get original error, if exists
        error = getattr(error, "original", error)

        # Prevent some exceptions from being reported
        if type(error) == commands.CommandNotFound:
            return

        # Get information
        title, content, do_traceback, inform = self._get_error_message(ctx, error)
        embed = utils.Discord.create_embed(
            author=ctx.author, error=True, title=title, description=content
        )
        tb = None
        if do_traceback or inform:
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            embed.add_field(name="Traceback", value="```" + tb[-256:] + "```", inline=False)

        await ctx.send(embed=embed)

        if inform:
            # TODO Send to error channel
            pass

    def _get_error_message(
        self, ctx: commands.Context, error: Exception
    ) -> Tuple[str, str, bool, bool]:
        """Get message for the error.

        Returns
        -------
        title: The error name
        content: The error description
        traceback: Whether to display traceback.
        inform: Whether to send the error for further inspection
        """

        # interactions
        if type(error) == commands.MissingRequiredArgument:
            return (
                tr("MissingRequiredArgument", "name"),
                tr("MissingRequiredArgument", "value", arg=error.param.name),
                False,
                False,
            )
        if type(error) == commands.CommandOnCooldown:
            time = utils.Time.seconds(error.retry_after)
            return (
                tr("CommandOnCooldown", "name"),
                tr("CommandOnCooldown", "value", time=time),
                False,
                False,
            )
        if type(error) == commands.MaxConcurrencyReached:
            return (
                tr("MaxConcurrencyReached", "name"),
                tr("MaxConcurrencyReached", "value", num=error.number, per=error.per.name),
                False,
                False,
            )
        if type(error) == commands.MissingRole:
            return (
                tr("MissingRole", "name"),
                tr("MissingRole", "value", role=f"`{error.missing_role!r}`"),
                False,
                False,
            )
        if type(error) == commands.BotMissingRole:
            return (
                tr("BotMissingRole", "name"),
                tr("BotMissingRole", "value", role=f"`{error.missing_role!r}`"),
                False,
                False,
            )
        if type(error) == commands.MissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                tr("MissingAnyRole", "name"),
                tr("MissingAnyRole", "value", roles=roles),
                False,
                False,
            )
        if type(error) == commands.BotMissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                tr("BotMissingAnyRole", "name"),
                tr("BotMissingAnyRole", "value", roles=roles),
                False,
                False,
            )
        if type(error) == commands.MissingPermissions:
            perms = ", ".join(f"**{p}**" for p in error.missing_perms)
            return (
                tr("MissingPermissions", "name"),
                tr("MissingPermissions", "value", perms=perms),
                False,
                False,
            )
        if type(error) == commands.BotMissingPermissions:
            perms = ", ".join(f"`{p}`" for p in error.missing_perms)
            return (
                tr("BotMissingPermissions", "name"),
                tr("BotMissingPermissions", "value", perms=perms),
                False,
            )
        if type(error) == commands.BadUnionArgument:
            return (
                tr("BadUnionArgument", "name"),
                tr("BadUnionArgument", "value", param=error.param.name),
                False,
                False,
            )
        if type(error) == commands.BadBoolArgument:
            return (
                tr("BadBoolArgument", "name"),
                tr("BadBoolArgument", "value", arg=error.argument),
                False,
                False,
            )
        if type(error) == commands.ConversionError:
            return (
                tr("ConversionError", "name"),
                tr("ConversionError", "value", converter=type(error.converter).__name__),
                False,
                False,
            )

        # extensions
        if type(error) == commands.ExtensionFailed:
            return (
                tr("ExtensionFailed", "name"),
                tr("ExtensionFailed", "value", extension=f"{error.name!r}"),
                True,
                True,
            )
        if isinstance(error, commands.ExtensionError):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value", extension=f"{error.name!r}"),
                False,
                False,
            )

        # the rest of client exceptions
        if type(error) == commands.CommandRegistrationError:
            return (
                tr("CommandRegistrationError", "name"),
                tr("CommandRegistrationError", "value", command=error.name),
                False,
                False,
            )
        if isinstance(error, commands.CommandError) or isinstance(error, discord.ClientException):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value"),
                False,
                False,
            )

        # non-critical discord.py exceptions
        if type(error) == discord.NoMoreItems or isinstance(error, discord.HTTPException):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value"),
                False,
                True,
            )

        # critical discord.py exceptions
        if isinstance(error, discord.DiscordException):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value"),
                True,
                True,
            )

        # other exceptions
        return (
            type(error).__name__,
            tr("Unknown", "value"),
            True,
            True,
        )


def setup(bot) -> None:
    bot.add_cog(Errors(bot))
