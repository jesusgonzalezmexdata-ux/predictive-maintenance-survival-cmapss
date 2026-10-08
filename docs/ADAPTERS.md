# Adapter Strategy

Current adapters are intentionally thin. Root and local `AGENTS.md` provide the portable baseline. Claude/Gemini files import the canonical baseline; Cursor/Copilot/Windsurf/Aider receive generated equivalents. A future adapter must translate syntax without changing semantics or authority.

If a tool lacks a native hook or sandbox feature, wrap the tool so `repoctl` and external isolation provide the missing guarantee.
