# Hooks and Event Fabric
Tool-native hooks are adapters. The guarantee is external: Git hooks, CI, `repoctl event`, sandbox and policy checks. If a future agent has no hook API, invoke it through a wrapper that calls these same gates.
