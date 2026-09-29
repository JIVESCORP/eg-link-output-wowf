# Datasets

Every file under `data/` is written by Efficient Games' processing job, which runs once a day and
commits only when something changed. Don't edit them by hand: the next run replaces them.

## Layout

```
data/index.json                                   every product, build and dataset, with counts
data/<product>/<clientBuild>/<dataset>.json       one file per dataset that has records
```

- `<product>` is the Battle.net product code of the client the data came from. World of Warcraft:
  Forever's beta is `wow_classic_beta`. The live game gets its own code when it launches on
  4 November 2026.
- `<clientBuild>` is the client's version, such as `1.60.1.70009`. A build's data is only what
  players recorded on that build, so compare builds to see what a patch changed.

Every file is UTF-8 JSON with one space of indent. Object keys are sorted: numerically when every
key is a number, otherwise alphabetically. A field with nothing to say is left out, never `null`.

Each dataset file starts with a `meta` block:

| Field | Meaning |
|---|---|
| `dataset`, `product`, `clientBuild` | what the file is |
| `schemaVersion` | the file's shape; it changes only when a field changes meaning or is removed |
| `sources` | how many players' saved files (a game account on one computer) contributed |
| `combatLogUploads` | `creatures` only: how many combat-log uploads contributed |
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

- `described[questId]`: `title`, and how many players' scans got it (`sources`).
- `noData`: quests some scan asked about and none got an answer for.
