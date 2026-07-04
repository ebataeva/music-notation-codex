# Phase 2: LoopEngine + ExportEngine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-04
**Phase:** 02-loopengine-exportengine
**Areas discussed:** Seed-политика, API движка, Политика экспорта, Обёртка + ревью-фиксы

---

## Seed-политика

| Option | Description | Selected |
|--------|-------------|----------|
| Плюмбинг сейчас | Движок принимает seed, создаёт random.Random(seed), передаёт стратегиям — интерфейс не меняется в 2.5 | ✓ |
| Только seed в trace | RNG появится в фазе 2.5, сейчас только запись в trace | |
| Реши сам | Отдать на планирование | |

**User's choice:** Плюмбинг сейчас (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Сгенерить и записать | При отсутствии seed движок сам генерирует и всегда пишет в trace (никогда None) | ✓ |
| seed=None допустим | Без seed — без фиксации, в trace None | |
| Фиксированный дефолт | seed=0 по умолчанию | |

**User's choice:** Сгенерить и записать (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Параметр движка | seed — опциональный аргумент метода генерации | |
| Поле в GenerationRequest | seed добавляется в дата-класс запроса | |
| Реши сам | Отдать на планирование | ✓ |

**User's choice:** Реши сам

| Option | Description | Selected |
|--------|-------------|----------|
| Нет, только в библиотеке | Скрипт максимально тонкий | |
| Да, добавить --seed | Опциональный флаг, дефолт не меняется, golden-тесты целы | ✓ |

**User's choice:** Да, добавить --seed

| Option | Description | Selected |
|--------|-------------|----------|
| Честный полный trace | pattern_strategy + register_choices + chord_tones_used из реальных нот пресета по-тактово | ✓ |
| Минимальный trace | Только seed и pattern_strategy, остальное None до 2.5 | |

**User's choice:** Честный полный trace (Recommended)

---

## API движка

| Option | Description | Selected |
|--------|-------------|----------|
| Два уровня API | build_score() → Score (низкий) + generate_variant() → LoopVariant с trace (высокий) | ✓ |
| Только Score | LoopVariant собирает вызывающий код | |
| Только LoopVariant | Один метод, но противоречит критерию успеха | |

**User's choice:** Два уровня API (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Классы по ROADMAP | LoopEngine/ExportEngine как классы | |
| Модульные функции | Стиль фазы 1 | |
| Реши сам | Отдать на планирование | ✓ |

**User's choice:** Реши сам

| Option | Description | Selected |
|--------|-------------|----------|
| Внутри движка | Валидаторы вызываются при сборке Score — LOOP-03/04 автоматически | ✓ |
| Отдельный шаг | Явный отдельный вызов валидации | |
| Реши сам | Отдать на планирование | |

**User's choice:** Внутри движка (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Исправить пресет + новый baseline | A1 → A2, переснять golden-хеши | |
| Пер-пресетное исключение | Движок пропускает известные легаси-отклонения с предупреждением в trace; вывод байт-идентичен | ✓ |
| Реши сам | Отдать на планирование | |

**User's choice:** Пер-пресетное исключение (Recommended)

---

## Политика экспорта

| Option | Description | Selected |
|--------|-------------|----------|
| Конфигурируемая база | Базовая директория с дефолтом scores/, внутри musicxml/ и midi/ | ✓ |
| Жёсткие пути как сейчас | Минимальный рефакторинг | |
| Реши сам | Отдать на планирование | |

**User's choice:** Конфигурируемая база (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Только пути в фазе 2 | *_bytes остаются None до фаз 5-6 | ✓ |
| Пути + midi_bytes | Задел на фазу 5 | |
| Реши сам | Отдать на планирование | |

**User's choice:** Только пути в фазе 2 (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Молча перезаписывать | Текущее поведение, воспроизводимость по seed | ✓ |
| Уникальные имена | timestamp/seed в имени — ломает golden-тесты | |

**User's choice:** Молча перезаписывать (Recommended)

---

## Обёртка + ревью-фиксы

| Option | Description | Selected |
|--------|-------------|----------|
| Только dark_ostinato | Строго по цели фазы | |
| Все 4 генератора | Дуэтные скрипты тоже становятся обёртками | ✓ |

**User's choice:** Все 4 генератора

| Option | Description | Selected |
|--------|-------------|----------|
| WR-01: дуэты в solo CLI | Фильтр CLI-choices до solo-пресетов | ✓ |
| WR-04: запись ~/.music21rc | environment.Environment() вместо UserSettings() | ✓ |
| WR-02/03: дыры валидаторов | Октава обязательна, ValueError-контракт, положительные длительности | ✓ |
| Отложить все | Чистый рефакторинг без фиксов | |

**User's choice:** WR-01 + WR-04 + WR-02/03 (multiselect, все три фикса)

| Option | Description | Selected |
|--------|-------------|----------|
| Только argparse + вызов | Никакой music21-логики в scripts/ | ✓ |
| Скрипты удалить | Противоречит критерию идентичного вывода | |

**User's choice:** Только argparse + вызов (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Внутренний путь без публичного API | Двухголосная сборка в core, но generate_variant() cello-only | ✓ |
| InstrumentSet в API сразу | Проектирование v2-фичи в v1-фазе | |
| Реши сам | Отдать на планирование | |

**User's choice:** Внутренний путь без публичного API (Recommended)

---

## Claude's Discretion

- Где живёт seed в API (параметр метода vs поле GenerationRequest)
- Классы vs модульные функции для LoopEngine/ExportEngine
- Оформление механизма пер-пресетных легаси-исключений и идентификатора стратегии

## Deferred Ideas

- WR-05 (ложная иммутабельность frozen MoodPreset) — не выбран для этой фазы
- Дуэтная генерация как публичная фича (InstrumentSet) — v2 (DUET-01)
- harmony_advisor.py — фаза 3 (TheoryExplainer)
- Уникальные имена файлов / история экспортов — фаза 10 (Loop Library)
