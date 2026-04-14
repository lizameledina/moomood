"""
Текстовая аналитика для Telegram: компактный график, связи и инсайты.
Выводы показываются только если данных достаточно и разница заметна.
"""

from __future__ import annotations

from html import escape
from statistics import median
from typing import Any, List, Optional, Sequence, Tuple

TAG_LABELS = {
    "work": "Работа",
    "sport": "Спорт",
    "friends": "Друзья",
    "relax": "Отдых",
    "study": "Учёба",
    "family": "Семья",
    "health": "Здоровье",
    "walk": "Прогулка",
    "hobby": "Хобби",
    "home": "Дом",
    "trips": "Поездки",
    "children": "Дети",
}

ANALYTICS_TAGS = (
    "work",
    "sport",
    "friends",
    "relax",
    "study",
    "family",
    "health",
    "walk",
    "hobby",
    "home",
    "trips",
    "children",
)

MIN_RECORDS_INSIGHTS = 5
MIN_RECORDS_RELATIONS = 5
MIN_PER_GROUP = 2
TAG_MIN_DAYS = 2
MOOD_DIFF_NOTICE = 0.35
STRESS_DIFF_NOTICE = 0.6


def _row_metric(row: Any, metric: str) -> float:
    if metric == "m":
        return float(row["mood"])
    if metric == "e":
        return float(row["energy"])
    if metric == "r":
        return float(row["stress"])
    if metric == "h":
        return float(row["sleep"])
    raise ValueError(metric)


def _fmt_value(metric: str, value: float) -> str:
    if metric == "h":
        return f"{value:.1f} ч."
    if metric == "m":
        return f"{value:.1f}/5"
    return f"{value:.1f}/10"


def _avg_metric(rows: Sequence[Any], metric: str) -> float:
    if not rows:
        return 0.0
    return sum(_row_metric(row, metric) for row in rows) / len(rows)


def _parse_tags(tags: Optional[str]) -> set[str]:
    if not tags:
        return set()
    return {tag.strip() for tag in tags.split(",") if tag.strip()}


def _tag_label(tag: str) -> str:
    return TAG_LABELS.get(tag, tag)


def _split_by_median(rows: List[Any], key: str) -> Tuple[List[Any], List[Any], float]:
    values = sorted(float(row[key]) for row in rows)
    pivot = float(median(values))
    higher = [row for row in rows if float(row[key]) >= pivot]
    lower = [row for row in rows if float(row[key]) < pivot]
    return higher, lower, pivot


METRIC_TITLE = {
    "m": "Настроение",
    "e": "Энергия",
    "r": "Стресс",
    "h": "Сон",
}

PERIOD_TITLE = {
    "7": "Последние 7 дней",
    "30": "Последние 30 дней",
    "0": "Всё время",
}


def build_analytics_html(rows: List[Any], period: str, metric: str) -> str:
    period_name = PERIOD_TITLE.get(period, period)
    metric_name = METRIC_TITLE.get(metric, metric)

    lines: List[str] = [
        "<b>Аналитика</b>",
        f"<i>Период: {escape(period_name)} · Показатель: {escape(metric_name)}</i>",
        "",
    ]
    lines.append(_build_relations_section(rows))
    lines.append("")
    lines.append(_build_insights_section(rows))
    return "\n".join(lines)


def _relation_sleep_mood(rows: List[Any]) -> Optional[str]:
    more_sleep = [row for row in rows if float(row["sleep"]) > 7]
    less_sleep = [row for row in rows if float(row["sleep"]) <= 7]
    if len(more_sleep) < MIN_PER_GROUP or len(less_sleep) < MIN_PER_GROUP:
        return None

    mood_more = _avg_metric(more_sleep, "m")
    mood_less = _avg_metric(less_sleep, "m")
    if abs(mood_more - mood_less) <= MOOD_DIFF_NOTICE:
        return None

    if mood_more > mood_less:
        return (
            f"- Похоже, в дни со сном больше 7 часов настроение обычно выше "
            f"({mood_more:.1f} против {mood_less:.1f})."
        )
    return (
        "- Похоже, в дни со сном до 7 часов настроение было чуть выше. "
        "Пока это выглядит как слабая закономерность."
    )


def _relation_stress_mood(rows: List[Any]) -> Optional[str]:
    higher_stress, lower_stress, pivot = _split_by_median(rows, "stress")
    if len(higher_stress) < MIN_PER_GROUP or len(lower_stress) < MIN_PER_GROUP:
        return None

    mood_high = _avg_metric(higher_stress, "m")
    mood_low = _avg_metric(lower_stress, "m")
    if abs(mood_low - mood_high) <= MOOD_DIFF_NOTICE:
        return None

    if mood_low > mood_high:
        return (
            f"- В более спокойные дни настроение чаще выше, чем в дни со стрессом от {pivot:.0f} и выше "
            f"({mood_low:.1f} против {mood_high:.1f})."
        )
    return (
        "- В более напряжённые дни настроение неожиданно оказалось чуть выше. "
        "Пока данных недостаточно, чтобы уверенно это подтвердить."
    )


def _relation_tag_mood(rows: List[Any], tag: str) -> Optional[str]:
    with_tag = [row for row in rows if tag in _parse_tags(row["tags"])]
    without_tag = [row for row in rows if tag not in _parse_tags(row["tags"])]
    if len(with_tag) < TAG_MIN_DAYS or len(without_tag) < MIN_PER_GROUP:
        return None

    mood_with = _avg_metric(with_tag, "m")
    mood_without = _avg_metric(without_tag, "m")
    if abs(mood_with - mood_without) <= MOOD_DIFF_NOTICE:
        return None

    label = escape(_tag_label(tag))
    if mood_with > mood_without:
        return (
            f"- С тегом «{label}» настроение обычно выше, чем в дни без него "
            f"({mood_with:.1f} против {mood_without:.1f})."
        )
    return (
        f"- С тегом «{label}» настроение чаще ниже, чем в дни без него "
        f"({mood_with:.1f} против {mood_without:.1f})."
    )


def _relation_tag_stress(rows: List[Any], tag: str) -> Optional[str]:
    with_tag = [row for row in rows if tag in _parse_tags(row["tags"])]
    without_tag = [row for row in rows if tag not in _parse_tags(row["tags"])]
    if len(with_tag) < TAG_MIN_DAYS or len(without_tag) < MIN_PER_GROUP:
        return None

    stress_with = _avg_metric(with_tag, "r")
    stress_without = _avg_metric(without_tag, "r")
    if abs(stress_with - stress_without) <= STRESS_DIFF_NOTICE:
        return None

    label = escape(_tag_label(tag))
    if stress_with > stress_without:
        return (
            f"- В дни с тегом «{label}» стресс обычно выше, чем без него "
            f"({stress_with:.1f} против {stress_without:.1f})."
        )
    return (
        f"- В дни с тегом «{label}» стресс чаще ниже, чем без него "
        f"({stress_with:.1f} против {stress_without:.1f})."
    )


def _collect_relation_lines(rows: List[Any]) -> List[str]:
    if len(rows) < MIN_RECORDS_RELATIONS:
        return []

    lines: List[str] = []
    for builder in (_relation_sleep_mood, _relation_stress_mood):
        line = builder(rows)
        if line:
            lines.append(line)

    for tag in ANALYTICS_TAGS:
        mood_line = _relation_tag_mood(rows, tag)
        if mood_line:
            lines.append(mood_line)

        stress_line = _relation_tag_stress(rows, tag)
        if stress_line:
            lines.append(stress_line)

    return lines[:6]


def _build_relations_section(rows: List[Any]) -> str:
    lines = ["<b>Связи</b>"]
    if len(rows) < MIN_RECORDS_RELATIONS:
        lines.append("Пока данных маловато, чтобы замечать связи между показателями.")
        return "\n".join(lines)

    found = _collect_relation_lines(rows)
    if not found:
        lines.append("Пока заметных закономерностей не видно. Нужны ещё записи за разные дни.")
        return "\n".join(lines)

    lines.extend(found)
    return "\n".join(lines)


def _insight_sleep_mood(rows: List[Any]) -> Optional[str]:
    more_sleep = [row for row in rows if float(row["sleep"]) > 7]
    less_sleep = [row for row in rows if float(row["sleep"]) <= 7]
    if len(more_sleep) < MIN_PER_GROUP or len(less_sleep) < MIN_PER_GROUP:
        return None

    if _avg_metric(more_sleep, "m") > _avg_metric(less_sleep, "m") + MOOD_DIFF_NOTICE:
        return "- Похоже, когда сна больше 7 часов, настроение обычно выше."
    return None


def _insight_stress_mood(rows: List[Any]) -> Optional[str]:
    higher_stress, lower_stress, _ = _split_by_median(rows, "stress")
    if len(higher_stress) < MIN_PER_GROUP or len(lower_stress) < MIN_PER_GROUP:
        return None

    if _avg_metric(lower_stress, "m") > _avg_metric(higher_stress, "m") + MOOD_DIFF_NOTICE:
        return "- Часто в более спокойные дни настроение лучше."
    return None


def _insight_tag_stress(rows: List[Any]) -> Optional[str]:
    for tag in ANALYTICS_TAGS:
        with_tag = [row for row in rows if tag in _parse_tags(row["tags"])]
        without_tag = [row for row in rows if tag not in _parse_tags(row["tags"])]
        if len(with_tag) < TAG_MIN_DAYS or len(without_tag) < MIN_PER_GROUP:
            continue
        if _avg_metric(with_tag, "r") > _avg_metric(without_tag, "r") + STRESS_DIFF_NOTICE:
            return f"- Похоже, тег «{_tag_label(tag)}» часто встречается в более напряжённые дни."
    return None


def _insight_tag_mood(rows: List[Any]) -> Optional[str]:
    for tag in ANALYTICS_TAGS:
        with_tag = [row for row in rows if tag in _parse_tags(row["tags"])]
        without_tag = [row for row in rows if tag not in _parse_tags(row["tags"])]
        if len(with_tag) < TAG_MIN_DAYS or len(without_tag) < MIN_PER_GROUP:
            continue
        if _avg_metric(with_tag, "m") > _avg_metric(without_tag, "m") + MOOD_DIFF_NOTICE:
            return f"- Обычно с тегом «{_tag_label(tag)}» настроение чуть выше."
    return None


def _build_insights_section(rows: List[Any]) -> str:
    lines = ["<b>Инсайты</b>"]
    if len(rows) < MIN_RECORDS_INSIGHTS:
        lines.append("Пока данных маловато, чтобы делать выводы.")
        return "\n".join(lines)

    candidates = [
        _insight_sleep_mood(rows),
        _insight_stress_mood(rows),
        _insight_tag_stress(rows),
        _insight_tag_mood(rows),
    ]

    unique: List[str] = []
    seen = set()
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)

    if not unique:
        lines.append("Пока рано делать выводы — полезно собрать ещё немного записей.")
        return "\n".join(lines)

    lines.extend(unique[:4])
    return "\n".join(lines)
