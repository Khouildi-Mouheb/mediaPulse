from collections import Counter, defaultdict
from typing import Dict

from sqlalchemy.orm import Session

from models import Billboard, OOHEvent, User
from schemas import calculate_age, get_age_group


PREMIUM_REGIONS = {"Lac 2", "La Marsa", "Tunis Centre"}
PREMIUM_OCCUPATIONS = {"Manager", "Engineer", "Business Owner", "Doctor", "Lawyer"}


def _apply_filters(query, filters: Dict):
    if filters.get("region"):
        query = query.filter(Billboard.region == filters["region"])
    if filters.get("panel_id"):
        query = query.filter(Billboard.panel_id == filters["panel_id"])
    if filters.get("start_date"):
        query = query.filter(OOHEvent.timestamp >= filters["start_date"])
    if filters.get("end_date"):
        query = query.filter(OOHEvent.timestamp <= filters["end_date"])
    return query


def _normalize_percentages(counter: Counter) -> Dict[str, float]:
    total = sum(counter.values())
    if total == 0:
        return {}
    return {key: round((value / total) * 100, 2) for key, value in counter.items()}


def get_panels_demographics(filters: Dict, db: Session):
    query = (
        db.query(OOHEvent, User, Billboard)
        .join(User, User.id == OOHEvent.user_id)
        .join(Billboard, Billboard.id == OOHEvent.billboard_id)
    )
    query = _apply_filters(query, filters)

    sex_counter = Counter()
    age_counter = Counter()
    region_counter = Counter()
    occupation_counter = Counter()
    total = 0

    for event, user, billboard in query.all():
        if filters.get("sex") and user.sex != filters["sex"]:
            continue
        age = calculate_age(user.birth_date)
        age_group = get_age_group(age)
        if filters.get("age_group") and age_group != filters["age_group"]:
            continue
        if filters.get("occupation") and user.occupation != filters["occupation"]:
            continue

        total += 1
        sex_counter[user.sex] += 1
        age_counter[age_group] += 1
        region_counter[user.region] += 1
        occupation_counter[user.occupation] += 1

    def group_other(counter: Counter):
        grouped = Counter()
        for key, value in counter.items():
            if value < 5:
                grouped["Other"] += value
            else:
                grouped[key] += value
        return grouped

    return {
        "total_exposures": total,
        "sex": _normalize_percentages(group_other(sex_counter)),
        "age_group": _normalize_percentages(group_other(age_counter)),
        "region": _normalize_percentages(group_other(region_counter)),
        "occupation": _normalize_percentages(group_other(occupation_counter)),
    }


def _premium_score(region: str, occupation: str) -> float:
    score = 0.5
    if region in PREMIUM_REGIONS:
        score += 0.3
    if occupation in PREMIUM_OCCUPATIONS:
        score += 0.2
    return round(min(score, 1.0) * 100, 2)


def get_panels_ranking(filters: Dict, db: Session):
    query = (
        db.query(OOHEvent, User, Billboard)
        .join(User, User.id == OOHEvent.user_id)
        .join(Billboard, Billboard.id == OOHEvent.billboard_id)
    )
    query = _apply_filters(query, filters)

    panel_stats = defaultdict(list)
    for event, user, billboard in query.all():
        if filters.get("sex") and user.sex != filters["sex"]:
            continue
        age = calculate_age(user.birth_date)
        age_group = get_age_group(age)
        if filters.get("age_group") and age_group != filters["age_group"]:
            continue
        if filters.get("occupation") and user.occupation != filters["occupation"]:
            continue
        panel_stats[billboard.panel_id].append((user, billboard))

    results = []
    max_exposures = max((len(v) for v in panel_stats.values()), default=1)

    for panel_id, rows in panel_stats.items():
        billboard = rows[0][1]
        total_exposures = len(rows)
        sex_counter = Counter(user.sex for user, _ in rows)
        age_counter = Counter(get_age_group(calculate_age(user.birth_date)) for user, _ in rows)
        occupation_counter = Counter(user.occupation for user, _ in rows)

        female_percent = round((sex_counter.get("female", 0) / total_exposures) * 100, 2)
        male_percent = round((sex_counter.get("male", 0) / total_exposures) * 100, 2)
        age_18_34 = age_counter.get("18-24", 0) + age_counter.get("25-34", 0)
        age_18_34_percent = round((age_18_34 / total_exposures) * 100, 2)
        top_occupation = occupation_counter.most_common(1)[0][0] if occupation_counter else None

        exposure_score = round((total_exposures / max_exposures) * 100, 2)
        premium_score = _premium_score(billboard.region, top_occupation or "")
        score = round(
            exposure_score * 0.5
            + age_18_34_percent * 0.2
            + female_percent * 0.1
            + premium_score * 0.2,
            2,
        )

        results.append(
            {
                "panel_id": billboard.panel_id,
                "name": billboard.name,
                "region": billboard.region,
                "total_exposures": total_exposures,
                "female_percent": female_percent,
                "male_percent": male_percent,
                "age_18_34_percent": age_18_34_percent,
                "top_occupation": top_occupation,
                "premium_score": premium_score,
                "score": score,
            }
        )

    return sorted(results, key=lambda item: item["score"], reverse=True)
