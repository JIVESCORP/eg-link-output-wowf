# Datasets

Every file under `data/` is written by Efficient Games' processing job, which runs once a day and
commits only when something changed. Don't edit them by hand: the next run replaces them.

## Layout

```
data/index.json                                          every product, build and dataset, with counts
data/<product>/<clientBuild>/<dataset>.json              one file per dataset that has records
data/<product>/<clientBuild>/<dataset>.<locale>.json     the datasets in the game's own words, per language
```

- `<product>` is the Battle.net product code of the client the data came from. World of Warcraft:
  Forever's beta is `wow_classic_beta`. The live game gets its own code when it launches on
  4 November 2026.
- `<clientBuild>` is the client's version, such as `1.60.1.70009`. A build's data is only what
  players recorded on that build, so compare builds to see what a patch changed.
- `<locale>` is the game client's language, such as `enUS`. The five datasets read from the game's
  caches (`quests`, `creature_details`, `object_details`, `item_hotfixes`, `broadcast_text`) are
  mostly the server's text, and the three scans of the game's tooltips (`talent_scan`, `stat_scan`,
  `tooltip_scan`) and the words its windows showed (`texts`) are the game's text, so each language
  gets its own file. Names in the other datasets are in whatever language the contributing players'
  clients use.

`data/index.json` has `license` and `attribution`, and `products[product][clientBuild][dataset]` for
every file: `records` (how many records the file holds, across its collections), `sources` (as the
file's `meta.sources`) and `lastCollectedOn` (its `meta.collectedOn.last`). A per-language dataset is
listed under its file's name, such as `quests.enUS`.

Every file is UTF-8 JSON with one space of indent. Object keys are sorted: numerically when every
key is a number, otherwise alphabetically. A field with nothing to say is left out, never `null`.

Each dataset file starts with a `meta` block:

| Field | Meaning |
|---|---|
| `dataset`, `product`, `clientBuild` | what the file is |
| `schemaVersion` | the file's shape; it changes only when a field changes meaning or is removed |
| `sources` | how many players' saved files (a game account on one computer) contributed |
| `combatLogUploads` | `creatures` and `encounters` only: how many combat-log uploads contributed |
| `locale` | the per-language datasets only: the client's language |
| `cacheFiles`, `cachesLeftOut` | the cache datasets only: how many cache files were read, and how many weren't (a layout the game changed, which Efficient Games must learn before reading it) |
| `collectedOn.first`, `collectedOn.last` | the days of the oldest and newest contribution used |
| `license`, `attribution` | CC BY 4.0, and the credit line to use |

## How contributions are combined

EG Link records running totals on each player's computer, so each player's newest upload replaces
their earlier ones. Players' contributions are then combined:

- **Counts add up**: kills, loot windows, drops, visits, flight times, XP and reputation per kill.
- **Facts take the newest value**: a name, a price, a level, a route's stops. "Newest" is the day the
  player last saw the record. When players saw different values on the same day, the value most of
  them saw wins. Prices are picked separately for each standing and each Legacy talent rank.
- **Sets are unions**: an NPC's interactions, a creature's classifications and reactions, the
  maximum health values seen at each level.
- **Positions are merged**: every player's positions, keeping one per 5 yards (3 yards for objects
  walked up to).
- **Every record says how many players' files it came from** (`sources`).

Positions are `{instance, uiMap, mapX, mapY, worldX, worldY}`: `mapX`/`mapY` are 0-1 across the
`uiMap` map (x right, y down), and `worldX`/`worldY` are the game's world coordinates in yards on
`instance`. They're where the player's character stood: at an NPC when its window opened, at a
corpse when it was looted, and so on. Combat-log positions are `{map, uiMap, x, y}` in world yards:
`map` is the map the creature is on (0 Eastern Kingdoms, 1 Kalimdor, else an instance's map ID), and
`uiMap` is 0 inside an instance, where the game has no map. Positions from logs read before
2026-10-02 have no `map`.

Standings (the keys of `costs`) are the game's reaction numbers: 4 Neutral, 5 Friendly, 6 Honored,
7 Revered, 8 Exalted. A price is in copper, for the item's `stack`, as the game showed it at that
standing. Prices seen with the Legacy talent Bartering are kept apart under `bartered[rank][standing]`,
with rank `"?"` when the game wouldn't say the rank.

Days are `YYYY-MM-DD` in UTC. Nothing is more precise than a day.

## vendors

`vendors[npcId]`, every vendor a player opened:

- `name`, `repairs` (whether it repairs), `lastSeen`, `visits`, `positions`, `sources`
- `entries[key]`, keyed `item:<id>`, `currency:<id>` or `spell:<id>`, with `#2`, `#3` for the same
  thing listed twice. Each has `itemId`/`currencyId`/`spellId`, `name`, `stack`, `startsQuest`,
  `limited` and `stockMax` (limited stock), `costItems` (items or currencies it costs besides
  money: `itemId`/`currencyId`, `name`, `amount`), `costs[standing]`, `bartered[rank][standing]` and
  `sources`.

## trainers

`trainers[npcId]`, every trainer whose list a player opened:

- `name`, `trainerType` (the game's trainer type: 0 on class trainers and 2 on profession trainers so
  far), `tradeskill`, `lastSeen`, `positions`,
  `sources`
- `services[spellId]`: `spellId`, `name`, `rankText`, `category`, `icon` (a FileDataID), `level`
  (the level it can be learned at), `skill` and `skillRank` (a profession requirement), `abilities`
  (what it teaches), `profession` and `step` (a profession or a new rank of one), `costs[standing]`,
  `bartered[rank][standing]`, `sources`. A trainer shows level 0 for a spell the character already
  knows, so `level` is the newest level that isn't 0, and 0 only when no player saw another.

A class trainer lists only its own class's spells, so its services are the union of what players
of that class saw.

## npcs

- `npcs[npcId]` and `objects[objectId]`, everyone and everything a player opened a window at: `name`,
  `side` (Alliance, Horde), `levels` (every level seen), `windows` (windows opened), `interactions`
  (the kinds of window: Merchant, Trainer, QuestGiver, Gossip, TaxiNode, Binder, Banker ...),
  `options[gossipOptionId]` (`name`, `icon`, `spellId`), `offers[questId]` (quests it gives: `title`,
  `level`, `frequency`, `repeatable`, `legendary`, `important`, `meta`, and `infoId`, the quest's
  `QuestInfo` ID as `questInfoId` in `quests.<locale>`: 81 Dungeon ...), `takes[questId]` (quests it
  ends: `title`, `level`), `lastSeen`, `positions`, `sources`.
- `approached[objectId]`, objects players walked up to without opening (herbs, veins, mailboxes):
  `name`, `times`, `positions`, `sources`. An object ID is a kind of object, so every Copper Vein
  shares one, and its positions are everywhere it grows.

## flights

- `masters[npcId]`: `node` (the flight point's `TaxiNodes` ID), `name`, `sources`.
- `routes["<from>><to>"]`, flight point IDs, with `|frequentFlier:<rank>` when the Legacy talent
  Frequent Flier was on: `hops` (the flight points flown through, in order), `costs[standing]`,
  `seconds[duration]` (how many flights took that many seconds), `arrivals` (where flights landed),
  `sources`. A trip with stops costs the sum of its legs.

## loot

- `format`: the addon's loot format (3).
- `sources[key]`, keyed as the addon keys them: `npc:<id>` a corpse, `npc:<id>|spell:<id>` skinning
  or pick pocket, `object:<id>|spell:<id>` a node or chest opened with that spell, `fishing:<uiMap>`,
  `item:<id>` a container. Then, in order: `|quest` when the creature was tied to one of the
  character's active quests (quest items drop only then), `|bountifulHarvest:<rank>` or
  `|luremaster:<rank>` when that Legacy talent was on, and `|group` in a group. Each has:
  - `windows`: loot windows opened;
  - `items[itemId]` and `currencies[currencyId]`: `drops` (slots it filled), `quantity`, `shared`
    (drops in a slot shared by several sources, quantity unknown), `quest` (a quest item: the quest's
    ID when the game gave it, else `true`) and `chance`;
  - `coins` (coin slots, one per window with money), `copper` and `copperWindows` (money from
    windows with one source, solo);
  - `positions`, `sources`;
  - `quests[questId]`, under a `|quest` key: the same loot counted per quest the creature was tied to
    when it died: `windows`, the quest `items` in those windows (`drops`, `quantity`, `shared`,
    `chance`), and `sources`. A window counts for every quest the creature was tied to.
- `kills[key]`, keyed as the corpse: `deaths`, `empty` (corpses with nothing on them), `unknown`
  (corpses the game didn't say about), `levels[level]`, `sources`, and under a `|quest` key
  `quests[questId]`: the corpses tied to each quest (`deaths`, `empty`, `unknown`, `sources`).

`chance` is the expected number of that item per kill: the share of corpses with loot
((`deaths` - `empty` - `unknown`) / (`deaths` - `unknown`)) times `drops` / `windows`. For a source
with no kill count (nodes, chests, skinning, containers) it is `drops` / `windows`. It is rounded half
up to 4 decimals. With few kills it is rough; the counts are there to judge it.

A creature can be tied to several quests at once: killed for one quest, say, and looted for another's
item. A quest item drops only for a character on the quest that needs it, so its chance per kill is the
one under that quest, `sources[key].quests[questId].items[itemId].chance`, worked out from that quest's
own `windows` and `kills`. The chance on the key itself mixes in every other quest's kills. The game
rarely says which quest a drop is for (an item's `quest` is usually `true`), so look up which quest
needs the item in the quest's own data: its objectives and `itemDrops` in `quests.<locale>`. Counted by
EG Link releases after 0.2.9.

## creatures

`creatures[npcId]`:

- From the addon's creature recorder: `name`, `seen` (spawns seen), `levels[level]`, `classifications`
  (normal, elite, rare ...), `reactions[faction]` (the reactions shown to that faction's players),
  `questBoss`, `deaths` and `positions` (where the character stood when this creature, its target,
  died), `xp["<character level>:<creature level>"][xp]` and `rep["<race>"][factionId][change]` (kills
  that paid that much, counted only when nothing else paid at the same time), `sources`.
- `combatLog`, from the game's combat log where players switched it on: `name`, `entries` (logging
  sessions it appeared in), `spawns`, `deaths`, `levels[level]`, `maxHealth[level]`,
  `maxPower[powerType]`, `casts[spellId]` (`name`, `starts`, `successes`), `melee[level]` (`hits` and
  the `low` and `high` hit before armor; level `"?"` when unknown), `positions` (`{map, uiMap, x, y}`),
  and `sources`, which here counts players rather than saved files. Players, their pets and anything a player summoned are never included.

A creature only the combat log saw has only `combatLog`.

## encounters

`encounters[encounterId]`, the boss encounters players fought with the game's combat log switched on
(`ENCOUNTER_START` to `ENCOUNTER_END`): `name`, `map` (the instance's map ID), `pulls` and `kills`,
`difficulties[difficultyId]` (pulls), `bosses` (the IDs of the creatures named as the encounter is),
`positions` (`{map, uiMap, x, y}`: where pulls began, the boss's first position in the fight), `runs`
and `sameRun[encounterId]`, `entries` and `sources` (players).

A run is one copy of an instance that a player's log fought encounters in. `runs` counts the runs an
encounter was fought in, and `sameRun` how many of those each other encounter was fought in too. A
dungeon's wings are each a copy of their own, so encounters that share runs are one wing's: Dire
Maul's three wings are all map 429. A run that spans two logs (the game restarted mid-dungeon) counts
as two.

## turn_ins

`quests[questId]` and `withLegacy[questId]` (turned in with the Legacy talent Diplomat): each distinct
thing a turn-in paid, once, with how many `sources` saw it. An observation has the character's
`level`, `race` and `faction`, `xp`, `money` (copper), `maxLevel`, `xpDisabled`, `rep` (each
`factionId`, `change`, `to` and `bonus`), `repFrom` (`event` or `comparison`, how the addon read
it), and `diplomat` (the talent's rank).

## objectives

- `quests[questId][objective]`: `type` (`monster`, `item`, `object`, `event` ...), `required`, `gains`
  (times the count went up), `positions` (where the character stood each time), `sources`.

Escorts and scripted events often have no count: the quest just becomes complete, or fails,
somewhere. Recorded from EG Link 0.2.5:

- `completed[questId]`: the quest became complete with no count going up just before. `times`,
  `positions` (where the character stood: where the escort or event ends), `sources`.
- `failed[questId]`: `times` the quest failed (an escort lost, a timer run out), `sources`.
- `gossip[questId][choice]`: a gossip option a player chose before the quest moved. `choice` is
  `npc:<npcId>|option:<option>` (or `object:<objectId>|...`), where `<option>` is the
  `gossipOptionId`, or `name:<text>` in the player's language when the game gave none, as in `npcs`'
  `options`. `soon` counts the times the quest moved within seconds of the choice (speaking with
  someone was the step), `before` the times it later completed with no count, or failed, and this
  was the last choice made since (the "I'm ready" that starts an escort). Either is left out when no
  player saw it. `sources`.

## item_uses

The items players used for their quests, recorded from EG Link 0.2.5. A quest's objectives never say
that an item has to be used first (Morbent's Bane on Morbent Fel, a Taming Rod on a beast); this does.
A use is a successful cast of the item's spell. An item counts when the quest tracker shows it for a
quest, when a quest handed it over, or when it's a Quest item.

- `quests[questId][itemId]`: `spellId` (the item's spell, a fact), `uses`, `targets` (what the uses
  were cast on: `npc:<npcId>`, `object:<objectId>`, `none` when there was no target or it was the
  player's own character, and `other` for another player, a pet or a target the game kept hidden,
  never named), `progressed` (uses after which the quest moved: a count went up or it became
  complete), `objectives[objective]` (which counts went up after a use), `positions` (where the
  character stood), `sources`. Counts add up.
- `untied[itemId]`: the same, without `progressed` and `objectives`, for a Quest item no quest in the
  player's log claimed, and after which no one quest moved.

## quest_scan

EG Link asks the server about every quest the client lists. The server describes only quests that
are open.

- `described[questId]`: `title`, how many players' scans got it (`sources`), and per faction
  (`Alliance`, `Horde`) how many scans of that side got it (`factions`) and how many got no data for it
  (`noDataFactions`). A quest one side gets and the other doesn't shows in those two.
- `noData`: quests some scan asked about and none got an answer for.

A scan's side is the side of the character that asked. A scan from before EG Link 0.2.6 doesn't say
which side got each answer, so its answers count for its characters' side when they were all one
side's, and for neither otherwise.

`title` is in whichever language the newest scan's client used. `quests.<locale>` has each language's
text.

What the game said of a quest, recorded by EG Link releases after 0.2.6, each as how many players'
files had the answer, so any disagreement shows:

- `pushable[questId]`: `true` and `false`, the game's answer to whether the quest can be shared
  (`C_QuestLog.IsPushableQuest`), read when the scan found the quest described.
- `frequency[questId][frequency]`: what the quest log said: `1` Daily, `2` Weekly, `3` resets on a
  schedule.
- `repeatable[questId]`: the game called the quest repeatable.

`frequency` and `repeatable` are read only for quests in a player's log, so a quest with neither may
still be daily or repeatable.

## talent_scan.&lt;locale&gt;

What the game shows for every class talent at each rank and for every class spell, read from its
tooltips. The game writes a tooltip's numbers for the character reading it, so each reading says which
character it was (`reader`).

- `readers[n]`: a character readings were written for: `class`, `level`, `talentPoints` (spent; a talent
  can change what a tooltip says), `spellDamage` (by school, 1 Physical to 7 Arcane), `healing`,
  `spellHaste`, `rangedHaste`, `attackPower`.
- `entries[entryId]` (a `TraitNodeEntry` ID): `ranks[rank]`, the talent's text at each rank, and
  `tooltip`, the lines of its tooltip.
- `spells[spellId]`: `castTime` and `cooldown` and `gcd` (milliseconds), `minRange`, `maxRange`,
  `passive`, `description`, `costs` (`name`, `type`, `cost`, `minCost`, `costPercent`, `costPerSec`,
  `hasRequiredAura`, `requiredAuraID`), `charges`, and `tooltip` for a talent's own spell.
- Each entry and spell is one player's reading, with `reader` and `sources`. A reading that says
  something beats an empty one, then the reader with the fewest talent points, then the newest.
- `notLoaded`: spells no player's game loaded.

## stat_scan.&lt;locale&gt; and tooltip_scan.&lt;locale&gt;

Items as the game's tooltip shows them: one or two items for every stat type (`stat_scan`), and every
weapon (`tooltip_scan`). These show where the game differs from the client's tables: a weapon whose
damage nothing in the client files gives, say.

- `items[itemId]`: `name`, `quality`, `itemLevel`, `minLevel`, `sellPrice` (copper; `stat_scan` only),
  `stats` (the game's own key for each, such as `ITEM_MOD_STAMINA_SHORT`, with its value; damage per
  second to 4 decimals), `labels` (`stat_scan` only: the game's name for each key, or `false` when it
  has none), `tooltip` (its lines, bar those about the reader's collection), `sources`. A fact, so the
  newest wins.
- `notLoaded`: listed items no player's game held. The server sends some items only when a player
  meets them.

## durability

`items[itemId]`: `max`, an item's maximum durability as the game reported it for one a player's
character held. The server sets it item by item, and no client table holds it. `disagree` lists any
other maximum a player's game reported, and `sources` counts the players.

## game_rules

Game rules no client file holds, read from players' games (EG Link 0.2.14 and later). Each is a fact
about the game, not about a player, bar where a new character first stood and where a class teleport
landed, which are combined per race, faction and class and per spell, never per character.

- `starts["<race>|<faction>|<class>"]`: where new characters first logged in, keyed by the game's race
  and class tokens (`Scourge` is Undead). `count` (characters), `positions` (where they stood; a spot
  without `uiMap`, `mapX` and `mapY` is one the character had already moved from when the map was read),
  `zones` and `subZones` (the zone text the game showed, per client language, with counts), `sources`.
- `teleports[spellId]`: where a class teleport landed (the Mage teleports and Teleport: Moonglade), the
  same fields.
- `levelCap`: `maxPlayerLevel`, `maxLevelForLatestExpansion` and `maxLevelForPlayerExpansion`, each value
  a player's game gave with how many players' games gave it.
- `standings[reaction]["<from>..<to>"]`: each standing's point range, `reaction` counting from 1 (Hated)
  to 8 (Exalted), `to` exclusive (Neutral is `0..3000`: 0 to 2,999).
- `renown[factionId]`: each renown track (PvP Rank Points, Legacy Track): `name`, `factionID` (the
  key again), `expansionID`, `maxLevel`, `renownLevelThreshold`, and `levels[level]` with
  `totalReputation` and `rewards` (`itemID` and the other reward IDs, `name`, `description`, `icon`,
  `uiOrder`, `rewardType`, `isAccountUnlock` ...). The game gives every reward's `renownRewardID` as
  0, so match rewards by `itemID`; a reward's `name` can be missing.
- `questDifficulty[effectiveLevel][questLevel][difficulty]`: the colour the game gives a quest, 0 Trivial
  (grey), 1 Easy (green), 2 Fair (yellow), 3 Difficult (orange), 4 Impossible (red).
  `trivialRange[effectiveLevel][range]`: how many levels below the character a quest turns grey.
- `rewardSpells[questId][spellId]`: what the quest window's reward spell says of itself
  (`C_QuestInfoSystem.GetQuestRewardSpellInfo`): `type`, `isTradeskill`, `isSpellLearned`,
  `hideSpellLearnText`, `isBoostSpell`, `genericUnlock`, `sources`, and `disagree`, any other set of
  flags a player's game gave, with how many.
- `professionCaps[skillLine][step][maxRank]`: the skill cap at each profession tier (step 1 Apprentice,
  2 Journeyman ...; `?` when the tier wasn't known).

Sets and caps say how many players' games (`sources`) gave each value, so a game that disagrees shows.

## texts.&lt;locale&gt;

The words quest windows, gossip windows, greetings and books showed players, for voice-over addons:
recorded by EG Link 0.2.9 and later, and sent by EG Link's app from 0.6.0. Each place holds a list of
variants, every different text players saw there, the most `sources` first:

- `quests[questId]`: `accept` (the quest's text as it was offered), `objectives` (the line saying what
  to do), `progress` (what the giver says while the quest isn't done) and `complete` (what it says at
  the turn-in).
- `greeting[key]`: what a quest giver with no gossip says above its quests. `gossip[key]`: a gossip
  window's text. A key is `npc:<npcId>` or `object:<objectId>`.
- `books[source][page]`: a book, letter or plaque read, page by page: `title`, `material` (the page's
  background, such as `Parchment` or `Silver`), `texts` (the page's variants). A source is
  `object:<objectId>`, `item:<itemId>` or, when the game named neither, `title:<the book's title>`.

A variant has:

- `text`. When it is the game's own text, `template` says where it was found: `questCache` (the quest's
  `description` or `objectivesText` in `quests.<locale>`) or `broadcastText` (rows of
  `broadcast_text.<locale>`, all listed in `broadcastTextIds`; `text` is the lowest ID's). `text` is
  then the template itself, with the game's placeholders, and every player's copy that matched counts
  as one of its sources, whoever read it. A copy matches when it equals the template with line breaks
  (`$B`, `\r\n`) and the reader's `$n`/`$N`, `$c`/`$C` and `$r`/`$R` made alike, and the template's
  `$g<male>:<female>;` read as either. Otherwise `text` is what the game showed, with the reader's name,
  class and race put back as `$N`, `$C` and `$R`. A placeholder the game showed as it was, such as `$r`
  in a greeting, stays.
- `sources` (players' saved files that sent it), `times` (how often it was shown).
- `sexes`: how often it was shown to a character of each sex, `male` and `female`. A gendered line's
  form depends on it.
- `speakers` (`quests` only): who showed it, `npc:<npcId>`, `object:<objectId>`, `item:<itemId>` or
  `none`, with how often.

No text names a player. EG Link drops any text holding the name of one of the player's characters, and
any while the game keeps the reader's name, class or race secret; Efficient Games then drops any text
that isn't the game's own and names one of the contributing member's characters, and any book page
whose title or source does. `meta.withheld` counts them, never their words: `addon` what EG Link held
back, and `names` what Efficient Games did, each per kind (`quests`, `greeting`, `gossip`, `books`).

## The cache datasets

The game keeps the server's answers in cache files: what a quest says, what a creature or object is,
and the rows of the game's tables the server sent after the client shipped ("hotfixes"). The last are
in `DBCache.bin`: its `ItemSparse` rows make `item_hotfixes`, and its `BroadcastText` rows
`broadcast_text`. EG Link's app uploads them as the game wrote them. A cache holds what the game asked
about since it last started one, so every upload adds to what's known, and a player's newer upload
replaces only the records it has. For each record, the newest player's answer wins (for a pushed item, the newest push
first), then the one most players have. `sources` counts the players who had it.

A cache is read only when it's from the upload's build and language, and only when its record layout
has been checked record by record. Otherwise the whole file is left out and counted in
`meta.cachesLeftOut`.

### quests.&lt;locale&gt;

`quests[questId]`, every quest a player's game asked the server about, as the server described it.
IDs aren't joined to names here: the client's own tables name zones, items, factions and spells.

- `title`, `level`, `minLevel`, `zoneAreaId` (the zone, an `AreaTable` ID) or `categoryId` (a
  `QuestSort` ID), `questInfoId`, `questType`, `flags`, `flagsEx`, `flagsEx2`, `nextQuestId`,
  `startItemId`, `timeLimitSeconds`
- `raceMask`: the races allowed, as 16 hex digits. Each bit is a race's `ChrRaces.PlayableRaceBit`,
  and every bit set means every race.
- the text: `objectivesText`, `description`, `completionText`, `areaDescription`, and the portraits'
  `portraitGiverText`, `portraitGiverName`, `portraitTurnInText`, `portraitTurnInName`. `$n`, `$r`,
  `$c` and `$g...;` are the game's placeholders for the reader's name, race, class and gender.
- `objectives`: `id`, `typeId` and `type` (`monster`, `item`, `gameObject`, `talkTo`, `areaTrigger`,
  `criteriaTree`, `areaTriggerEnter`; left out for a type not yet identified), `objectId`, `amount`,
  `storageIndex`, `text`
- `itemDrops`: items that drop for the quest (`itemId`, `count`)
- `rewards`: `xpDifficulty` and `xpMultiplier` (the XP is the client's `QuestXP` row for the quest's
  level at that difficulty, times the multiplier), `money` (copper), `spellId`, `displaySpells`
  (`spellId`, `type`), `items` and `choices` (`itemId`, `count`), `reputation` (`factionId`, `tier`,
  and `override`, an explicit amount stored times 100 that replaces the tier's), `currencies`
  (`currencyId`, `amount`)
- `conditionalDescriptions` and `conditionalCompletionTexts` (`playerConditionId`, `creatureId`,
  `text`), `treasurePickerIds`
- `sources`

### creature_details.&lt;locale&gt;

`creatures[npcId]`, every creature a player's game asked about:

- `name`, `femaleName`, `otherNames`, `title` (the line under the name, such as "Druid Trainer"),
  `femaleTitle`, `cursor` (the cursor shown over it), `leader`
- `type` (a `CreatureType` ID: 1 Beast, 7 Humanoid ...), `family` (a `CreatureFamily` ID for beasts
  and demons: 1 Wolf, 2 Cat ...), `classification` (0 normal, 1 elite, 2 rare elite, 3 world boss,
  4 rare, 5 trivial, 6 minus), `unitClass` (1 warrior, 2 paladin, 4 rogue or 8 mage, as the game
  classes creatures)
- `flags` (three flag words; 0x1 in the first marks a tameable beast), `proxyCreatureIds` (creatures
  whose kill credit it gives)
- `displays` (`displayId`, a `CreatureDisplayInfo` ID, with `scale` and `probability`) and
  `totalProbability`
- `hpMultiplier`, `energyMultiplier`
- `questItems`: items it drops only for players on the quest that needs them. `questCurrencies`
  likewise.
- `movementInfoId`, `healthScalingExpansion`, `requiredExpansion`, `vignetteId`, `widgetSetId`,
  `widgetSetUnitConditionId`
- `creatureDifficultyId`: the server's difficulty record for it, which the client doesn't have. It
  equals the creature's own ID for Classic's creatures.
- `sources`

### object_details.&lt;locale&gt;

`objects[objectId]`, every game object a player's game asked about (chests, herbs, veins, doors,
boats ...): `type`, `displayId`, `name`, `size`, `data` (35 numbers whose meaning depends on the type:
for a boat or zeppelin, type 15, the first is its `TaxiPath` ID and the next two its speed and
acceleration), `questItems`, `sources`.

### item_hotfixes.&lt;locale&gt;

`items[itemId]`: what the server said about an item's `ItemSparse` row, the table holding an item's
name and figures. WoW Forever ships thousands of items without one and sends it when it's ready, so
this is how an item missing from the client files gets its name.

- `status`: `valid` (the server sent the row), `removed` (it said there's no such item) or `invalid`
  (the game asked and the server refused: the item exists, and the server doesn't show it yet)
- `pushId`: which of the server's hotfix pushes said so (-1 for an answer to the game's own request)
- `name` and `description`, for a `valid` row
- `sources`

### broadcast_text.&lt;locale&gt;

`texts[broadcastTextId]`, every `BroadcastText` row the server sent a player's game: the lines NPCs say
in gossip windows and speech. `texts.<locale>` matches what players saw against these.

- `text` and `text1`: the line's two forms, the table's `Text` and `Text1`, for a male and a female
  speaker. Either is left out when the row has it empty. They hold the game's placeholders: `$n`, `$c`
  and `$r` for the reader's name, class and race, `$g<male>:<female>;` for the reader's gender, and
  `$b` or `$B` for a line break.
- `sources`
