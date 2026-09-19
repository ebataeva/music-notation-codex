# Music Theory: Astra Max and Ultra Prompts

Saved from the conversation on 2026-09-16. Prompt blocks preserve the original wording and language. This file stores instructions for later use; saving it does not execute them.

## Recommended sequence

1. **Prompt 1 — Initial theory audit:** the original musical-correctness task. The user reported starting it on Max, although it was initially proposed for Ultra.
2. **Prompt 2 — Max implementation:** add this to the running task for concise UI explanations, an audio dictionary, and modulation guidance.
3. Review the resulting interface.
4. **Prompt 4 — Ultra review:** independently check the completed implementation and fix confirmed problems.

**Prompt 3 is an alternative to Prompt 2, not a subsequent implementation stage.** It covers the same features with additional musical validation. Do not run both implementation prompts sequentially just to repeat the work. Check actual task progress before resuming any stage.

## Prompt 1 — Initial theory audit

```text
Focus on the musical correctness of Theory in music-notation-codex.

Read CONTEXT.md and CLAUDE.md through MCP first, verify the current
implementation, and follow the project's existing GSD workflow.

Audit the connection between actual musical input, harmonic analysis,
preset style policies, and generated explanations across all seven presets.

Check:
- chord tones, scale degrees, accidentals and enharmonic spelling;
- distinctions between natural minor, harmonic minor and Dorian;
- cadences, borrowed chords and ambiguous tonal interpretations;
- whether every explanation is supported by the actual notes;
- whether classical conventions are incorrectly imposed on modal or
  contemporary styles;
- whether transposition preserves the musical meaning.

Build a compact set of independently reasoned musical examples.
Check transposable cases in all 12 tonics. Include counterexamples that
could expose plausible-sounding but incorrect explanations.

Distinguish objective errors from stylistic choices. Verify disputed
theoretical claims against authoritative sources.

Fix up to three of the most consequential reproducible errors and add
meaningful regression tests. If no errors are established, say so.
Show concrete musical examples before and after each fix.

Keep the scope within the theory engine and its tests. Do not create
extra documentation. Finish with results and remaining uncertainties.
```

## Prompt 2 — Astra / Max implementation

```text
Добавь к текущей задаче в music-notation-codex улучшение подачи музыкальной теории.

1. Краткие объяснения в основном UI
Сейчас объяснения громоздкие, непонятные и одинаково начинаются. Перепиши их так, чтобы каждое обычно занимало 1–2 коротких предложения и сразу передавало музыкальную идею: что происходит, какой эффект это создаёт и что можно попробовать.

Привязывай объяснение к реальным нотам, аккордам и выбранному стилю. Убери повторяющиеся вступления и общие фразы. Различия между объяснениями должны следовать из музыки, а не из случайной замены слов синонимами.

2. Отдельная страница Theory Dictionary
Вынеси подробные объяснения терминов на отдельную страницу и добавь переходы к нужным статьям из основного UI.

Для каждого термина:
- простое и короткое определение;
- наглядный нотный пример;
- воспроизводимый аудиопример, соответствующий нотам;
- пояснение, на что обратить внимание при прослушивании.

Начни с терминов, которые уже используются в приложении. Используй существующие средства отображения нот и воспроизведения аудио.

3. Правила модуляции
Добавь понятные правила и примеры переходов между тональностями. Различай модуляцию, краткое отклонение и модальное заимствование.

Объясняй исходную и целевую тональность, способ перехода и признаки утверждения нового центра. Покажи подходящие способы: общий аккорд, доминанта новой тональности, прямой переход. Учитывай стиль: классические рекомендации не должны становиться универсальными запретами.

Свяжи эти правила с существующими советами приложения и словарём.

Соблюдай правила проекта и существующий GSD-процесс. UI и код — на английском, общение со мной — на русском. Проверь краткость и содержательность текстов, переходы в словарь и реальное воспроизведение примеров. Покажи результат на нескольких конкретных музыкальных примерах.
```

## Prompt 3 — Astra / Ultra implementation alternative

```text
Добавь к текущему аудиту music-notation-codex переработку музыкальных объяснений, интерактивный словарь и правила модуляции. Доведи изменения до работающего результата.

Основной UI должен быстро объяснять музыкальную идею. Сейчас тексты громоздкие, непонятные и начинаются одинаково. Сделай их короткими — обычно 1–2 предложения: что происходит в этой музыке, почему это слышно и какой следующий шаг имеет смысл.

Каждое утверждение должно опираться на фактические ноты, аккорды и контекст. Убирай шаблонные вступления. Не создавай искусственное разнообразие случайными синонимами.

Создай отдельную страницу Theory Dictionary с переходами к конкретным терминам из UI. Каждая статья должна соединять:
- понятное определение;
- наглядный нотный пример;
- работающий аудиопример;
- короткую инструкцию «что услышать».

Где сравнение помогает пониманию, используй пару примеров с одним существенным музыкальным различием. Ноты, подписи, объяснение и звучание должны соответствовать друг другу. Начни с терминов, используемых приложением.

Добавь правила модуляции в существующую теоретическую логику и объяснения. Различай установившуюся модуляцию, тонизацию/отклонение, модальное заимствование и неоднозначный тональный центр.

Для каждого предлагаемого перехода объясняй:
- откуда и куда мы переходим;
- какой музыкальный механизм обеспечивает переход;
- что подтверждает новую тональность;
- когда этот приём уместен для выбранного стиля.

Покажи переход через общий аккорд, доминанту новой тональности и прямую модуляцию. Не навязывай функциональную гармонию модальным петлям.

Проверь музыкальную корректность независимыми примерами и контрпримерами: хроматический аккорд без модуляции, краткая тонизация, подтверждённая новая тональность. Проверь сохранение смысла при транспонировании. Спорные теоретические утверждения сверяй с авторитетными источниками; неоднозначные трактовки обозначай явно.

Используй существующие компоненты нот и аудио, соблюдай правила проекта и GSD-процесс. UI и код — на английском, общение со мной — на русском. Проверь работу интерфейса и аудио, добавь необходимые регрессионные тесты и покажи конкретные примеры до и после изменений.
```

## Prompt 4 — Astra / Ultra review after implementation

```text
Проверь результат предыдущей реализации: краткие объяснения в UI,
Theory Dictionary с нотами и аудио, правила модуляции.

Проведи независимую музыкальную и педагогическую проверку:
- соответствуют ли объяснения реальным нотам и звучанию;
- понятны ли они начинающему, нет ли повторяющейся воды;
- корректно ли различаются модуляция, тонизация и модальное заимствование;
- учитывается ли стиль, сохраняется ли смысл при транспонировании;
- работают ли ссылки, нотные примеры и аудио.

Ищи контрпримеры и воспроизводимые ошибки. Исправляй только
подтверждённые проблемы, проверяй исправления тестами.
Не переделывай архитектуру и не добавляй новые функции.
Покажи конкретные примеры найденных проблем и исправлений.
```
