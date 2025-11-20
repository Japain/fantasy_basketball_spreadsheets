"""
Discord notification module for Fantasy Basketball automation.

Sends rich embedded notifications to Discord channels via webhooks for update
summaries, error alerts, and other automated events.
"""

from discord_webhook import DiscordWebhook, DiscordEmbed
import os
import logging
from datetime import datetime
from typing import Optional

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
