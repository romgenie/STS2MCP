# Slay The Spire 2 - MCP Server

> [!warning]
> This mod allows external programs to read the game's state and control the gameplay via a localhost API.
>
> Ill-intentioned software can abuse the API to ruin your runs, and those software likely require no special permissions to run.
>
> Additionally, even the best AI agents make the gravest mistakes sometimes.
>
> Use the mod at your own risk, and only with runs you care less about.

A mod for [**Slay the Spire 2**](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) that exposes the game state and allows external control via REST endpoints, plus an optional Python MCP server for native AI agent integration.

Default port is `15526`.

Tested against STS2 `v0.98.2`

## Roadmap

- [ ] Singleplayer
  - [x] Full battle state with keyword glossary
  - [x] Battle actions (play cards, use potions, end turn)
  - [x] Post-combat reward screen (claim rewards, card selection, skip, proceed)
  - [x] Map navigation (full DAG state, path selection)
  - [x] Rest site actions (resting, smithing, other options)
  - [x] Shop (browse inventory, purchase cards/relics/potions, card removal, auto-open)
  - [x] Events (choices, dialogue) and Ancients (dialogue advancement, relic options)
  - [x] Card selection overlays (transform, upgrade, remove, choose-a-card from potions/effects)
  - [x] In-combat card selection (exhaust, discard, upgrade prompts from card effects)
  - [x] Relic selection (boss relics, skip)
  - [x] Treasure rooms (auto-open chest, claim relics)
  - [x] Keyword system across all entities (cards, relics, potions, powers, events, shop)
  - [x] Catch-all overlay detection (prevents soft-locks on unhandled screens)
  - [ ] Quality assurance and edge case handling
- [ ] Multiplayer
  - [ ] Authentication for multiplayer sessions
- [ ] Additional API endpoints (e.g., run history, seed info)

## Requirements

**To run the mod, you need:**

- Slay the Spire 2 (Steam)

**To run both the mod and the MCP server, you will additionally need:**

- Python 3.11+ and [uv](https://docs.astral.sh/uv/) (for the MCP server)

**To build the mod, you need:**:

- [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0) (for building the mod)
- [PckPacker](https://docs.godotengine.org/en/stable/classes/class_pckpacker.html)

## Installation

Copy `STS2_MCP.dll` and `STS2_MCP.pck` to `<game_install>/mods/`.

Enable the mod in the game settings (a consent dialog will appear on first launch with mods present).

## Building the Mod

From the project root:

```bash
./build.sh
```

Or manually:

```bash
dotnet build STS2_MCP/STS2_MCP.csproj -c Release -o out/STS2_MCP
dotnet run --project tools/PckPacker/PckPacker.csproj -- out/STS2_MCP/STS2_MCP.pck "" STS2_MCP/mod_manifest.json
cp out/STS2_MCP/STS2_MCP.{dll,pck} "<game_install>/mods/"
```

## MCP Server Setup

The Python MCP server bridges the mod's HTTP API to the MCP protocol (stdio transport), enabling Claude Desktop and Claude Code to interact with the game natively.

### Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "sts2": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/STS2_MCP/mcp", "python", "server.py"]
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sts2": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/STS2_MCP/mcp", "python", "server.py"]
    }
  }
}
```

### MCP Server Options

```
--host HOST   Game HTTP server host (default: localhost)
--port PORT   Game HTTP server port (default: 15526)
```

Documentation for MCP is at [mcp/README.md](./mcp/README.md).

## License

MIT
