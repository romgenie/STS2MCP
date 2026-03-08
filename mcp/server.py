"""MCP server bridge for Slay the Spire 2.

Connects to the STS2_MCP mod's HTTP server and exposes game actions
as MCP tools for Claude Desktop / Claude Code.
"""

import argparse
import json
import sys

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sts2")

_base_url: str = "http://localhost:15526"


def _api_url() -> str:
    return f"{_base_url}/api/v1/singleplayer"


async def _get(params: dict | None = None) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(_api_url(), params=params)
        r.raise_for_status()
        return r.text


async def _post(body: dict) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(_api_url(), json=body)
        r.raise_for_status()
        return r.text


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_game_state(format: str = "markdown") -> str:
    """Get the current Slay the Spire 2 game state.

    Returns the full game state including player stats, hand, enemies, potions, etc.
    The state_type field indicates the current screen (combat, map, event, shop, etc.).

    Args:
        format: "markdown" for human-readable output, "json" for structured data.
    """
    try:
        return await _get({"format": format})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def use_potion(slot: int, target: str | None = None) -> str:
    """Use a potion from the player's potion slots.

    Works both during and outside of combat. Combat-only potions require an active battle.

    Args:
        slot: Potion slot index (as shown in game state).
        target: Entity ID of the target enemy (e.g. "jaw_worm_0"). Required for enemy-targeted potions.
    """
    body: dict = {"action": "use_potion", "slot": slot}
    if target is not None:
        body["target"] = target
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def proceed_to_map() -> str:
    """Proceed from the current screen to the map.

    Works from: rewards screen, rest site, shop.
    Does NOT work for events — use event_choose_option() with the Proceed option's index.
    """
    try:
        return await _post({"action": "proceed"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Combat (state_type: monster / elite / boss)
# ---------------------------------------------------------------------------


@mcp.tool()
async def combat_play_card(card_index: int, target: str | None = None) -> str:
    """[Combat] Play a card from the player's hand.

    Args:
        card_index: Index of the card in hand (0-based, as shown in game state).
        target: Entity ID of the target enemy (e.g. "jaw_worm_0"). Required for single-target cards.

    Note that the index can change as cards are played - playing a card will shift the indices of remaining cards in hand.
    Refer to the latest game state for accurate indices. New cards are drawn to the right, so playing cards from right to left can help maintain more stable indices for remaining cards.
    """
    body: dict = {"action": "play_card", "card_index": card_index}
    if target is not None:
        body["target"] = target
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def combat_end_turn() -> str:
    """[Combat] End the player's current turn."""
    try:
        return await _post({"action": "end_turn"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# In-Combat Card Selection (state_type: hand_select)
# ---------------------------------------------------------------------------


@mcp.tool()
async def combat_select_card(card_index: int) -> str:
    """[Combat Selection] Select a card from hand during an in-combat card selection prompt.

    Used when a card effect asks you to select a card to exhaust, discard, etc.
    This is different from deck_select_card which handles out-of-combat card selection overlays.

    Args:
        card_index: 0-based index of the card in the selectable hand cards (as shown in game state).
    """
    body: dict = {"action": "combat_select_card", "card_index": card_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def combat_confirm_selection() -> str:
    """[Combat Selection] Confirm the in-combat card selection.

    After selecting the required number of cards from hand (exhaust, discard, etc.),
    use this to confirm the selection. Only works when the confirm button is enabled.
    """
    try:
        return await _post({"action": "combat_confirm_selection"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Rewards (state_type: combat_rewards / card_reward)
# ---------------------------------------------------------------------------


@mcp.tool()
async def rewards_claim(reward_index: int) -> str:
    """[Rewards] Claim a reward from the post-combat rewards screen.

    Gold, potion, and relic rewards are claimed immediately.
    Card rewards open the card selection screen (state changes to card_reward).

    Args:
        reward_index: 0-based index of the reward on the rewards screen.

    Note that claiming a reward may change the indices of remaining rewards, so refer to the latest game state for accurate indices.
    Claiming from right to left can help maintain more stable indices for remaining rewards, as rewards will always shift left to fill in gaps.
    """
    body: dict = {"action": "claim_reward", "index": reward_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def rewards_pick_card(card_index: int) -> str:
    """[Rewards] Select a card from the card reward selection screen.

    Args:
        card_index: 0-based index of the card to add to the deck.
    """
    body: dict = {"action": "select_card_reward", "card_index": card_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def rewards_skip_card() -> str:
    """[Rewards] Skip the card reward without selecting a card."""
    try:
        return await _post({"action": "skip_card_reward"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Map (state_type: map)
# ---------------------------------------------------------------------------


@mcp.tool()
async def map_choose_node(node_index: int) -> str:
    """[Map] Choose a map node to travel to.

    Args:
        node_index: 0-based index of the node from the next_options list.
    """
    body: dict = {"action": "choose_map_node", "index": node_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Rest Site (state_type: rest_site)
# ---------------------------------------------------------------------------


@mcp.tool()
async def rest_choose_option(option_index: int) -> str:
    """[Rest Site] Choose a rest site option (rest, smith, etc.).

    Args:
        option_index: 0-based index of the option from the rest site state.
    """
    body: dict = {"action": "choose_rest_option", "index": option_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Shop (state_type: shop)
# ---------------------------------------------------------------------------


@mcp.tool()
async def shop_purchase(item_index: int) -> str:
    """[Shop] Purchase an item from the shop.

    Args:
        item_index: 0-based index of the item from the shop state.
    """
    body: dict = {"action": "shop_purchase", "index": item_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Event (state_type: event)
# ---------------------------------------------------------------------------


@mcp.tool()
async def event_choose_option(option_index: int) -> str:
    """[Event] Choose an event option.

    Works for both regular events and ancients (after dialogue ends).
    Also used to click the Proceed option after an event resolves.

    Args:
        option_index: 0-based index of the unlocked option.
    """
    body: dict = {"action": "choose_event_option", "index": option_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def event_advance_dialogue() -> str:
    """[Event] Advance ancient event dialogue.

    Click through dialogue text in ancient events. Call repeatedly until options appear.
    """
    try:
        return await _post({"action": "advance_dialogue"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Card Selection (state_type: card_select)
# ---------------------------------------------------------------------------


@mcp.tool()
async def deck_select_card(card_index: int) -> str:
    """[Card Selection] Select or deselect a card in the card selection screen.

    Used when the game asks you to choose cards from your deck (transform, upgrade,
    remove, discard) or pick a card from offered choices (potions, effects).

    For deck selections: toggles card selection. For choose-a-card: picks immediately.

    Args:
        card_index: 0-based index of the card (as shown in game state).
    """
    body: dict = {"action": "select_card", "index": card_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def deck_confirm_selection() -> str:
    """[Card Selection] Confirm the current card selection.

    After selecting the required number of cards, use this to confirm.
    If a preview is showing (e.g., transform preview), this confirms the preview.
    Not needed for choose-a-card screens where picking is immediate.
    """
    try:
        return await _post({"action": "confirm_selection"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def deck_cancel_selection() -> str:
    """[Card Selection] Cancel the current card selection.

    If a preview is showing, goes back to the selection grid.
    For choose-a-card screens, clicks the skip button (if available).
    Otherwise, closes the card selection screen (only if cancellation is allowed).
    """
    try:
        return await _post({"action": "cancel_selection"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Relic Selection (state_type: relic_select)
# ---------------------------------------------------------------------------


@mcp.tool()
async def relic_select(relic_index: int) -> str:
    """[Relic Selection] Select a relic from the relic selection screen.

    Used when the game offers a choice of relics (e.g., boss relic rewards).

    Args:
        relic_index: 0-based index of the relic (as shown in game state).
    """
    body: dict = {"action": "select_relic", "index": relic_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def relic_skip() -> str:
    """[Relic Selection] Skip the relic selection without choosing a relic."""
    try:
        return await _post({"action": "skip_relic_selection"})
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Treasure (state_type: treasure)
# ---------------------------------------------------------------------------


@mcp.tool()
async def treasure_claim_relic(relic_index: int) -> str:
    """[Treasure] Claim a relic from the treasure chest.

    The chest is auto-opened when entering the treasure room.
    After claiming, use proceed_to_map() to continue.

    Args:
        relic_index: 0-based index of the relic (as shown in game state).
    """
    body: dict = {"action": "claim_treasure_relic", "index": relic_index}
    try:
        return await _post(body)
    except httpx.ConnectError:
        return "Error: Cannot connect to STS2_MCP mod. Is the game running with the mod enabled?"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(description="STS2 MCP Server")
    parser.add_argument("--port", type=int, default=15526, help="Game HTTP server port")
    parser.add_argument("--host", type=str, default="localhost", help="Game HTTP server host")
    args = parser.parse_args()

    global _base_url
    _base_url = f"http://{args.host}:{args.port}"

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
