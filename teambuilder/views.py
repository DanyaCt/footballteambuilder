from django.shortcuts import render
from django.core.cache import cache
from django.core.serializers import serialize
from decimal import Decimal
from geopy.distance import geodesic
from .models import Player, Country
from .forms import TeamCriteriaForm

def index(request):
    return render(request, 'index.html')

def team_form(request):
    calculate_players_compatibility_country()
    calculate_players_compatibility_age()
    calculate_players_compatibility_experience()
    calculate_players_compatibility_rank()
    players = Player.objects.all().order_by('name')
    players_json = serialize('json', players, fields=('id', 'name', 'surname'))

    if request.method == 'POST':
        form = TeamCriteriaForm(request.POST)
        if form.is_valid():
            criteria_priorities = {
                'players_compatibility_country': get_decimal_or_default(form.cleaned_data.get('country_priority')),
                'players_compatibility_age': get_decimal_or_default(form.cleaned_data.get('age_priority')),
                'players_compatibility_experience': get_decimal_or_default(form.cleaned_data.get('experience_priority')),
                'players_compatibility_rank': get_decimal_or_default(form.cleaned_data.get('rank_priority')),
            }

            selected_players_ids = []
            for key in request.POST:
                if key.startswith('player'):
                    player_id = request.POST[key]
                    if player_id:
                        selected_players_ids.append(player_id)

            print("Вибрані гравці IDs:", selected_players_ids)

            final_table = calculate_final_compatibility(criteria_priorities, players)
            best_team = greedy_best_team(final_table, players, selected_players_ids, k=11)

            best_team_players = Player.objects.filter(id__in=best_team).order_by('name')

            return render(request, 'team_form.html', {
                'form': form,
                'final_table': final_table,
                'best_team_players': best_team_players,
                'players_json': players_json
            })
        else:
            return render(request, 'team_form.html', {
                'form': form,
                'players_json': players_json
            })
    else:
        form = TeamCriteriaForm()
        return render(request, 'team_form.html', {
            'form': form,
            'players_json': players_json
        })


def all_data(request):
    compatibility_list_country = calculate_compatibility()
    players = Player.objects.all().order_by('name')
    countries = Country.objects.all().order_by('country')
    players_compatibility_country = calculate_players_compatibility_country()
    players_compatibility_age = calculate_players_compatibility_age()
    players_compatibility_experience = calculate_players_compatibility_experience()
    players_compatibility_rank = calculate_players_compatibility_rank()
    return render(request, 'all_data.html', {
        'players': players,
        'countries': countries,
        'compatibility_list_country': compatibility_list_country,
        'players_compatibility_country': players_compatibility_country,
        'players_compatibility_age': players_compatibility_age,
        'players_compatibility_experience': players_compatibility_experience,
        'players_compatibility_rank': players_compatibility_rank
    })

def get_decimal_or_default(value, default='0'):
    if value in [None, '']:
        return Decimal(default)
    return Decimal(value)

def calculate_compatibility():
    countries = Country.objects.all().order_by('country')
    max_distance = 0
    compatibility_list_country = []

    for country1 in countries:
        for country2 in countries:
            if country1 != country2:
                distance = geodesic((country1.latitude, country1.longitude), (country2.latitude, country2.longitude)).kilometers
                max_distance = max(max_distance, distance)

    for country1 in countries:
        country_compatibilities = [country1.country]
        for country2 in countries:
            if country1 == country2:
                compatibility_score = 1.0
            else:
                distance = geodesic((country1.latitude, country1.longitude), (country2.latitude, country2.longitude)).kilometers
                compatibility_score = round(1 - (distance / max_distance), 3)
            country_compatibilities.append(compatibility_score)
        compatibility_list_country.append(country_compatibilities)

    cache.set('countries_compatibility_list', compatibility_list_country, timeout=86400)
    return compatibility_list_country

def calculate_players_compatibility_country():
    countries_compatibility_list = cache.get('countries_compatibility_list', [])
    if not countries_compatibility_list:
        countries_compatibility_list = calculate_compatibility()

    countries_compatibility_dict = {
        (country1_name, country2_name): compatibility_score
        for country1_name, *compatibilities in countries_compatibility_list
        for country2_name, compatibility_score in zip(
            [country2_name for country2_name, *_ in countries_compatibility_list],
            compatibilities
        )
    }

    players = Player.objects.select_related('country').all()
    players_compatibility_country = {}

    for player1 in players:
        for player2 in players:
            if player1 != player2:
                key = f"{player1.id}_{player2.id}"
                comp_score = countries_compatibility_dict.get(
                    (player1.country.country, player2.country.country)
                )
                if comp_score is not None:
                    players_compatibility_country[key] = comp_score
                else:
                    players_compatibility_country[key] = 0

    cache.set('players_compatibility_country', players_compatibility_country, timeout=86400)
    return players_compatibility_country


def calculate_players_compatibility_age():
    players = Player.objects.all()
    min_age = min(players, key=lambda x: x.age).age
    max_age = max(players, key=lambda x: x.age).age
    age_range = max_age - min_age

    players_compatibility_age = {}

    for player1 in players:
        for player2 in players:
            if player1 != player2:
                age_diff = abs(player1.age - player2.age)
                compatibility_score = 1 - (age_diff / age_range) if age_range else 1
                key = f"{player1.id}_{player2.id}"
                players_compatibility_age[key] = round(compatibility_score, 3)
            else:
                key = f"{player1.id}_{player2.id}"
                players_compatibility_age[key] = 1

    cache.set('players_compatibility_age', players_compatibility_age, timeout=86400)
    return players_compatibility_age

def calculate_players_compatibility_experience():
    players = Player.objects.all()
    max_experience = max(players, key=lambda x: x.experience).experience
    min_experience = min(players, key=lambda x: x.experience).experience
    experience_range = max_experience - min_experience

    players_compatibility_experience = {}

    for player1 in players:
        for player2 in players:
            if player1 == player2:
                key = f"{player1.id}_{player2.id}"
                players_compatibility_experience[key] = 1
            else:
                experience_diff = abs(player1.experience - player2.experience)
                if experience_range > 0:
                    compatibility_score = 1 - (experience_diff / experience_range)
                else:
                    compatibility_score = 1
                key = f"{player1.id}_{player2.id}"
                players_compatibility_experience[key] = round(compatibility_score, 3)

    cache.set('players_compatibility_experience', players_compatibility_experience, timeout=86400)
    
    return players_compatibility_experience

def calculate_players_compatibility_rank():
    players = Player.objects.all()
    max_rank = max(players, key=lambda x: x.rank).rank
    min_rank = min(players, key=lambda x: x.rank).rank
    rank_range = max_rank - min_rank

    players_compatibility_rank = {}

    for player1 in players:
        for player2 in players:
            if player1 == player2:
                key = f"{player1.id}_{player2.id}"
                players_compatibility_rank[key] = 1
            else:
                rank_diff = abs(player1.rank - player2.rank)
                if rank_range > 0:
                    compatibility_score = 1 - (rank_diff / rank_range)
                else:
                    compatibility_score = 1 
                key = f"{player1.id}_{player2.id}"
                players_compatibility_rank[key] = round(compatibility_score, 3)

    cache.set('players_compatibility_rank', players_compatibility_rank, timeout=86400)
    
    return players_compatibility_rank

def calculate_final_compatibility(criteria_priorities, players):
    final_compatibility = {f"{p1.id}_{p2.id}": 0 for p1 in players for p2 in players if p1 != p2}

    for criterion_key, priority in criteria_priorities.items():
        compatibility_scores = cache.get(criterion_key, {})
        for key in final_compatibility.keys():
            if key in compatibility_scores:
                score = compatibility_scores[key]
                final_compatibility[key] += Decimal(str(score)) * Decimal(str(priority))

    for key in final_compatibility:
        final_compatibility[key] = final_compatibility[key].quantize(Decimal('0.001'))

    return final_compatibility

def greedy_best_team(final_table, all_players, selected_player_ids, k=11):
    all_player_ids = [int(player.id) for player in all_players]

    selected_player_ids = set(int(id) for id in selected_player_ids)

    selected_players = set(selected_player_ids)

    compatibility_pairs = [
        ((i, j), final_table.get(f"{i}_{j}", Decimal('0')))
        for i in selected_player_ids for j in all_player_ids if i != j
    ]

    compatibility_pairs.sort(key=lambda x: x[1], reverse=True)

    for (i, j), _ in compatibility_pairs:
        if len(selected_players) >= k:
            break
        if j not in selected_players:
            selected_players.add(j)

    if len(selected_players) < k:
        additional_pairs = [
            ((i, j), final_table.get(f"{i}_{j}", Decimal('0')))
            for i in all_player_ids for j in all_player_ids if i != j and i not in selected_players and j not in selected_players
        ]
        additional_pairs.sort(key=lambda x: x[1], reverse=True)
        for (i, j), _ in additional_pairs:
            if len(selected_players) >= k:
                break
            if i not in selected_players and j not in selected_players:
                selected_players.update([i, j])
            elif i not in selected_players:
                selected_players.add(i)
            elif j not in selected_players:
                selected_players.add(j)

    print(f"Final selected players: {list(selected_players)}")

    return list(selected_players)[:k]

