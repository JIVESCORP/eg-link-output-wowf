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
- `<locale>` is the game client's language, such as `enUS`. The four datasets read from the game's
  caches (`quests`, `creature_details`, `object_details`, `item_hotfixes`) are mostly the server's
  text, and the three scans of the game's tooltips (`talent_scan`, `stat_scan`, `tooltip_scan`) are
  the game's text, so each language gets its own file. Names in the other datasets are in whatever
  language the contributing players' clients use.

Every file is UTF-8 JSON with one space of indent. Object keys are sorted: numerically when every
key is a number, otherwise alphabetically. A field with nothing to say is left out, never `null`.

Each dataset file starts with a `meta` block:

| Field | Meaning |
|---|---|
| `dataset`, `product`, `clientBuild` | what the file is |
| `schemaVersion` | the file's shape; it changes only when a field changes meaning or is removed |
| `sources` | how many players' saved files (a game account on one computer) contributed |
| `combatLogUploads` | `creatures` only: how many combat-log uploads contributed |
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
corpse when it was looted, and so on. Combat-log positions are `{uiMap, x, y}` in world yards.

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
  `level`, `frequency`, `repeatable` ...), `takes[questId]` (quests it ends: `title`, `level`),
  `lastSeen`, `positions`, `sources`.
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
  - `positions`, `sources`.
- `kills[key]`, keyed as the corpse: `deaths`, `empty` (corpses with nothing on them), `unknown`
  (corpses the game didn't say about), `levels[level]`, `sources`.

`chance` is the expected number of that item per kill: the share of corpses with loot
((`deaths` - `empty` - `unknown`) / (`deaths` - `unknown`)) times `drops` / `windows`. For a source
with no kill count (nodes, chests, skinning, containers) it is `drops` / `windows`. It is rounded half
up to 4 decimals. With few kills it is rough; the counts are there to judge it.

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
  the `low` and `high` hit before armor; level `"?"` when unknown), `positions` (`{uiMap, x, y}`),
  and `sources`, which here counts players rather than saved files. Players, their pets and anything a player summoned are never included.

A creature only the combat log saw has only `combatLog`.

## turn_ins

`quests[questId]` and `withLegacy[questId]` (turned in with the Legacy talent Diplomat): each distinct
thing a turn-in paid, once, with how many `sources` saw it. An observation has the character's
`level`, `race` and `faction`, `xp`, `money` (copper), `maxLevel`, `xpDisabled`, `rep` (each
`factionId`, `change`, `to` and `bonus`), `repFrom` (`event` or `comparison`, how the addon read
it), and `diplomat` (the talent's rank).

## objectives

`quests[questId][objective]`: `type` (`monster`, `item`, `object`, `event` ...), `required`, `gains`
(times the count went up), `positions` (where the character stood each time), `sources`.

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

## The cache datasets

The game keeps the server's answers in cache files: what a quest says, what a creature or object is,
and the rows of the game's tables the server changed after the client shipped ("hotfixes"). EG
Link's app uploads them as the game wrote them. A cache holds what the game asked about since it last
started one, so every upload adds to what's known, and a player's newer upload replaces only the
records it has. For each record, the newest player's answer wins (for a pushed item, the newest push
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
