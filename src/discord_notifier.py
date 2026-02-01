"""
Discord notification module for Fantasy Basketball automation.

Sends rich embedded notifications to Discord channels via webhooks for update
summaries, error alerts, and other automated events.
"""

from discord_webhook import DiscordWebhook, DiscordEmbed
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Handles Discord webhook notifications for fantasy basketball updates."""

    def __init__(self, webhook_url: Optional[str] = None, enabled: bool = True):
        """
        Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL. If None, reads from DISCORD_WEBHOOK_URL env var.
            enabled: Whether notifications are enabled. If False, methods will no-op.
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.enabled = enabled and bool(self.webhook_url)

        if not self.enabled:
            logger.info("Discord notifications are disabled (no webhook URL or enabled=False)")

    def send_update_summary(
        self,
        teams_updated: int,
        total_teams: int,
        transactions_processed: int,
        spreadsheet_url: str,
        last_update_hours: float,
        verbose_transaction_log: Optional[str] = None
    ) -> bool:
        """
        Send update completion notification with rich embed.

        Args:
            teams_updated: Number of teams that had roster changes
            total_teams: Total number of teams in league
            transactions_processed: Number of transactions processed
            spreadsheet_url: URL to updated Google Spreadsheet
            last_update_hours: Hours since previous update
            verbose_transaction_log: Optional detailed transaction log

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Calculate percent updated
            update_percent = (teams_updated / total_teams * 100) if total_teams > 0 else 0

            # Create webhook
            webhook = DiscordWebhook(
                url=self.webhook_url,
                username="Fantasy Basketball Bot"
            )

            # Create rich embed
            embed = DiscordEmbed(
                title="📊 Fantasy Basketball Update Complete",
                description=f"Successfully updated league data at {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}",
                color="03b2f8"  # Blue
            )

            # Add fields
            embed.add_embed_field(
                name="✅ Teams Updated",
                value=f"**{teams_updated}** of {total_teams} ({update_percent:.0f}% updated)",
                inline=False
            )

            embed.add_embed_field(
                name="📈 Transactions Processed",
                value=f"**{transactions_processed}** transaction(s)",
                inline=True
            )

            embed.add_embed_field(
                name="⏱️ Last Update",
                value=f"{last_update_hours:.1f} hours ago",
                inline=True
            )

            # Add spreadsheet link
            embed.add_embed_field(
                name="🔗 View Spreadsheet",
                value=f"[Open in Google Sheets]({spreadsheet_url})",
                inline=False
            )

            # Add verbose transaction log if provided
            if verbose_transaction_log:
                # Truncate if too long (Discord field limit: 1024 chars)
                if len(verbose_transaction_log) > 1000:
                    verbose_transaction_log = verbose_transaction_log[:997] + "..."

                embed.add_embed_field(
                    name="📝 Recent Transactions",
                    value=f"```{verbose_transaction_log}```",
                    inline=False
                )

            # Add footer and timestamp
            embed.set_footer(text="Fantasy Basketball Automation • Powered by Yahoo API")
            embed.set_timestamp()

            # Send webhook
            webhook.add_embed(embed)
            response = webhook.execute()

            if response.status_code in [200, 204]:
                logger.info("Discord notification sent successfully")
                return True
            else:
                logger.warning(f"Discord notification failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def send_error_notification(
        self,
        error_message: str,
        error_type: str,
        stack_trace: Optional[str] = None,
        role_id: Optional[str] = None
    ) -> bool:
        """
        Send error alert notification.

        Args:
            error_message: Human-readable error description
            error_type: Type/category of error (e.g., "Yahoo API Error")
            stack_trace: Optional stack trace for debugging
            role_id: Optional Discord role ID to mention (format: "123456789")

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Create webhook
            webhook = DiscordWebhook(
                url=self.webhook_url,
                username="Fantasy Basketball Bot"
            )

            # Add role mention if provided
            if role_id:
                webhook.set_content(f"<@&{role_id}> 🚨 **Fantasy Basketball Update Failed**")
            else:
                webhook.set_content("🚨 **Fantasy Basketball Update Failed**")

            # Create error embed
            embed = DiscordEmbed(
                title="Error During Automated Update",
                description=error_message,
                color="ff0000"  # Red
            )

            embed.add_embed_field(
                name="Error Type",
                value=error_type,
                inline=False
            )

            embed.add_embed_field(
                name="Timestamp",
                value=datetime.now().strftime('%B %d, %Y at %I:%M:%S %p UTC'),
                inline=False
            )

            # Add stack trace if provided (truncate if too long)
            if stack_trace:
                if len(stack_trace) > 1000:
                    stack_trace = stack_trace[:997] + "..."
                embed.add_embed_field(
                    name="Stack Trace",
                    value=f"```{stack_trace}```",
                    inline=False
                )

            embed.add_embed_field(
                name="📋 Action Required",
                value="Check GitHub Actions logs for full error details",
                inline=False
            )

            embed.set_footer(text="Check logs for full error details")
            embed.set_timestamp()

            # Send webhook
            webhook.add_embed(embed)
            response = webhook.execute()

            if response.status_code in [200, 204]:
                logger.info("Discord error notification sent successfully")
                return True
            else:
                logger.warning(f"Discord error notification failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Discord error notification: {e}")
            return False

    def send_bench_alert(
        self,
        bench_teams: list,
        il_violations: Dict[str, List[Dict[str, str]]],
        spreadsheet_url: str,
        check_date: str
    ) -> bool:
        """
        Send bench management alert via Discord webhook.

        Shows both bench violations (healthy players on bench with games)
        and IL violations (healthy players in IL/IL+ slots) in a single alert.

        Args:
            bench_teams: List of team names with bench violations
            il_violations: Dict mapping team names to IL violation details (includes player names)
            spreadsheet_url: URL to the league spreadsheet
            check_date: Date string for the violations (YYYY-MM-DD)

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        # Count total violations
        total_violations = len(bench_teams) + len(il_violations)

        if total_violations == 0:
            logger.info("No bench or IL violations to report")
            return False

        try:
            # Create webhook
            webhook = DiscordWebhook(
                url=self.webhook_url,
                username="Fantasy Basketball Bot"
            )

            # Build title
            title = "⚠️ Roster Management Alert"

            # Build description
            description_parts = []
            if bench_teams:
                description_parts.append(
                    f"**{len(bench_teams)} team(s) with bench violations**\n"
                    "Healthy players on bench who have games today"
                )
            if il_violations:
                description_parts.append(
                    f"**{len(il_violations)} team(s) with IL violations**\n"
                    "Healthy players in IL/IL+ slots"
                )

            description = "\n\n".join(description_parts)

            # Build team lists
            bench_list = "\n".join(f"• {team}" for team in bench_teams) if bench_teams else "None"

            # Build IL list with player details
            if il_violations:
                il_list_parts = []
                for team_name, team_violations in il_violations.items():
                    il_list_parts.append(f"• **{team_name}**")
                    for player in team_violations:
                        player_info = f"  • {player['player_name']} ({player['nba_team']} - {player['position']}) [{player['roster_slot']}]"
                        il_list_parts.append(player_info)
                il_list = "\n".join(il_list_parts)
            else:
                il_list = "None"

            # Create embed
            embed = DiscordEmbed(
                title=title,
                description=description,
                color="ffa500"  # Orange
            )

            embed.add_embed_field(
                name="🏀 Bench Violations",
                value=bench_list,
                inline=False
            )

            embed.add_embed_field(
                name="🏥 IL/IL+ Violations",
                value=il_list,
                inline=False
            )

            if spreadsheet_url:
                embed.add_embed_field(
                    name="📊 View Rosters",
                    value=f"[Open Spreadsheet]({spreadsheet_url})",
                    inline=False
                )

            embed.add_embed_field(
                name="💡 Tip",
                value=(
                    "**Bench**: Move healthy benched players to active roster\n"
                    "**IL**: Activate healthy players from IL/IL+ slots"
                ),
                inline=False
            )

            # Add footer and timestamp
            embed.set_footer(text=f"Check date: {check_date}")
            embed.set_timestamp()

            # Send webhook
            webhook.add_embed(embed)
            response = webhook.execute()

            if response.status_code in [200, 204]:
                logger.info(f"Roster management alert sent successfully ({total_violations} teams)")
                return True
            else:
                logger.warning(f"Roster management alert failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send roster management alert: {e}")
            return False


# Utility functions for easy integration
def notify_update_complete(
    teams_updated: int,
    total_teams: int,
    transactions_processed: int,
    spreadsheet_url: str,
    last_update_hours: float,
    verbose_transaction_log: Optional[str] = None
) -> None:
    """
    Convenience function to send update notification.

    Automatically reads webhook URL from environment and sends notification.
    Safe to call even if Discord integration is not configured (will no-op).

    Args:
        teams_updated: Number of teams that had roster changes
        total_teams: Total number of teams in league
        transactions_processed: Number of transactions processed
        spreadsheet_url: URL to updated Google Spreadsheet
        last_update_hours: Hours since previous update
        verbose_transaction_log: Optional detailed transaction log
    """
    notifier = DiscordNotifier()
    notifier.send_update_summary(
        teams_updated=teams_updated,
        total_teams=total_teams,
        transactions_processed=transactions_processed,
        spreadsheet_url=spreadsheet_url,
        last_update_hours=last_update_hours,
        verbose_transaction_log=verbose_transaction_log
    )


def notify_error(
    error_message: str,
    error_type: str = "Unknown Error",
    stack_trace: Optional[str] = None
) -> None:
    """
    Convenience function to send error notification.

    Automatically reads webhook URL and role ID from environment.
    Safe to call even if Discord integration is not configured (will no-op).

    Args:
        error_message: Human-readable error description
        error_type: Type/category of error
        stack_trace: Optional stack trace for debugging
    """
    notifier = DiscordNotifier()
    role_id = os.getenv("DISCORD_ALERT_ROLE_ID")
    notifier.send_error_notification(
        error_message=error_message,
        error_type=error_type,
        stack_trace=stack_trace,
        role_id=role_id
    )


def notify_bench_violations(
    bench_violations: Dict[str, List[Dict[str, str]]],
    il_violations: Dict[str, List[Dict[str, str]]],
    spreadsheet_url: str = "",
    check_date: str = ""
) -> bool:
    """
    Convenience function to send bench and IL violation notifications.

    Args:
        bench_violations: Dict mapping team names to bench violation details
        il_violations: Dict mapping team names to IL violation details
        spreadsheet_url: Optional URL to the league spreadsheet
        check_date: Optional date string for the violations

    Returns:
        True if notification sent, False if Discord disabled or no violations
    """
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '').strip()

    if not webhook_url:
        logger.info("Discord notifications disabled (no webhook URL)")
        return False

    # Convert bench violations to team list
    from src.bench_analyzer import get_teams_with_bench_violations
    bench_teams = get_teams_with_bench_violations(bench_violations)

    # Send combined alert (pass full IL violations dict for player details)
    notifier = DiscordNotifier(webhook_url)
    return notifier.send_bench_alert(
        bench_teams=bench_teams,
        il_violations=il_violations,
        spreadsheet_url=spreadsheet_url,
        check_date=check_date
    )
