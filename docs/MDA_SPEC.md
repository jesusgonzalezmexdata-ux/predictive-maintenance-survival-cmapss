# MDA Specification v1.0

MDA in this repository is an internal intermediate representation. It contains canonical behavior, capabilities, maturity, authority, events and folder semantics. `repoctl compile` translates this representation to native instruction formats.

Adapter drift is a build failure. The correct remediation is to regenerate adapters, not manually reconcile copies.

## v2 intent compilation

MDA compilation now begins one layer earlier when owner intent is supplied. Markdown is parsed and normalized into an intent contract; the selected scaffold profile is then merged into `folders.mda.json`, after which normal adapter compilation generates root/local agent contracts. Tool-native configuration remains downstream and disposable.
