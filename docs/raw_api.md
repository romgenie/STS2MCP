# Raw API Reference

These API endpoints are available for direct HTTP requests *without* using the MCP server. For example, you can use `curl` or Postman to interact with the mod directly at `http://localhost:15526/api/v1/singleplayer`. 

:::note
These endpoints are designed for local use and do not have authentication or security measures, so they should not be exposed publicly - unless you know what you're doing!
:::

## `GET /api/v1/singleplayer`

Query parameters:
| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `format`  | `json`, `markdown` | `json` | Response format |

Returns the current game state. The `state_type` field indicates the screen:
- `monster` / `elite` / `boss` — In combat (full battle state returned)
- `combat_rewards` — Post-combat rewards screen (reward items, proceed button)
- `card_reward` — Card reward selection screen (card choices, skip option)
- `map` — Map navigation screen (full DAG, next options with lookahead, visited path)
- `rest_site` — Rest site (available options: rest, smith, etc.)
- `shop` — Shop (full inventory: cards, relics, potions, card removal with costs)
- `event` — Event or Ancient (options with descriptions, ancient dialogue detection)
- `card_select` — Deck card selection (transform, upgrade, remove, discard)
- `treasure` — Treasure room (stub for now)
- `menu` — No run in progress

**Battle state includes:**
- Player: HP, block, energy, stars (Regent), gold, character, powers, relics, potions, hand (with card details including star costs), pile counts, orbs
- Enemies: entity_id, name, HP, block, powers, intents with labels

**Rewards state includes:**
- Player summary: character, HP, gold, potion slot availability
- Reward items: index, type (`gold`, `potion`, `relic`, `card`, `special_card`, `card_removal`), description, and type-specific details (gold amount, potion id/name)
- Proceed button state

**Event state includes:**
- Event metadata: id, name, whether it's an Ancient, dialogue phase status
- Player summary: character, HP, gold
- Options: index, title, description, locked/proceed/chosen status, attached relic (for Ancients)

**Rest site state includes:**
- Player summary: character, HP, gold
- Available options: index, id, name, description, enabled status
- Proceed button state

**Shop state includes:**
- Player summary: character, HP, gold, potion slot availability
- Full inventory by category: cards (with details, cost, on_sale), relics, potions, card removal
- Each item: index, cost, stocked status, affordability

**Map state includes:**
- Player summary: character, HP, gold, potion slot availability
- Current position and visited path
- Next options: index, coordinate, node type, with 1-level lookahead (children types)
- Full map DAG: all nodes with coordinates, types, and edges (children)

**Card select state includes:**
- Screen type: `transform`, `upgrade`, `select`, `simple_select`
- Player summary: character, HP, gold
- Prompt text (e.g., "Choose 2 cards to Transform.")
- Cards: index, id, name, type, cost, description, rarity, upgrade status, keywords
- Preview state, confirm/cancel button availability

**Card reward state includes:**
- Card choices: index, id, name, type, energy cost, star cost (Regent), description, rarity, upgrade status, keywords
- Skip availability

### `POST /api/v1/singleplayer`

**Play a card:**
```json
{
  "action": "play_card",
  "card_index": 0,
  "target": "jaw_worm_0"
}
```
- `card_index`: 0-based index in hand (from GET response)
- `target`: entity_id of the target (required for `AnyEnemy` cards, omit for self-targeting/AoE cards)

**Use a potion:**
```json
{
  "action": "use_potion",
  "slot": 0,
  "target": "jaw_worm_0"
}
```
- `slot`: potion slot index (from GET response)
- `target`: entity_id of the target (required for `AnyEnemy` potions, omit otherwise)

**End turn:**
```json
{ "action": "end_turn" }
```

**Claim a reward:**
```json
{ "action": "claim_reward", "index": 0 }
```
- `index`: 0-based index of the reward on the rewards screen (from GET response)
- Gold, potion, and relic rewards are claimed immediately
- Card rewards open the card selection screen (state changes to `card_reward`)

**Select a card reward:**
```json
{ "action": "select_card_reward", "card_index": 1 }
```
- `card_index`: 0-based index of the card to add to the deck (from GET response)

**Skip card reward:**
```json
{ "action": "skip_card_reward" }
```

**Proceed from rewards:**
```json
{ "action": "proceed" }
```
- Proceeds from the rewards screen to the map
- Any unclaimed rewards are skipped

**Choose a rest site option:**
```json
{ "action": "choose_rest_option", "index": 0 }
```
- `index`: 0-based index of the enabled option (from GET response)
- Options include Rest (heal), Smith (upgrade a card), and relic-granted options

**Purchase a shop item:**
```json
{ "action": "shop_purchase", "index": 0 }
```
- `index`: 0-based index of the item in the shop inventory (from GET response)
- Item must be stocked and affordable

**Choose an event option:**
```json
{ "action": "choose_event_option", "index": 0 }
```
- `index`: 0-based index of the unlocked option (from GET response)
- Works for both regular events and ancients (after dialogue)

**Advance ancient dialogue:**
```json
{ "action": "advance_dialogue" }
```
- Clicks through dialogue text in ancient events
- Call repeatedly until `in_dialogue` becomes `false` and options appear

**Choose a map node:**
```json
{ "action": "choose_map_node", "index": 0 }
```
- `index`: 0-based index from the `next_options` array in the map state
- Node types: Monster, Elite, Boss, RestSite, Shop, Treasure, Unknown, Ancient

**Select a card in the deck selection grid:**
```json
{ "action": "select_card", "index": 0 }
```
- `index`: 0-based index of the card in the grid (from GET response)
- Toggles selection — call again to deselect
- When enough cards are selected, a preview may appear automatically

**Confirm card selection:**
```json
{ "action": "confirm_selection" }
```
- Confirms the current selection (from preview or main confirm button)

**Cancel card selection:**
```json
{ "action": "cancel_selection" }
```
- If preview is showing, goes back to the selection grid
- Otherwise, closes the card selection screen (only if cancellation is allowed)

### Error responses

All errors return:
```json
{
  "status": "error",
  "error": "Description of what went wrong"
}
```

