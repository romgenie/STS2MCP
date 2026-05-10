# MCP Tools

## Singleplayer

| Tool | Scope | Description |
|---|---|---|
| `get_game_state(format?, wait_for_actionable?, wait_timeout?, poll_interval?)` | General | Get current game state (`markdown` or `json`), optionally waiting through transient non-actionable states |
| `log_agent_decision(summary, reasoning?, intended_action?, alternatives?, confidence?, tags?)` | General | Add a structured decision annotation to the run log |
| `menu_select(option, seed?)` | General | Select a visible menu/game-over option |
| `get_profile()` | Profiles | Get active profile progress |
| `list_profiles()` | Profiles | List profile slots and active slot |
| `switch_profile(profile_id)` | Profiles | Switch to a profile slot through the game UI |
| `delete_profile(profile_id)` | Profiles | Delete an inactive profile slot |
| `use_potion(slot, target?)` | General | Use a potion (works in and out of combat) |
| `discard_potion(slot)` | General | Discard a potion to free up the slot |
| `proceed_to_map()` | General | Proceed from rewards/rest site/shop/treasure to the map |
| `combat_play_card(card_index, target?)` | Combat | Play a card from hand |
| `combat_end_turn()` | Combat | End the current turn |
| `combat_select_card(card_index)` | Combat Selection | Select a card from hand during exhaust/discard prompts |
| `combat_confirm_selection()` | Combat Selection | Confirm the in-combat card selection |
| `rewards_claim(reward_index)` | Rewards | Claim a reward from the post-combat screen |
| `rewards_pick_card(card_index)` | Rewards | Select a card from the card reward screen |
| `rewards_skip_card()` | Rewards | Skip the card reward |
| `map_choose_node(node_index)` | Map | Choose a map node to travel to |
| `rest_choose_option(option_index)` | Rest Site | Choose a rest site option (rest, smith, etc.) |
| `shop_purchase(item_index)` | Shop | Purchase an item from the shop |
| `event_choose_option(option_index)` | Event | Choose an event option (including Proceed) |
| `event_advance_dialogue()` | Event | Advance ancient event dialogue |
| `deck_select_card(card_index)` | Card Select | Pick/toggle a card in the selection screen |
| `deck_confirm_selection()` | Card Select | Confirm the current card selection |
| `deck_cancel_selection()` | Card Select | Cancel/skip card selection |
| `bundle_select(bundle_index)` | Bundle Select | Open a bundle preview |
| `bundle_confirm_selection()` | Bundle Select | Confirm the current bundle preview |
| `bundle_cancel_selection()` | Bundle Select | Cancel the current bundle preview |
| `relic_select(relic_index)` | Relic Select | Choose a relic from the selection screen |
| `relic_skip()` | Relic Select | Skip relic selection |
| `treasure_claim_relic(relic_index)` | Treasure | Claim a relic from the treasure chest |
| `crystal_sphere_set_tool(tool)` | Crystal Sphere | Switch the active divination tool |
| `crystal_sphere_click_cell(x, y)` | Crystal Sphere | Click a hidden cell in the grid |
| `crystal_sphere_proceed()` | Crystal Sphere | Continue after the minigame finishes |

## Multiplayer

All multiplayer tools are prefixed with `mp_`. They route through `/api/v1/multiplayer` and are only available during multiplayer (co-op) runs. The endpoints automatically guard against cross-mode calls.

| Tool | Scope | Description |
|---|---|---|
| `mp_get_game_state(format?, wait_for_actionable?, wait_timeout?, poll_interval?)` | General | Get multiplayer game state (all players, votes, bids), optionally waiting through transient non-actionable states |
| `mp_combat_play_card(card_index, target?)` | Combat | Play a card from the local player's hand |
| `mp_combat_end_turn()` | Combat | Submit end-turn vote (turn ends when all players submit) |
| `mp_combat_undo_end_turn()` | Combat | Retract end-turn vote |
| `mp_use_potion(slot, target?)` | General | Use a potion from the local player's slots |
| `mp_discard_potion(slot)` | General | Discard a potion from the local player's slots |
| `mp_proceed_to_map()` | General | Proceed from current screen to the map |
| `mp_map_vote(node_index)` | Map | Vote for a map node (travel when all agree) |
| `mp_event_choose_option(option_index)` | Event | Vote for / choose an event option |
| `mp_event_advance_dialogue()` | Event | Advance ancient event dialogue |
| `mp_rest_choose_option(option_index)` | Rest Site | Choose a rest site option (per-player, no vote) |
| `mp_shop_purchase(item_index)` | Shop | Purchase an item (per-player inventory) |
| `mp_rewards_claim(reward_index)` | Rewards | Claim a post-combat reward |
| `mp_rewards_pick_card(card_index)` | Rewards | Select a card from the card reward screen |
| `mp_rewards_skip_card()` | Rewards | Skip the card reward |
| `mp_deck_select_card(card_index)` | Card Select | Pick/toggle a card in the selection screen |
| `mp_deck_confirm_selection()` | Card Select | Confirm the current card selection |
| `mp_deck_cancel_selection()` | Card Select | Cancel/skip card selection |
| `mp_bundle_select(bundle_index)` | Bundle Select | Open a bundle preview |
| `mp_bundle_confirm_selection()` | Bundle Select | Confirm the current bundle preview |
| `mp_bundle_cancel_selection()` | Bundle Select | Cancel the current bundle preview |
| `mp_combat_select_card(card_index)` | Combat Selection | Select a card during in-combat selection prompts |
| `mp_combat_confirm_selection()` | Combat Selection | Confirm in-combat card selection |
| `mp_relic_select(relic_index)` | Relic Select | Choose a relic from the selection screen |
| `mp_relic_skip()` | Relic Select | Skip relic selection |
| `mp_treasure_claim_relic(relic_index)` | Treasure | Bid on a relic (relic fight if contested) |
| `mp_crystal_sphere_set_tool(tool)` | Crystal Sphere | Switch the active divination tool |
| `mp_crystal_sphere_click_cell(x, y)` | Crystal Sphere | Click a hidden cell in the grid |
| `mp_crystal_sphere_proceed()` | Crystal Sphere | Continue after the minigame finishes |

## Run Logging

The MCP bridge writes structured JSONL logs by default under `logs/run_<timestamp>-<id>.jsonl` relative to the server working directory. Each line has a stable envelope with `schema_version`, `run_id`, `sequence`, UTC `timestamp`, `monotonic_ms`, `event_type`, and when applicable `tool_call_id` / `tool_name`.

Logged events include:

- `session_start` with bridge configuration and runtime metadata.
- `tool_call_start`, `tool_call_result`, and `tool_call_error` for every MCP tool.
- `http_request`, `http_response`, and `http_error` for calls to the STS2_MCP REST API.
- `state_poll` and `state_poll_final_format` for smart polling decisions.
- `agent_decision` entries from `log_agent_decision`.

Tool and HTTP results include length, byte count, SHA-256, preview text, and truncation status. Keys containing `authorization`, `cookie`, `password`, `secret`, `token`, `api_key`, or `apikey` are redacted before writing.

Logging options:

```bash
python server.py --log-dir logs
python server.py --disable-run-log
python server.py --log-preview-chars 8000
python server.py --log-full-text
```

`STS2_MCP_LOG_DIR` can also set the default log directory. Use `--log-full-text` when you need complete replayable tool/API text for evaluation; otherwise previews plus hashes keep the log smaller while preserving integrity checks.

## Smart State Polling

`get_game_state` and `mp_get_game_state` default to `wait_for_actionable=true`. The bridge polls JSON state until one of these conditions is met, then returns the requested format:

- combat reaches the player's play phase;
- event dialogue/options are available;
- reward, rest, shop, treasure, or Crystal Sphere controls are actionable;
- another non-transient state is reached;
- `wait_timeout` expires.

Set `wait_for_actionable=false` to get the immediate raw state. `wait_timeout` is capped at 60 seconds and `poll_interval` is capped between 0.1 and 5 seconds.
