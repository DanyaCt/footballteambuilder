from django import template
from django.core.cache import cache

register = template.Library()

@register.simple_tag
def get_compatibility_country(player_id, other_player_id):
    compatibility_country = cache.get('players_compatibility_country', {})
    key = f"{player_id}_{other_player_id}"
    return compatibility_country.get(key, "Н/Д")

@register.simple_tag
def get_compatibility_age(player_id, other_player_id):
    compatibility_age = cache.get('players_compatibility_age', {})
    key = f"{player_id}_{other_player_id}"
    return compatibility_age.get(key, "Н/Д")

@register.simple_tag
def get_compatibility_experience(player_id, other_player_id):
    compatibility_experience = cache.get('players_compatibility_experience', {})
    key = f"{player_id}_{other_player_id}"
    return compatibility_experience.get(key, "Н/Д")

@register.simple_tag
def get_compatibility_rank(player_id, other_player_id):
    compatibility_experience = cache.get('players_compatibility_rank', {})
    key = f"{player_id}_{other_player_id}"
    return compatibility_experience.get(key, "Н/Д")