"""MOOD_PRESETS registry: merged data from all 5 pre-existing CLI scripts.

Source of truth for Phase 2's LoopEngine and Phase 3's TheoryExplainer
(ARCHITECTURE.md Pattern 2). Data below is migrated verbatim (character-for-
character, including Russian text) from:

- scripts/generate_cello_dark_ostinato.py (GENRE_PRESETS: tempo/key/rhythm/bars/feel
  for 4 solo moods)
- scripts/harmony_advisor.py (GENRE_IDEAS: progressions/modulations/mood -> mood_tips
  for the same 4 moods)
- scripts/generate_sexy_duet_loop.py, generate_simple_sexy_duet_loop.py,
  generate_dorian_sexy_duet_loop.py (3 standalone duet presets, each with
  per-instrument duet_rhythm/duet_bars)

This is a data-only move: validators (Plan 02) are not wired into any
generation path yet, so pre-existing out-of-range notes migrate verbatim,
not silently fixed (see the "A1" note below).
"""

from __future__ import annotations

from core.models import MoodPreset

MOOD_PRESETS: dict[str, MoodPreset] = {
    "dark_trip_hop": MoodPreset(
        name="dark_trip_hop",
        tempo_bpm=72,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=76,
        rhythm=(0.5,) * 8,
        bars=(
            ("C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"),
            ("C2", "C2", "G2", "Bb2", "C3", "Bb2", "G2", "Eb2"),
            ("Ab2", "Ab2", "Eb3", "G3", "Ab3", "G3", "Eb3", "C3"),
            ("G2", "G2", "D3", "F3", "G3", "F3", "D3", "Bb2"),
            ("C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"),
            ("Eb2", "Eb2", "Bb2", "C3", "Eb3", "C3", "Bb2", "G2"),
            ("F2", "F2", "C3", "Eb3", "F3", "Eb3", "C3", "Ab2"),
            ("G2", "G2", "D3", "F3", "G3", "F3", "D3", "C2"),
        ),
        feel="dark, sexy, loopy trip-hop groove",
        progressions=(
            "i - VI - v - i: C minor -> Ab -> G minor -> C minor. Работает, потому что низкая тоника держит гипноз, VI дает темное тепло, v возвращает без слишком яркого классического разрешения.",
            "i - bVII - VI - V: C minor -> Bb -> Ab -> G. Работает как спуск вниз: ощущение соблазна, опасности и неизбежного возврата.",
        ),
        modulations=(
            "Через общий аккорд: C minor -> Eb major. Eb major является относительным мажором, поэтому переход мягкий, но свет становится холоднее и кинематографичнее.",
            "Через доминанту: C minor -> G minor. Повтори D или G в басу, затем закрепи G minor. Это дает ощущение темного поворота без разрушения грува.",
        ),
        mood_tips=(
            "Загадочность: добавь b2 или натуральную 7 ступень как проходящую ноту, например Db или B в C minor. Эти звуки слегка конфликтуют с ладом и создают тень.",
            "Секси-эффект: оставь устойчивый низкий пульс, а верхние ноты двигай хроматически на полтона. Полутон звучит телесно и напряженно, потому что ухо ждет разрешения.",
            "Драйв: укороти длительности до шестнадцатых и повторяй опорную ноту между движущимися нотами. Повтор дает мотор, движение нот дает направление.",
        ),
    ),
    "ritual_tribal": MoodPreset(
        name="ritual_tribal",
        tempo_bpm=88,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=88,
        rhythm=(0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5),
        bars=(
            ("D2", "D2", "A2", "D3", "C3", "A2", "F2"),
            ("D2", "D2", "A2", "F3", "E3", "C3", "A2"),
            ("Bb2", "Bb2", "F3", "E3", "D3", "A2", "F2"),
            ("C3", "C3", "G2", "Bb2", "A2", "F2", "D2"),
            ("D2", "D2", "A2", "D3", "C3", "A2", "F2"),
            ("F2", "F2", "C3", "F3", "E3", "C3", "A2"),
            ("G2", "G2", "D3", "F3", "E3", "C3", "Bb2"),
            ("A2", "A2", "E3", "G3", "F3", "E3", "D2"),
        ),
        feel="ritual pulse with accents, more body and movement",
        progressions=(
            "i - bVII - i - bVI: D minor -> C -> D minor -> Bb. Работает как круговой обряд: тоника возвращается часто, а соседние ступени дают первобытное качание.",
            "i - iv - bVII - i: D minor -> G minor -> C -> D minor. Хорошо для телесного, танцевального движения без попсовой сладости.",
        ),
        modulations=(
            "Смести центр на кварту: D minor -> G minor. Держи D как общий звук, затем сделай G новой опорой. Это звучит естественно для струнных и усиливает ритуальность.",
            "Параллельная окраска: D minor -> D Phrygian. Замени E на Eb. Модуляция почти незаметная, но сразу появляется древний, опасный оттенок.",
        ),
        mood_tips=(
            "Загадочность: используй фригийскую b2 ступень. В D это Eb. Она работает, потому что полутон над тоникой звучит как запретная дверь рядом с домом.",
            "Драйв: ставь акценты не только на 1 и 3, а на 1, последнюю восьмую 2-й доли и 4. Сдвинутый акцент создает племенной толчок.",
            "Секси-эффект: чередуй сухой низкий пульс и мягкий ответ выше на кварту/квинту. Контраст тела и ответа создает разговорность.",
        ),
    ),
    "noir_slow_burn": MoodPreset(
        name="noir_slow_burn",
        tempo_bpm=58,
        key_tonic="A",
        key_mode="minor",
        meter_signature="4/4",
        velocity=68,
        rhythm=(1.0, 0.5, 0.5, 1.0, 1.0),
        bars=(
            ("A2", "E3", "G3", "C3", "B2"),
            ("A2", "E3", "G3", "C3", "D3"),
            ("F2", "C3", "E3", "A2", "G2"),
            ("E2", "B2", "D3", "G2", "A2"),
            ("A2", "E3", "G3", "C3", "B2"),
            ("C3", "G2", "Bb2", "Eb3", "D3"),
            ("F2", "C3", "E3", "A2", "G2"),
            ("E2", "B2", "D3", "G2", "A2"),
        ),
        feel="slow noir, unspoken tension, held pause",
        progressions=(
            "i - iv - bVI - V: A minor -> D minor -> F -> E. Работает как noir: минорная тягучесть, затем яркая доминанта E просит разрешения.",
            "i - bVI - iiø - V: A minor -> F -> B half-diminished -> E. Это более джазовый путь, сразу появляется дымная неопределенность.",
        ),
        modulations=(
            "A minor -> C major через общий аккорд Am/C. Это даст холодное просветление без потери меланхолии.",
            "A minor -> C minor через хроматическое понижение E до Eb. Это резкий noir-поворот: знакомый материал внезапно темнеет.",
        ),
        mood_tips=(
            "Загадочность: оставляй паузы после напряженных нот. Пауза работает, потому что слушатель сам достраивает угрозу.",
            "Секси-эффект: используй медленные нисходящие полутона, например C -> B -> Bb -> A. Нисходящий хроматизм звучит как выдох и притяжение.",
            "Драйв без ускорения: добавь ghost-notes на слабые доли. Темп остается медленным, но внутри появляется нерв.",
        ),
    ),
    "driving_cinematic": MoodPreset(
        name="driving_cinematic",
        tempo_bpm=104,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=94,
        rhythm=(0.25,) * 16,
        bars=(
            ("C2", "G2", "C3", "G2", "C2", "G2", "Eb3", "G2", "C2", "G2", "C3", "G2", "Bb2", "G2", "Eb2", "G2"),
            ("C2", "G2", "C3", "G2", "C2", "G2", "F3", "G2", "C2", "G2", "Eb3", "G2", "Bb2", "G2", "C3", "G2"),
            ("Ab2", "Eb3", "Ab3", "Eb3", "Ab2", "Eb3", "G3", "Eb3", "Ab2", "Eb3", "F3", "Eb3", "C3", "Eb3", "Ab2", "Eb3"),
            ("G2", "D3", "G3", "D3", "G2", "D3", "F3", "D3", "G2", "D3", "Eb3", "D3", "Bb2", "D3", "G2", "D3"),
            ("C2", "G2", "C3", "G2", "C2", "G2", "Eb3", "G2", "C2", "G2", "C3", "G2", "Bb2", "G2", "Eb2", "G2"),
            ("Eb2", "Bb2", "Eb3", "Bb2", "Eb2", "Bb2", "G3", "Bb2", "Eb2", "Bb2", "F3", "Bb2", "C3", "Bb2", "G2", "Bb2"),
            ("F2", "C3", "F3", "C3", "F2", "C3", "Ab3", "C3", "F2", "C3", "Eb3", "C3", "Ab2", "C3", "F2", "C3"),
            ("G2", "D3", "G3", "D3", "G2", "D3", "F3", "D3", "G2", "D3", "Eb3", "D3", "C3", "G2", "C2", "G2"),
        ),
        feel="fast cinematic motor, drive and build",
        progressions=(
            "i - bVI - bVII - i: C minor -> Ab -> Bb -> C minor. Работает эпично: bVI дает масштаб, bVII поднимает энергию без слишком классического V-I.",
            "i - iv - VI - V: C minor -> F minor -> Ab -> G. Более драматично, потому что V создает сильное ожидание возврата.",
        ),
        modulations=(
            "C minor -> Eb minor через общий тон Eb. Это темный кинематографичный скачок: общий звук связывает, новая тональность пугает.",
            "C minor -> D minor секвенцией: подними весь остинатный рисунок на тон. Это простой способ усилить сцену без сложной теории.",
        ),
        mood_tips=(
            "Драйв: держи pedal tone, например C или G, между каждой движущейся нотой. Pedal tone фиксирует землю, а верхнее движение разгоняет мотор.",
            "Загадочность: перед сменой гармонии вставь чужую ноту на слабую долю. Она мелькает и исчезает, поэтому интригует, но не ломает лад.",
            "Секси-эффект: добавь синкопу перед сильной долей. Тело слышит ожидание удара, а задержка делает грув более липким.",
        ),
    ),
    # Duet presets below have no GENRE_IDEAS-equivalent theory data source, so
    # progressions/modulations/mood_tips stay empty (no fabricated theory text).
    # rhythm/bars/tempo_bpm mirror the duet_* fields for schema consistency
    # since duet scripts have no separate solo-cello-only data.
    "sexy_duet": MoodPreset(
        name="sexy_duet",
        tempo_bpm=76,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=82,
        rhythm=(),
        bars=(),
        feel="",
        progressions=(),
        modulations=(),
        mood_tips=(),
        duet_rhythm={
            "cello": (0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5),
            "violin": (1.0, 0.5, 0.5, 1.0, 1.0),
        },
        duet_bars={
            "cello": (
                ("D2", "A2", "D3", "C3", "A2", "F2", "A2"),
                ("D2", "A2", "F3", "E3", "C3", "A2", "F2"),
                ("Bb2", "F3", "A3", "G3", "F3", "D3", "Bb2"),
                ("A2", "E3", "G3", "F3", "E3", "C#3", "D2"),
                ("D2", "A2", "D3", "C3", "A2", "F2", "A2"),
                ("F2", "C3", "E3", "D3", "C3", "A2", "F2"),
                ("G2", "D3", "F3", "E3", "D3", "Bb2", "G2"),
                ("A2", "E3", "G3", "F3", "E3", "C#3", "D2"),
            ),
            "violin": (
                ("A4", "C5", "D5", "F5", "E5"),
                ("A4", "C5", "E5", "D5", "C5"),
                ("Bb4", "D5", "F5", "E5", "D5"),
                ("A4", "C#5", "E5", "G5", "F5"),
                ("A4", "C5", "D5", "F5", "E5"),
                ("C5", "A4", "D5", "E5", "F5"),
                ("Bb4", "D5", "G5", "F5", "E5"),
                ("A4", "C#5", "E5", "G5", "D5"),
            ),
        },
        duet_tempo_bpm=76,
    ),
    "simple_sexy_duet": MoodPreset(
        name="simple_sexy_duet",
        tempo_bpm=64,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=68,
        rhythm=(),
        bars=(),
        feel="",
        progressions=(),
        modulations=(),
        mood_tips=(),
        duet_rhythm={
            "cello": (1.0, 1.0, 1.0, 1.0),
            "violin": (1.0, 1.0, 1.0, 1.0),
        },
        duet_bars={
            "cello": (
                ("D2", "A2", "D3", "E3"),
                # NOTE: "A1" (MIDI 33) is below the C2 validator floor — pre-existing
                # in source script, migrated verbatim, not yet validated at
                # generation time (Phase 2 concern).
                ("A1", "E2", "G2", "C#3"),
                ("D2", "A2", "D3", "E3"),
                ("A1", "E2", "G2", "C#3"),
                ("D2", "A2", "F2", "E2"),
                ("A1", "E2", "G2", "C#3"),
                ("D2", "A2", "D3", "E3"),
                ("A1", "E2", "G2", "C#3"),
            ),
            "violin": (
                ("F4", "E4", "D4", "E4"),
                ("E4", "G4", "C#5", "Bb4"),
                ("F4", "E4", "D4", "A4"),
                ("G4", "E4", "C#4", "D4"),
                ("A4", "F4", "E4", "D4"),
                ("E4", "G4", "C#5", "Bb4"),
                ("F4", "E4", "D4", "E4"),
                ("C#4", "E4", "G4", "D4"),
            ),
        },
        duet_tempo_bpm=64,
    ),
    "dorian_sexy_duet": MoodPreset(
        name="dorian_sexy_duet",
        tempo_bpm=88,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=74,
        rhythm=(),
        bars=(),
        feel="D Dorian vamp: Dm9 -> G9. The B natural keeps it warm instead of funeral-dark.",
        progressions=(),
        modulations=(),
        mood_tips=(),
        duet_rhythm={
            "cello": (0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5),
            "violin": (0.5, 0.5, 1.0, 0.5, 0.5, 1.0),
        },
        duet_bars={
            "cello": (
                ("D2", "A2", "D3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "A2", "G2"),
                ("D2", "A2", "D3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "A2", "G2"),
                ("D2", "A2", "C3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "C3", "B2"),
                ("D2", "A2", "D3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "A2", "D2"),
            ),
            "violin": (
                ("A4", "B4", "C5", "B4", "A4", "F4"),
                ("G4", "A4", "B4", "A4", "G4", "E4"),
                ("A4", "B4", "C5", "B4", "A4", "F4"),
                ("G4", "A4", "B4", "C5", "B4", "A4"),
                ("F4", "A4", "B4", "A4", "F4", "E4"),
                ("G4", "A4", "B4", "A4", "G4", "E4"),
                ("A4", "B4", "C5", "B4", "A4", "F4"),
                ("G4", "A4", "B4", "A4", "F4", "D4"),
            ),
        },
        duet_tempo_bpm=88,
    ),
}
