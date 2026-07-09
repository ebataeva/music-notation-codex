# Research Plan: Style-Aware Harmony Policy for 7 Presets

Date: 2026-07-08
Project: music-notation-codex
Branch: blog-theory-explainer

## Objective

Заменить generic-фразы в TheoryExplainer на note-specific, preset-aware гармонические обоснования. Для этого — исследовать современный гармонический язык для каждого из 7 пресетов и синтезировать policy-слой.

## Пресеты

### Solo (виолончель соло)

| Пресет | Тональность | BPM | Характер |
|---|---|---|---|
| `dark_trip_hop` | C minor | 72 | тёмный, сексуальный, loopy groove |
| `ritual_tribal` | D minor | 88 | ритуальный пульс, телесное движение |
| `noir_slow_burn` | A minor | 58 | медленный нуар, напряжённая пауза |
| `driving_cinematic` | C minor | 104 | быстрый кинематографичный мотор |

### Duet (виолончель + скрипка)

| Пресет | Тональность | BPM | Характер |
|---|---|---|---|
| `sexy_duet` | D minor | 76 | классический «sexy» дуэт |
| `simple_sexy_duet` | D minor | 64 | упрощённая версия |
| `dorian_sexy_duet` | D minor, Dorian | 88 | D Dorian vamp (Dm9 → G9) |

## Методология исследования

### Источники (в порядке приоритета)

1. **Web search** — по каждому жанру цепочка запросов (см. ниже)
2. **Анализ нотного текста** в `mood_presets.py` — из `bars` и `duet_bars` извлекаются реальные гармонические последовательности
3. **MusicXML-файлы** в `scores/musicxml/` — для верификации вывода

### Web search запросы

#### dark_trip_hop
- "trip hop chord progressions minor harmony"
- "Portishead Massive Attack harmonic analysis"
- "trip hop bass movement typical chord changes"
- "dark trip hop cello ostinato harmony"

#### ritual_tribal
- "tribal ostinato harmony modal Phrygian"
- "world music cello ostinato harmony ritual"
- "dark ritual chord progression bass riff"
- "Phrygian mode bass riff dark harmony"

#### noir_slow_burn
- "film noir harmony minor jazz chord progression"
- "noir soundtrack harmonic language slow burn"
- "jazz minor harmony tension building chord voicing"

#### driving_cinematic
- "cinematic minor ostinato harmony film score"
- "Hans Zimmer style harmonic language driving bass"
- "epic trailer music chord progression minor"

#### sexy_duet / simple_sexy_duet
- "sexy minor key chord progression D minor"
- "D minor sensual harmony cello violin duet"
- "sultry duet harmony pop"

#### dorian_sexy_duet
- "D Dorian vamp harmony Dm9 G9"
- "Dorian mode minor 9th chord progression"
- "warm Dorian harmony sensual"

### Формат вывода для каждого пресета

```yaml
preset: <name>
key: <tonic mode>
modal_center: <Aeolian/Dorian/Phrygian/etc.>
core_chords:
  - <chord>: <role description, why it works>
bass_pattern: <описание басового движения>
chromatic_approaches: <passing tones, semitone slides, tension notes>
cadences: <preferred cadence types, avoided cadences>
texture: <описание фактуры, ритмического рисунка>
```

## План имплементации

1. **Research** — 5 параллельных sub-agent'ов (4 solo + 1 duet)
2. **Синтез** — свести результаты в единый style policy
3. **Создать** `core/presets/style_policy.py` — маппинг пресет → гармонические правила
4. **Переписать** `core/theory/explainer.py` — читать policy, выдавать note-specific тексты
5. **Заполнить** пустые `progressions`/`modulations`/`mood_tips` для дуэтов в `mood_presets.py`
6. **Тесты** — минимум 1 конкретный пример на пресет в `test_theory_explainer.py`

## Критические файлы

- `core/presets/mood_presets.py` — source data
- `core/theory/explainer.py` — main target
- `core/engine/loop_engine.py` — generator
- `core/presets/registry.py` — preset access
- `core/models.py` — data models
- `tests/test_theory_explainer.py` — existing tests
