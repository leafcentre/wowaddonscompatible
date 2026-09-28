# WoW 12.x removed global API → replacement mapping

Verified against warcraft.wiki.gg `Patch_12.1.0/API_changes` ("Removed" list) and the wiki's per-API pages (each removed API's page lists the modern signature). Extend this table as new removals surface in live testing.

Signatures to shim (legacy multi-return adapters, all wrapped in `if not _G.Name then`):

| Removed global | Replacement | Notes |
|---|---|---|
| `GetSpellInfo(id)` | `C_Spell.GetSpellInfo(id)` | returns table; legacy returns were `name, rank, icon, castTime, minRange, maxRange, spellID, originalIconID` |
| `GetSpellTexture` / `GetSpellLink` / `GetSpellCooldown` / `GetSpellCharges` | `C_Spell.*` | cooldown/charges return tables now |
| `IsSpellInRange` | `C_Spell.IsSpellInRange` | returns true/false/nil, not 1/0/nil |
| `UnitAura` / `UnitBuff` / `UnitDebuff` | `C_UnitAuras.GetAuraDataByIndex(unit, index, filter)` | returns auraData table; guard `type(index) == "number"` — some code passes spell names or nil as arg 2 |
| `GetItemInfo` / `GetItemCount` / `GetItemIcon` | `C_Item.*` | namespaced 10.2.6, global removed 12.x |
| `GetContainerItemInfo` / `GetContainerItemLink` / `GetContainerNumSlots` / `UseContainerItem` / `PickupContainerItem` | `C_Container.*` | |
| `GetWeaponEnchantInfo` (removed 12.1) | `C_PaperDollInfo.GetTemporaryEnchantmentInfo(slot)` | per-slot (16 main, 17 off); returns table `{hasEnchant, expirationTime, charges, enchantID}`; adapt to legacy 12-tuple, fill ranged (18) with false/nil |
| `GetInspectSpecialization` (removed 12.1) | `C_SpecializationInfo.GetInspectSpecialization(unit)` | |
| `GetInventorySlotInfo` (removed 12.1) | `C_PaperDollInfo.GetInventorySlotInfo(slotName)` | |
| `CancelItemTempEnchantment` (removed 12.1) | `C_PaperDollInfo.CancelTemporaryEnchantment(slot)` | |
| `MouseIsOver(frame)` (removed 12.1) | `frame:IsMouseOver()` | frame method, no shim needed — swap the call site |
| `GetComboPoints`, `UnitIsCharmed`, `GetRaidRosterInfo`, `UnitInRange`, `CheckInteractDistance`, `SpellIsTargeting` | still exist | do not shim; some (UnitIsCharmed) return Secret Values in combat |
| `getglobal` / `setglobal` / `UIParentLoadAddOn` | removed 12.0/12.1 | `UIParentLoadAddOn` → `LoadAddOnWithErrorHandling` |

Events:

- `COMBAT_LOG_EVENT(_UNFILTERED)` — registration errors outright on 12.x. Wrap in pcall; handler code becomes dead. Libs that early-return on non-classic (`WOW_PROJECT_ID ~= WOW_PROJECT_CLASSIC`) are dormant on retail — leave them.
- Combat-time `UnitHealth`/`UnitPower`/`UnitCastingInfo` return Secret Values — display OK, arithmetic/comparison can error in combat. Signature: `attempt to compare local '<varname>' (a secret number value, while execution tainted by '<addon>')` — the var name and the stack's top addon-frame point at the exact compare/arithmetic site to guard (wrap the comparison in a non-secret check, or drop to Blizzard's unit-percent APIs). Bars keep rendering; the error is noisy but not fatal.

Wiki workflow notes:

- `Patch_12.1.0/API_changes` page has the authoritative Removed list, but web extraction often drops the second table cell — search the page text for the API name instead of parsing the table.
- townlong-yak.com framexml pages return a JS gate ("Please hold") to non-browser fetches; use the wiki page for the API or raw.githubusercontent.com instead.
- `grep.app` API is behind a Vercel JS challenge; GitHub code search API needs auth. The wiki is the reliable offline-hours source.
