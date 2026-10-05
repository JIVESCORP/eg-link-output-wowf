# EG Link output: World of Warcraft: Forever

Open data about **World of Warcraft: Forever**, compiled by [Efficient Games](https://efficient.games)
from the game's own data and from what players' **EG Link** addon records as they play. Examples
are quests, profession trainers and the ranks recipes are learned at, and where things are on the
map.

## Datasets

Each client build gets a folder, `data/<product>/<clientBuild>/`, holding what players recorded on
that build. The last four datasets come from the game's caches of the server's answers, one file per
client language (`quests.enUS.json`):

| Dataset | What it holds |
|---|---|
| `vendors` | Every vendor: where it stands, what it sells, stock limits, and prices at each standing |
| `trainers` | Every trainer: where it stands, what it teaches, the level and skill each needs, and prices |
| `npcs` | Every NPC and object with a window: what it offers (quests given and ended, gossip, services), levels, where it is; and objects walked up to, such as herbs and veins |
| `flights` | Flight masters' flight points, and every route's stops, prices, flight times and landing spots |
| `loot` | Loot and kill totals per creature, node, chest and container, with each item's drop chance |
| `creatures` | Creatures' levels, classifications, reactions, where they die, the XP and reputation a kill pays, and, from combat logs, their spells, health and melee hits |
| `turn_ins` | What each quest's turn-in paid: XP, money and reputation |
| `objectives` | Where each quest objective's count went up |
| `quest_scan` | Which quests the server describes (open content) and which it doesn't yet |
| `game_rules` | Game rules no client file holds: where new characters start, where class teleports land, the level cap, standing ranges, renown tracks, quest colours, reward spell flags and profession skill caps |
| `quests.<locale>` | Every quest as the server describes it: text, levels, objectives, rewards |
| `creature_details.<locale>` | Every creature's name, title, type, family, rank, models and quest drops |
| `object_details.<locale>` | Every game object's name, type, model, size and quest drops |
| `item_hotfixes.<locale>` | Items the server sent, removed or withheld, with the names the client files lack |

`data/index.json` lists every product, build and dataset with its record count. [DATASETS.md](DATASETS.md)
documents every field and how players' contributions are combined.

## License

The data in this repository is licensed under
[Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE). You may use it for anything,
including commercial and closed-source projects, as long as you give credit. Please credit it as:

> Data from [Efficient Games](https://efficient.games), licensed under
> [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Say so if you changed the data.

## Game content

World of Warcraft, Warcraft and Blizzard Entertainment are trademarks or registered trademarks of
Blizzard Entertainment, Inc. Game content in these datasets, such as names and in-game text, is the
property of Blizzard Entertainment and is included for reference. The license above covers Efficient
Games' own contribution: the selection, structure, compilation and player-contributed observations.
It grants no rights in Blizzard's content.

This project is not affiliated with or endorsed by Blizzard Entertainment. To request removal of
content, contact [legal@efficient.games](mailto:legal@efficient.games).

## Personal data

These datasets contain no personal data. Player contributions are stripped of account, character
and machine details before they leave the player's computer, and only aggregated results are
published here.
