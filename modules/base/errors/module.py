import re
import traceback
from typing import Tuple

import discord
from discord.ext import commands

import core.exceptions
from core import text, logging, utils


tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()


class Errors(commands.Cog):
    """Error handling module."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_error(event, *args, **kwargs):
        tb = traceback.format_exc()
        await bot_log.error(None, None, traceback=tb)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """Handle bot exceptions."""
        # Recursion prevention
        if hasattr(ctx.command, "on_error") or hasattr(ctx.command, "on_command_error"):
            return

        # Get original exception
        while True:
            new_error = getattr(error, "original", error)
            if new_error == error:
                break
            error = new_error

        # Prevent some exceptions from being reported
        if type(error) == commands.CommandNotFound:
            return

        # Get information
        title, content, show_traceback, inform = Errors.__get_error_message(ctx, error)
        embed = utils.Discord.create_embed(
            author=ctx.author, error=True, title=title, description=content
        )

        tb: str = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        if show_traceback:
            embed.add_field(
                name="Traceback", value="```" + tb[-256:] + "```", inline=False
            )
        await ctx.send(embed=embed)

        # Send to error logging channel
        if inform:
            # TODO Complete when we know what channel we have to send the content to
            pass

        # Log the error
        if show_traceback or inform:
            await guild_log.error(
                ctx.author,
                ctx.channel,
                f"{type(error).__name__}: {str(error)}",
                traceback=traceback.format_tb(error.__traceback__),
            )

    def __get_error_message(
        ctx: commands.Context, error: Exception
    ) -> Tuple[str, str, bool, bool]:
        """Get message for the error.

        :param ctx: The invocation context.
        :param error: Detected exception.
        :return:
            title (The error name),
            content (The error description),
            show_traceback (Whether to display traceback),
            inform (Whether to send the error for further inspection).
        """

        # pumpkin.py own exceptions
        if isinstance(error, core.exceptions.PumpkinException):
            return (
                tr("pumpkin.py", type(error).__name__, ctx),
                str(error),
                False,
                True,
            )

        # interactions
        if type(error) == commands.MissingRequiredArgument:
            return (
                tr("MissingRequiredArgument", "name", ctx),
                tr("MissingRequiredArgument", "value", ctx, arg=error.param.name),
                False,
                False,
            )
        if type(error) == commands.CommandOnCooldown:
            time = utils.Time.seconds(error.retry_after)
            return (
                tr("CommandOnCooldown", "name", ctx),
                tr("CommandOnCooldown", "value", ctx, time=time),
                False,
                False,
            )
        if type(error) == commands.MaxConcurrencyReached:
            return (
                tr("MaxConcurrencyReached", "name", ctx),
                tr(
                    "MaxConcurrencyReached",
                    "value",
                    ctx,
                    num=error.number,
                    per=error.per.name,
                ),
                False,
                False,
            )
        if type(error) == commands.MissingRole:
            return (
                tr("MissingRole", "name", ctx),
                tr("MissingRole", "value", ctx, role=f"`{error.missing_role!r}`"),
                False,
                False,
            )
        if type(error) == commands.BotMissingRole:
            return (
                tr("BotMissingRole", "name", ctx),
                tr("BotMissingRole", "value", ctx, role=f"`{error.missing_role!r}`"),
                False,
                False,
            )
        if type(error) == commands.MissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                tr("MissingAnyRole", "name", ctx),
                tr("MissingAnyRole", "value", ctx, roles=roles),
                False,
                False,
            )
        if type(error) == commands.BotMissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                tr("BotMissingAnyRole", "name", ctx),
                tr("BotMissingAnyRole", "value", ctx, roles=roles),
                False,
                False,
            )
        if type(error) == commands.MissingPermissions:
            perms = ", ".join(f"**{p}**" for p in error.missing_perms)
            return (
                tr("MissingPermissions", "name", ctx),
                tr("MissingPermissions", "value", ctx, perms=perms),
                False,
                False,
            )
        if type(error) == commands.BotMissingPermissions:
            perms = ", ".join(f"`{p}`" for p in error.missing_perms)
            return (
                tr("BotMissingPermissions", "name", ctx),
                tr("BotMissingPermissions", "value", ctx, perms=perms),
                False,
                False,
            )
        if type(error) == commands.BadUnionArgument:
            return (
                tr("BadUnionArgument", "name", ctx),
                tr("BadUnionArgument", "value", ctx, param=error.param.name),
                False,
                False,
            )
        if type(error) == commands.BadBoolArgument:
            return (
                tr("BadBoolArgument", "name", ctx),
                tr("BadBoolArgument", "value", ctx, arg=error.argument),
                False,
                False,
            )
        if type(error) == commands.ConversionError:
            return (
                tr("ConversionError", "name", ctx),
                tr(
                    "ConversionError",
                    "value",
                    ctx,
                    converter=type(error.converter).__name__,
                ),
                False,
                False,
            )

        # extensions
        if type(error) == commands.ExtensionFailed:
            # return friendly name, e.g. strip "modules.{module}.module"
            name = error.name[8:-7]
            return (
                tr("ExtensionFailed", "name", ctx),
                tr("ExtensionFailed", "value", ctx, extension=name),
                True,
                True,
            )
        if isinstance(error, commands.ExtensionError):
            # return friendly name, e.g. strip "modules.{module}.module"
            name = error.name[8:-7]
            # send helpful message if the requested module does not follow naming rules
            if re.fullmatch(r"([a-z_]+)\.([a-z_]+)", name) is None:
                key = "ExtensionNotFound_hint"
            else:
                key = type(error).__name__
            return (
                tr(key, "name", ctx),
                tr(key, "value", ctx, extension=name),
                False,
                False,
            )

        # the rest of client exceptions
        if type(error) == commands.CommandRegistrationError:
            return (
                tr("CommandRegistrationError", "name", ctx),
                tr("CommandRegistrationError", "value", ctx, cmd=error.name),
                False,
                False,
            )
        if isinstance(error, commands.CommandError) or isinstance(
            error, discord.ClientException
        ):
            return (
                tr(type(error).__name__, "name", ctx),
                tr(type(error).__name__, "value", ctx),
                False,
                True,
            )

        # non-critical discord.py exceptions
        if type(error) == discord.NoMoreItems or isinstance(
            error, discord.HTTPException
        ):
            return (
                tr(type(error).__name__, "name", ctx),
                tr(type(error).__name__, "value", ctx),
                False,
                True,
            )

        # critical discord.py exceptions
        if isinstance(error, discord.DiscordException):
            return (
                tr(type(error).__name__, "name", ctx),
                tr(type(error).__name__, "value", ctx),
                True,
                True,
            )

        # other exceptions
        return (
            type(error).__name__,
            tr("Unknown", "value", ctx),
            True,
            True,
        )


def setup(bot) -> None:
    bot.add_cog(Errors(bot))
