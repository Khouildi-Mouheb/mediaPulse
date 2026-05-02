from datetime import date

from models import Billboard, Channel, Reward


DEFAULT_BILLBOARDS = [
    {
        "panel_id": "PANEL_LAC2_001",
        "name": "Billboard Lac 2",
        "region": "Tunis",
        "lat": 36.8489,
        "lng": 10.2801,
        "radius_meters": 50,
    },
    {
        "panel_id": "PANEL_BOURGUIBA_002",
        "name": "Avenue Habib Bourguiba",
        "region": "Tunis Centre",
        "lat": 36.8008,
        "lng": 10.1815,
        "radius_meters": 50,
    },
    {
        "panel_id": "PANEL_ARIANA_003",
        "name": "Ariana Centre",
        "region": "Ariana",
        "lat": 36.8665,
        "lng": 10.1647,
        "radius_meters": 50,
    },
]

DEFAULT_REWARDS = [
    {
        "title": "Carrefour 5% discount",
        "description": "5% discount at Carrefour",
        "points_cost": 500,
        "sponsor_name": "BrandX Beverage",
        "supermarket_name": "Carrefour",
        "discount_type": "percentage",
        "discount_value": "5%",
        "valid_until": date(2026, 12, 31),
    },
    {
        "title": "MG 5 TND discount",
        "description": "5 TND discount at MG",
        "points_cost": 900,
        "sponsor_name": "FreshMarket Tunisia",
        "supermarket_name": "MG",
        "discount_type": "fixed",
        "discount_value": "5 TND",
        "valid_until": date(2026, 12, 31),
    },
    {
        "title": "Monoprix 10% discount",
        "description": "10% discount at Monoprix",
        "points_cost": 1500,
        "sponsor_name": "Healthy Snacks TN",
        "supermarket_name": "Monoprix",
        "discount_type": "percentage",
        "discount_value": "10%",
        "valid_until": date(2026, 12, 31),
    },
]


def seed_data(db, default_channel_url: str):
    existing_channel = (
        db.query(Channel).filter(Channel.name == "Diwan FM").first()
    )
    if not existing_channel:
        db.add(
            Channel(
                name="Diwan FM",
                media_type="radio",
                source_type="youtube",
                source_url=default_channel_url,
                active=True,
            )
        )

    for billboard in DEFAULT_BILLBOARDS:
        exists = (
            db.query(Billboard)
            .filter(Billboard.panel_id == billboard["panel_id"])
            .first()
        )
        if not exists:
            db.add(Billboard(**billboard))

    for reward in DEFAULT_REWARDS:
        exists = (
            db.query(Reward)
            .filter(Reward.title == reward["title"])
            .first()
        )
        if not exists:
            db.add(Reward(**reward))

    db.commit()
