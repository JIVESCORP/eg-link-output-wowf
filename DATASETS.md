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
  `tooltip_scan`), the rank reader's spell descriptions (`rank_scan`) and the words its windows
  showed (`texts`) are the game's text, so each language gets its own file. Names in the other
  datasets are in whatever language the contributing players' clients use; `hunter_pets` files the
  game's words it holds under the client's language.

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
- **Readings are counted** in `character_stats`: each value of each fact keeps how many readings
  gave it, per race, class, level and form, and none is picked over another. Nothing is kept per
  character, day or gear.
- **Readings stay apart** in `rank_scan`: only identical readings merge, so no player's reading
  replaces another's.
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
- `rolls[key]`, a dungeon boss's items that went to a need/greed roll, from the game's loot history
  rather than a loot window. Keyed `encounter:<encounterId>|threshold:<quality>`: the boss encounter
  (the game's encounter ID, as the `encounters` dataset keys it) and the group's loot threshold (2
  Uncommon, 3 Rare, ...). Items under the threshold aren't rolled for, so each threshold has its own
  key. Each has:
  - `kills`: the encounter won in a group with Group Loot or Need before Greed, each confirmed by a
    roll the loot history listed for it;
  - `unconfirmed`: kills won with no roll seen, most likely because nothing at the threshold dropped;
  - `names[locale]`: the encounter's name in that client language;
  - `items[itemId]`: `drops`, `quantity` and `chance`, every item that went to a roll, whoever opened
    the corpse and whatever the roll's outcome;
  - `sources`.

`chance` is the expected number of that item per kill: the share of corpses with loot
((`deaths` - `empty` - `unknown`) / (`deaths` - `unknown`)) times `drops` / `windows`. For a source
with no kill count (nodes, chests, skinning, containers) it is `drops` / `windows`. It is rounded half
up to 4 decimals. With few kills it is rough; the counts are there to judge it.

Under `rolls`, `chance` is `drops` / (`kills` + `unconfirmed`), rounded the same way. A boss's corpse
under `sources` holds only what was left when the player opened it, so in a group a rolled item is
often missing there (another member opened the corpse first); `rolls` doesn't depend on who looted
first. Nothing about who rolled or won is recorded. Counted by EG Link releases from 0.2.21.

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

## rank_scan.&lt;locale&gt;

What the game's descriptions say old ranks of class spells heal, absorb or deal, read by EG Link's rank
reader (EG Link 0.2.34 and later) level by level. WoW Forever cuts the bonus healing or spell damage of
a rank learned far below the character's level, and the game writes a description's numbers for the
character reading it, so each reading keeps the character it was written for.

- `readings[]`, one per reading:
  - `class` (the game's class token, such as `DRUID`), `level`, `talentPoints` (spent; a talent can
    change a description).
  - `stats`: the reader's `level`, `healing`, `spellDamage` (by school, 1 Physical to 7 Arcane),
    `spellHaste`, `rangedHaste` and `attackPower`, as `talent_scan`'s readers have them. `statsAfter`:
    the same, read again at the end, only when the level or the bonus moved during the reading.
  - `descriptions[spellId]`: each rank's description as the game wrote it for the reader.
  - `controls`: the spell IDs among them read as controls, the newest rank the reader's level allows
    of a dozen spells (Fireball, Frostbolt, Heal, Healing Touch, Healing Wave, Holy Light, Lesser
    Heal, Lightning Bolt, Mend Pet, Shadow Bolt, Smite, Wrath), to compare the old ranks with.
  - `sources`: how many players' saved files hold that same reading.
- `listBuilds[clientBuild]`: the builds of the rank lists the readers' addons read (EG Link reads the
  ranks a list made from one build's game files names), with how many saved files read each.

Readings aren't combined as `talent_scan`'s are: none is picked over another, since readers at one
level with different bonuses are what the cut is measured from. Only identical readings merge, adding
their `sources`. They're sorted by class, level, healing, the highest school's spell damage and talent
points. No reading carries the day it was taken.

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

## barber

What a barber offered each race, sex and class (EG Link 0.2.31 and later): the categories, options
and choices of the barber's window, by ID. Game data, about no player. Their names are the client's
(`ChrCustomizationCategory`, `ChrCustomizationOption` and `ChrCustomizationChoice`), so none are here.

- `looks["<race>|<sex>|<class>"]`, keyed by the game's race token (both Skyborne races are `Skyborne`;
  `Scourge` is Undead), sex (`0` male, `1` female) and class token:
  - `sources`; `visits`, every read filed under the look: a visit at the character's own sex, and a
    try-on of the other body type in the chair, filed under that sex, so a look can have visits and
    no character of that sex; `bodyTypes`, how many players' windows offered a change of body type
    (read at the character's own sex only; absent when none).
  - `categories[categoryId]`: `order` (the game's), `chrModelID` and `shapeshiftFormID` (on a druid
    form's category), `subcategory` and `undressModel` (`true` when set), `sources`.
  - `options[optionId]`: `category`, `order` (the game's), `optionType`, `sources`, and
    `choices[choiceId]`: `order` (its place in the list), `swatch1` and `swatch2` (its colour swatches,
    `"rrggbb"`), `sources`, `seen` (the reads that listed it), `locked` (the reads that showed it
    locked, with `lockedText[locale]["<the game's reason>"]`, how many players' games gave each reason)
    and `ineligible` (the reads that showed it ineligible). `locked` and `ineligible` are read at the
    character's own sex only, and absent when 0.

IDs, orders, swatches and flags are facts, so the newest wins; `visits`, `seen`, `locked` and
`ineligible` add up. A choice the game lists only while another is picked (a Skyborne tattoo's colours)
is listed only by reads whose look had that one picked, so a choice's `seen` against its look's `visits`
says how often it was listed, not whether it is offered.

## hunter_pets

What hunters' games recorded about beasts they tamed or cast Beast Lore on, and Beast Training's list
(EG Link 0.2.33 and later). Game data, filed by the beast's creature ID; the beasts', families' and
spells' names are the client's (`creature_details.<locale>` has the beasts'). The only words are the
game's own lines, under the language of the client that showed them.

- `beasts[creatureId]`: `sources`, and
  - `tames`, what a pet tamed from it came with: `sources`, `count` (tames); `levels` (the beast's at
    the cast), `petLevels` (the new pet's), `families` (`CreatureFamily` IDs), `attackSpeed` (its swing
    time in seconds as the game gave it, such as `"2.00"`) and `trainingPoints`
    (`"<pet level>:<total>:<used>"`; an addon before 0.2.33's release wrote `"<pet level>:<total>"`),
    each value with how many tames gave it; `spells[spellId]`, its abilities (`count`, `passive`), and
    `auras[spellId]`, its permanent auras, where a Faster or Slower Attack passive shows (`count`);
    `diet[locale]["<food>"]`, the game's food words with how many tames. A pet that showed no ability
    in its first 30 seconds adds to `count` and to no spell, so `count` above a spell's says how often.
  - `lore`, Beast Lore cast on it: `sources`, `count` (reads), `levels`, and `tameable`, `diet` and
    `abilities` as `[locale]["<the game's line>"]`, how many reads showed each.
- `training[spellId]`, Beast Training's list by pet ability: `level` (the pet level it needs),
  `costs[trainingPoints]` and `families[familyId]` (the pet out when it was read), each with how many
  windows showed it, `sources`. An entry the game gave no spell ID for is left out.

Counts add up; `level` and `passive` are facts, so the newest wins.

## character_stats

What players' own character sheets say about a race, class and level (EG Link 0.2.34 and later; base
melee and ranged crit from 0.2.35): base stats, and how the game turns stats into health, mana, regen,
crit, dodge and attack power, which no client file fully holds. Each reading is the character pane's
numbers at one moment, and only these counts are published: never a character, its gear, its talents
or the day it was read.

- `stats["<race>|<class>|<level>"]`, keyed by the game's race and class tokens (both Skyborne races are
  `Skyborne`; `Scourge` is Undead) and the character's level when read, such as `Skyborne|DRUID|26`:
  - `sources`: how many players' saved files gave a reading.
  - `forms[formId]`: the game's shapeshift form ID, `0` for none (`1` Cat Form, `5` Bear Form, `8`
    Dire Bear Form, `17` a warrior's Battle Stance ...), since a form changes armor, health and attack
    power. Each has `sources`, `readings` (the distinct sheets read), `withTalents` (readings with
    talent points spent), `withAuras` (readings with any aura or debuff on the character; in a form,
    the form's own aura is one) and `facts`.
  - `facts[name][value]`: `count`, how many readings (or pairs of readings, below) gave that value, and
    `withTalents` and `withAuras`, how many of those a talent or an aura could explain (for a pair,
    either reading). A value is a key: the number rounded to 4 decimals with no trailing zeros, such
    as `"0.1025"`, `"4.66"` or `"-20"`. Players' games that read different numbers show as several
    values side by side, each with its count.

From one reading (one count per reading):

| Fact | What it is | Unit |
|---|---|---|
| `strength`, `agility`, `stamina`, `intellect`, `spirit` | the base stat: the game's total less its bonuses (gear, talents, buffs), so a talent adding a percentage doesn't move it | points |
| `critPerAgility`, `dodgePerAgility` | melee crit and dodge per point of agility: what the game says the character's agility gives, over that agility | % per point |
| `spellCritPerIntellect` | spell crit per point of intellect, the same way | % per point |
| `attackPowerPerStrength`, `attackPowerPerAgility` | attack power per point of strength and of agility, the same way | attack power per point |
| `baseDodge`, `baseParry` | the game's dodge and parry less what the game says the character's stats give. Defense skill is not taken out, so a character whose Defense is below level x 5 reads lower | % |
| `baseSpellCrit` | the lowest spell crit of the six magic schools, less what intellect gives | % |
| `attackPowerBase` | the game's base attack power less what all five stats give (negative for some classes, and its own value in a form) | attack power |
| `baseMeleeCrit` | the game's melee crit less what agility gives and 0.04% for each point the main hand's weapon skill sits above or below level x 5. Only from readings that settle the skill: in a form, Feral Combat's skill while the game's glancing-blow range holds it; out of forms, the skill of the main hand weapon's skill line (from its item type, through the client's weapon proficiencies), Unarmed when the hand is empty. Not from a crit of 0 | % |
| `baseRangedCrit` | the same from ranged crit and the ranged slot's skill: Unarmed when the slot is empty or holds an idol, libram, relic or totem; Feral Combat's in a form | % |
| `armorPerAgility` | armor over agility, only from a reading with nothing worn, no aura and no form | armor per point |

From two readings of one character at one level and form, with the same talents and auras and different
totals of the stat (one count per pair):

| Fact | What it is | Unit |
|---|---|---|
| `healthPerStamina` | the difference in health over the difference in stamina; both stamina totals at least 20 | health per point |
| `manaPerIntellect` | the same for mana and intellect; both intellect totals at least 20 | mana per point |
| `regenPerSpirit` | the same for mana regen (the game's regen while not casting) and spirit | mana per second per point |
| `rangedAttackPowerPerAgility` | the same for ranged attack power and agility | attack power per point |

From one reading and the form's agreed rate (one count per reading). The agreed rate is the value of
the pair fact above most pairs in that form gave (on a tie, the smallest); a form with no pair of its
own takes the value most pairs in the key's other forms gave.

| Fact | What it is | Unit |
|---|---|---|
| `baseHealth` | health less the first 20 stamina at 1 each and the rest at `healthPerStamina` | health |
| `baseMana` | mana less the first 20 intellect at 1 each and the rest at `manaPerIntellect` | mana |
| `baseRegen` | mana regen less spirit at `regenPerSpirit` | mana per second |
| `rangedAttackPowerBase` | ranged attack power less agility at `rangedAttackPowerPerAgility` | attack power |

A reading without its race, class, level or all five stats is left out. A fact a reading can't give
(no mana, no ranged attack power, an unsettled weapon skill) is left out of it, so a one-reading
fact's counts can add up to fewer than `readings`.

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
