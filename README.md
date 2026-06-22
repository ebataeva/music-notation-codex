# music-notation-codex

Локальный workflow для генерации виолончельных партий в MusicXML и MIDI, с жанровыми пресетами и подсказками по гармоническому развитию.

## Что внутри

- `scripts/generate_cello_dark_ostinato.py` — генерирует 8-тактовые виолончельные остинато в разных жанрах.
- `scripts/harmony_advisor.py` — подсказывает гармонические ходы, модуляции и приемы для загадочности, драйва и сексуального напряжения.
- `scores/musicxml/` — MusicXML-файлы для MuseScore.
- `scores/midi/` — MIDI-файлы для Ableton.
- `scores/pdf/` — место для PDF-экспорта из MuseScore.
- `references/` — место для референсов, набросков и материалов.

## Установка

Из папки проекта:

```bash
cd /Users/ebataeva/wp2/music-notation-codex
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Если `.venv` уже создано, достаточно:

```bash
cd /Users/ebataeva/wp2/music-notation-codex
source .venv/bin/activate
```

## Генерация MusicXML и MIDI

Базовый вариант:

```bash
python scripts/generate_cello_dark_ostinato.py
```

Посмотреть доступные жанры:

```bash
python scripts/generate_cello_dark_ostinato.py --list-genres
```

Сгенерировать конкретный жанр:

```bash
python scripts/generate_cello_dark_ostinato.py --genre ritual_tribal
python scripts/generate_cello_dark_ostinato.py --genre noir_slow_burn
python scripts/generate_cello_dark_ostinato.py --genre driving_cinematic
python scripts/generate_cello_dark_ostinato.py --genre dark_trip_hop
```

Задать имя выходного файла:

```bash
python scripts/generate_cello_dark_ostinato.py --genre driving_cinematic --output-name cello_drive_take_01
```

Скрипт сохраняет:

- `scores/musicxml/<output-name>.musicxml`
- `scores/midi/<output-name>.mid`

## Доступные жанры

- `dark_trip_hop` — темный, сексуальный, петлевой trip-hop groove.
- `ritual_tribal` — ритуальный пульс, больше акцентов и телесного движения.
- `noir_slow_burn` — медленный нуар, недосказанность, напряженная пауза.
- `driving_cinematic` — быстрый кинематографичный мотор, драйв и нарастание.

## Подсказки по гармонии, модуляциям и настроению

Посмотреть жанры помощника:

```bash
python scripts/harmony_advisor.py --list-genres
```

Получить идеи для жанра:

```bash
python scripts/harmony_advisor.py --genre dark_trip_hop
python scripts/harmony_advisor.py --genre ritual_tribal
python scripts/harmony_advisor.py --genre noir_slow_burn
python scripts/harmony_advisor.py --genre driving_cinematic
```

Помощник объясняет:

- какие гармонические прогрессии можно попробовать;
- как сделать модуляцию;
- чем добавить загадочность;
- чем добавить драйв;
- чем добавить сексуальное напряжение;
- почему каждый прием работает музыкально.

## Как открыть MusicXML в MuseScore

1. Открой MuseScore.
2. Выбери `File -> Open`.
3. Открой файл из `scores/musicxml/`.
4. При необходимости экспортируй PDF через `File -> Export`.

## Как импортировать MIDI в Ableton

1. Открой Ableton Live.
2. Перетащи `.mid` файл из `scores/midi/` на MIDI-трек.
3. Назначь виолончельный инструмент или любой басовый/струнный звук.
4. Включи loop для клипа, если хочешь использовать остинато как повторяющийся грув.

## Как менять музыку в коде

Открой `scripts/generate_cello_dark_ostinato.py`.

- Жанры описаны в словаре `GENRE_PRESETS`.
- Тональность меняется через `key_tonic` и `key_mode`.
- Темп меняется через `tempo_bpm`.
- Размер меняется через `meter_signature`.
- Ноты меняются в `bars`.
- Ритм меняется в `rhythm`.
- Динамическая сила MIDI меняется через `velocity`.

Важно: сумма длительностей в каждом такте должна соответствовать размеру. Для 4/4 это `4.0`. Например, восемь восьмых нот — это `[0.5] * 8`, а шестнадцать шестнадцатых — `[0.25] * 16`.

Все текущие партии одноголосные, без невозможных двойных нот, в рабочем регистре виолончели.
