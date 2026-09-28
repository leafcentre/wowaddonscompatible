# Getting measurements out of a live WoW client

Use when an edit's effect is only observable in-game, the user is the only one who can run the
client, and every extra round trip is expensive. Also use it to test the premise of a report —
both "that fixed it" and "it still doesn't work".

## 1. Establish which code the running session actually loaded

- SavedVariables are written at **session boundaries** (log-out, `/reload`, character switch),
  never when the files on disk change. A save timestamp therefore says nothing about which
  version of a `.lua` the client had in memory. Never conclude "the fix is live" — or "the fix
  failed" — from file mtimes alone.
- The client logs its own session boundaries in `<install>/_retail_/Logs/General.log`:
  `[N][Glues] Startup()` + `Resume()` = entering the world (this is when addon files are read),
  `Suspend()` / `Shutdown()` = leaving the world or back to character select. Compare those
  timestamps against the addon file mtimes to learn whether the session that produced the
  screenshot or the save was even running your edits.
- `/reload` ordering matters: the client saves the outgoing session FIRST, then reloads the UI
  and re-reads the files. So a probe added during this round is not in the file after one
  reload — ask for a second reload, or a reload followed by logging out.
- BugGrabber's `session` counter increments per client run. Use it to confirm a new run really
  started, and to tell whose errors/writes you are looking at.
- A **newly added or renamed addon directory is not picked up by `/reload` at all** — the addon
  list is built at client start. "Module produces no errors" then just means it never ran. Prove
  loading positively with that module's own `SavedVariablesPerCharacter` file, or with the
  core probe's keys changing.

## 2. Make the client write the measurement for you

Write both probes into the addon's SavedVariables so they can be read straight off disk.

- **Login snapshot** — at the end of the addon's init (after the frames exist), one `format()`
  string holding every input the failing path depends on. Wrap the block in `pcall`: `tostring()`
  on an inaccessible value may itself refuse, and an unprotected probe aborts the addon's init.
  Record the negative results too (`issecretvalue ~= nil`, `canaccessvalue ~= nil`,
  `RAID_CLASS_COLORS ~= nil`, `C_ClassColor ~= nil`) — "the API you assumed exists here does
  not" is one of the most common answers and it is invisible in a screenshot.
- **Decision probe** — at the branch under test, once per session: the values the branch saw
  (`unit=… isPlayer=… class=… gate=… colours=…`) plus which way it went (`-> tookClassColour=`).
  Key the one-shot to the frame under test (`self == TheFrame`) so the first unrelated frame to
  update does not consume it.
- **A write-once probe into SavedVariables freezes forever.** The guard `if (probe[key] == nil)`
  is checked against the SAVED table, which persists across sessions, so the entries from the
  first session that ever ran it are what every later read returns. Reset the table at login
  (`Config.probeX = nil` in the same init block) or the data you read is from days ago and looks
  exactly like fresh evidence.
- To observe the outcome of an early-`return` branch, convert it to a `local flag = true` plus a
  trailing `if (flag) then return end`; behaviour is identical and the result becomes readable.
- **Do not read another file's file-local from your probe — it is silently nil and reports a false value.** Z-Perl/QueFrame cores declare `local init_done, gradient, conf, doneOptions` (QueFrame_Init.lua) and `local conf` (QueFrame_Globals.lua), so a probe placed in a *different* core file (`QueFrame_Slash.lua`) reading `conf.bar.fat` sees a global that is usually nil and prints "fat=0" while the frames are demonstrably laid out in fat mode. Read the config through the global the config system publishes (`QueFrameDB`, set alongside the file-local), or record the value the code path itself used.
- **Geometry probe — the cheapest way to end a "this frame's bar is wrong" thread.** One line per unit frame, identical fields in the same order, so a single divergent frame stands out: `outer/name/portrait/stats` dims, then every bar `hp/mp/xp/rep/druid` as `WxH` plus a `(H)` marker when hidden, then a derived verdict `stack=n in WxH leftover=<statsH - sum of shown bar heights> top=<?> bot=<?>` computed as `statsFrame:GetTop() - firstShownBar:GetTop()` and `lastShownBar:GetBottom() - statsFrame:GetBottom()`. pcall every geometry read (`GetWidth`/`GetHeight`/`GetTop`) and classify the result — bar geometry can come back secret/inaccessible, and `floor(secret + 0.5)` throws where `format("%.0f", secret)` does not. This one line answers "where is the empty space", "is it a mode problem or an untouched frame" and "is the percent string really drawn in the space being reserved for it" without a screenshot, and run it on a WORKING sibling frame in the same pass: identical configs plus different geometry is the proof that the fault is a call that never ran, not a parameter.
- **Symmetric padding is by design, dead space is not.** In Z-Perl fat mode the bar stack always ends 5px above the frame bottom (5px top padding too); `top` and `bot` both reading ~9 with 10px bars in a 40px box means the bars are still at the template geometry (10px bars, 2px gap, no layout), not that the mode is off.
- Remove probes once the path is confirmed — they write into the user's own saved config.

## 3. Probe catalogue

- **Whole-addon removed-API sweep** (the highest-value probe for a ported addon). Old code hoists
  globals into file-scope locals at load, so a removed API becomes a nil upvalue whose first call
  aborts the rest of that function. Collect every pure alias from every file with
  `^local (\w+) = \1\s*$`, emit them as one Lua list, and at login record the ones where
  `_G[name] == nil` into a single SavedVariables string. One reload then names every dead API in
  the addon instead of one BugGrabber crash per discovery. Re-run the collection and extend the
  list after adding modules.
- **API-surface probe** — for a capability you are about to depend on, record existence flags
  (`UnitHealthPercent ~= nil`, `UnitPowerPercent ~= nil`, `C_CurveUtil.CreateCurve ~= nil`,
  `CurveConstants ~= nil`, `CurveConstants.ScaleTo100 ~= nil`), whether your own curve object was
  created, and how each read classifies. This is what separates "the API is missing" from "the
  API is present but the call needs a curve" from "my wrapper returns nil for a different
  reason".
- **Classification helper, never `tostring`** — for any probe field that may hold a secret, use
  `issecretvalue(v)` -> `SECRET`, `canaccessvalue(v)` -> `NOREAD`, then truthiness, then
  `tostring` only on a readable value, IN THAT ORDER (`v == nil` on a secret is itself a
  forbidden comparison). `tostring` of one secret taints the whole formatted string and the
  client serialises the entire entry as `nil --[[ secret value ]]`, destroying every other field
  in that probe. A field that comes back as that serialised nil is still evidence the value was
  secret — do not spend a round "fixing" the probe that produced it.
- **Widget-state probe** — a `C_Timer.After(5, …)` pass over the frames recording, per bar,
  `IsShown()`, `GetWidth()` and `HasSecretAspect(Enum.SecretAspect.Text)` for the value/percent
  fontstrings. Never call `GetText()` and concatenate the result: once you have written a secret
  into a fontstring, `GetText()` throws (`invalid value (secret) … for 'concat'`) — and that throw
  is the proof the number reached the widget. Guard it with `pcall` and record the state.
- **Don't self-poison the string** — keep each probe in its own SavedVariables key so one bad
  field cannot take the others down with it, and read the keys individually off disk rather than
  parsing one giant blob.

## 4. Infer from data already on disk before instrumenting

- A saved config value can prove a code path RAN. Z-Perl only fills `rangeFinder.spell` from
  `DefaultRangeSpells[playerClass]`, so a populated spell both identifies the player's class and
  proves `UnitClass` was readable at that moment — enough to exonerate the whole class-read layer
  without touching the game.
- Pixel-sample screenshots instead of trusting a description. A health bar of pure `(0,G,0)`
  (R and B both zero) is the green gradient/`healthFull` fallback and can never be a class colour:
  every Blizzard class colour has a non-zero R or B. The NAME text then splits the cases — a class
  colour means the class token is readable, the addon's nil-class default (`{0.5,0.5,1}` =
  `#8080FF`) means it is not.
- **A probe that never appears is itself a measurement.** If the decision probe for branch X is absent from the save while the login snapshot landed, branch X was never entered: the fault is an early return upstream (or a different call site), not the branch's inputs. That one fact outranks any static reading of the branch and short-circuits the "the inputs are all correct, so the lookup table must be wrong" rabbit hole — a real case had a login snapshot showing every gate input perfect while the colour branch was dead because the shared bar setter returned before reaching it whenever the health numbers were secret.
- **Sort BugGrabber entries by `session` AND `time` before fixing anything.** Entries for errors you already fixed stay in the file; a "2 errors" read can be entirely stale while the current session is clean. The current session number is the `session` of the newest matching save; a stale entry whose stack names a file that no longer exists at that shape is post-fix noise.
- Sample with PIL/numpy, never a vision model: the model reported the wrong colours twice and the
  wrong region once on the same UI screenshot. Its region descriptions are a starting hypothesis
  for where to sample, not a fact. Run PIL/numpy through the interpreter that has them (the
  execute_code sandbox may not), and isolate a region by scanning for a distinctive colour rather
  than trusting a described bounding box.

## 5. Order of verification for a "still broken" report

1. Did the session that produced the evidence load the edits? (session log vs mtimes, and for new
   dirs: is the module's SavedVariables file present at all)
2. Is the config table the code actually reads the one you think it is? (global vs per-character,
   saved keys vs default keys)
3. Did the failing path run at all? (decision probe present vs absent in the save) — absence
   means an early return upstream, and that is a different fix from "an input is wrong". For
   anything geometric, the same question is answered by size: a bar still at the template's
   exact XML size was never laid out by any path.
4. What does the failing path resolve to at runtime? (decision probe contents)
5. Only then change code.

Skipping to step 5 produces "fixes" that are really new hypotheses, and it burns the user's
patience faster than asking them for one more reload would.
