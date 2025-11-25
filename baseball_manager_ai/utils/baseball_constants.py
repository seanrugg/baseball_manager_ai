"""
Baseball constants and definitions.

Provides standard baseball terminology, field positions, game rules, etc.
"""

from typing import Dict, List, Tuple


# MLB Teams
TEAMS = {
    # AL East
    'BAL': {'name': 'Baltimore Orioles', 'division': 'AL East', 'park': 'Oriole Park at Camden Yards'},
    'BOS': {'name': 'Boston Red Sox', 'division': 'AL East', 'park': 'Fenway Park'},
    'NYY': {'name': 'New York Yankees', 'division': 'AL East', 'park': 'Yankee Stadium'},
    'TB': {'name': 'Tampa Bay Rays', 'division': 'AL East', 'park': 'Tropicana Field'},
    'TOR': {'name': 'Toronto Blue Jays', 'division': 'AL East', 'park': 'Rogers Centre'},
    
    # AL Central
    'CWS': {'name': 'Chicago White Sox', 'division': 'AL Central', 'park': 'Guaranteed Rate Field'},
    'CLE': {'name': 'Cleveland Guardians', 'division': 'AL Central', 'park': 'Progressive Field'},
    'DET': {'name': 'Detroit Tigers', 'division': 'AL Central', 'park': 'Comerica Park'},
    'KC': {'name': 'Kansas City Royals', 'division': 'AL Central', 'park': 'Kauffman Stadium'},
    'MIN': {'name': 'Minnesota Twins', 'division': 'AL Central', 'park': 'Target Field'},
    
    # AL West
    'HOU': {'name': 'Houston Astros', 'division': 'AL West', 'park': 'Minute Maid Park'},
    'LAA': {'name': 'Los Angeles Angels', 'division': 'AL West', 'park': 'Angel Stadium'},
    'OAK': {'name': 'Oakland Athletics', 'division': 'AL West', 'park': 'Oakland Coliseum'},
    'SEA': {'name': 'Seattle Mariners', 'division': 'AL West', 'park': 'T-Mobile Park'},
    'TEX': {'name': 'Texas Rangers', 'division': 'AL West', 'park': 'Globe Life Field'},
    
    # NL East
    'ATL': {'name': 'Atlanta Braves', 'division': 'NL East', 'park': 'Truist Park'},
    'MIA': {'name': 'Miami Marlins', 'division': 'NL East', 'park': 'loanDepot park'},
    'NYM': {'name': 'New York Mets', 'division': 'NL East', 'park': 'Citi Field'},
    'PHI': {'name': 'Philadelphia Phillies', 'division': 'NL East', 'park': 'Citizens Bank Park'},
    'WSH': {'name': 'Washington Nationals', 'division': 'NL East', 'park': 'Nationals Park'},
    
    # NL Central
    'CHC': {'name': 'Chicago Cubs', 'division': 'NL Central', 'park': 'Wrigley Field'},
    'CIN': {'name': 'Cincinnati Reds', 'division': 'NL Central', 'park': 'Great American Ball Park'},
    'MIL': {'name': 'Milwaukee Brewers', 'division': 'NL Central', 'park': 'American Family Field'},
    'PIT': {'name': 'Pittsburgh Pirates', 'division': 'NL Central', 'park': 'PNC Park'},
    'STL': {'name': 'St. Louis Cardinals', 'division': 'NL Central', 'park': 'Busch Stadium'},
    
    # NL West
    'ARI': {'name': 'Arizona Diamondbacks', 'division': 'NL West', 'park': 'Chase Field'},
    'COL': {'name': 'Colorado Rockies', 'division': 'NL West', 'park': 'Coors Field'},
    'LAD': {'name': 'Los Angeles Dodgers', 'division': 'NL West', 'park': 'Dodger Stadium'},
    'SD': {'name': 'San Diego Padres', 'division': 'NL West', 'park': 'Petco Park'},
    'SF': {'name': 'San Francisco Giants', 'division': 'NL West', 'park': 'Oracle Park'},
}

# Defensive Positions
POSITIONS = {
    'P': {'name': 'Pitcher', 'abbr': 'P', 'fielding_importance': 10},
    'C': {'name': 'Catcher', 'abbr': 'C', 'fielding_importance': 9},
    '1B': {'name': 'First Base', 'abbr': '1B', 'fielding_importance': 6},
    '2B': {'name': 'Second Base', 'abbr': '2B', 'fielding_importance': 8},
    '3B': {'name': 'Third Base', 'abbr': '3B', 'fielding_importance': 7},
    'SS': {'name': 'Shortstop', 'abbr': 'SS', 'fielding_importance': 9},
    'LF': {'name': 'Left Field', 'abbr': 'LF', 'fielding_importance': 5},
    'CF': {'name': 'Center Field', 'abbr': 'CF', 'fielding_importance': 7},
    'RF': {'name': 'Right Field', 'abbr': 'RF', 'fielding_importance': 5},
    'DH': {'name': 'Designated Hitter', 'abbr': 'DH', 'fielding_importance': 0},
}

# Player Roles
PLAYER_ROLES = {
    'starter': {'description': 'Starting Pitcher', 'typical_usage': 'game'},
    'reliever': {'description': 'Relief Pitcher', 'typical_usage': 'multiple innings'},
    'closer': {'description': 'Closer', 'typical_usage': '9th inning'},
    'setup': {'description': 'Setup Man', 'typical_usage': '7-8th inning'},
    'long_relief': {'description': 'Long Reliever', 'typical_usage': 'early relief'},
    'middle_relief': {'description': 'Middle Reliever', 'typical_usage': '5-7th inning'},
}

# Decision Types
DECISION_TYPES = {
    'steal_attempt': {
        'description': 'Steal base',
        'risk_level': 'medium',
        'success_threshold': 0.65
    },
    'sacrifice_bunt': {
        'description': 'Sacrifice bunt',
        'risk_level': 'low',
        'success_threshold': 0.65
    },
    'hit_and_run': {
        'description': 'Hit and run',
        'risk_level': 'medium',
        'success_threshold': 0.60
    },
    'play_it_safe': {
        'description': 'Play conservatively',
        'risk_level': 'low',
        'success_threshold': 0.50
    },
    'aggressive_baserun': {
        'description': 'Aggressive baserunning',
        'risk_level': 'high',
        'success_threshold': 0.60
    },
    'pitch_around': {
        'description': 'Pitch around batter',
        'risk_level': 'medium',
        'success_threshold': 0.55
    },
    'intentional_walk': {
        'description': 'Intentional walk',
        'risk_level': 'low',
        'success_threshold': 0.50
    },
    'full_count_approach': {
        'description': 'Aggressive full count',
        'risk_level': 'high',
        'success_threshold': 0.50
    },
}

# Game States
GAME_STATES = {
    'early_game': {'inning_range': (1, 3), 'description': 'Early innings'},
    'mid_game': {'inning_range': (4, 6), 'description': 'Middle innings'},
    'late_game': {'inning_range': (7, 8), 'description': 'Late innings'},
    'very_late_game': {'inning_range': (9, 9), 'description': 'Bottom of 9th'},
    'extra_inning': {'inning_range': (10, 99), 'description': 'Extra innings'},
}

# Base States (indexed 0-7)
BASE_STATES = {
    0: {'bases': (False, False, False), 'name': '---', 'runners': 0},
    1: {'bases': (True, False, False), 'name': '1--', 'runners': 1},
    2: {'bases': (False, True, False), 'name': '-2-', 'runners': 1},
    3: {'bases': (True, True, False), 'name': '12-', 'runners': 2},
    4: {'bases': (False, False, True), 'name': '--3', 'runners': 1},
    5: {'bases': (True, False, True), 'name': '1-3', 'runners': 2},
    6: {'bases': (False, True, True), 'name': '-23', 'runners': 2},
    7: {'bases': (True, True, True), 'name': '123', 'runners': 3},
}

# Park Factors (run environment multipliers)
PARK_FACTORS = {
    'Fenway Park': 1.08,
    'Yankee Stadium': 1.08,
    'Oriole Park at Camden Yards': 1.06,
    'Rogers Centre': 0.98,
    'Comerica Park': 0.94,
    'Coors Field': 1.20,  # Altitude advantage
    'Dodger Stadium': 0.94,
    'Oracle Park': 0.88,
    'Great American Ball Park': 1.05,
    'Citizens Bank Park': 1.05,
    'Busch Stadium': 1.00,
}

# Scoring Events
SCORING_EVENTS = {
    'single': {'bases_advance': 1, 'points': 0},
    'double': {'bases_advance': 2, 'points': 0},
    'triple': {'bases_advance': 3, 'points': 0},
    'home_run': {'bases_advance': 4, 'points': 1},
    'walk': {'bases_advance': 1, 'points': 0},
    'hit_by_pitch': {'bases_advance': 1, 'points': 0},
    'sacrifice_fly': {'bases_advance': 0, 'points': 0},
}

# Handedness
HANDEDNESS = {
    'L': 'Left',
    'R': 'Right',
    'S': 'Switch',
}

# Batting Order Positions (1-9)
BATTING_POSITIONS = {
    1: {'name': 'Leadoff', 'emphasis': ['OBP', 'speed', 'contact']},
    2: {'name': 'Number Two', 'emphasis': ['OBP', 'speed', 'sacrifice']},
    3: {'name': 'Number Three', 'emphasis': ['AVG', 'OBP', 'consistency']},
    4: {'name': 'Cleanup', 'emphasis': ['power', 'RBI', 'SLG']},
    5: {'name': 'Number Five', 'emphasis': ['power', 'RBI', 'consistency']},
    6: {'name': 'Number Six', 'emphasis': ['flexibility', 'speed', 'average']},
    7: {'name': 'Number Seven', 'emphasis': ['flexibility', 'speed', 'average']},
    8: {'name': 'Number Eight', 'emphasis': ['flexibility', 'contact']},
    9: {'name': 'Pitcher', 'emphasis': ['speed', 'contact']},
}

# Run Values (approximate run values for outcomes)
RUN_VALUES = {
    'strikeout': -0.27,
    'walk': 0.33,
    'single': 0.47,
    'double': 0.77,
    'triple': 1.06,
    'home_run': 1.40,
    'out': -0.27,
    'sacrifice_bunt': -0.07,
    'stolen_base': 0.18,
    'caught_stealing': -0.42,
}

# Default Statistics (league averages)
DEFAULT_STATS = {
    'batter': {
        'avg': 0.253,
        'obp': 0.323,
        'slg': 0.413,
        'ops': 0.736,
        'strikeout_rate': 0.215,
        'walk_rate': 0.085,
        'iso': 0.160,
    },
    'pitcher': {
        'era': 4.01,
        'whip': 1.27,
        'k9': 8.46,
        'bb9': 2.90,
        'era_lhb': 4.15,
        'era_rhb': 3.90,
    },
}


def get_base_state_name(bases: Tuple[bool, bool, bool]) -> str:
    """
    Get human-readable base state name.
    
    Args:
        bases: (first, second, third) occupied
    
    Returns:
        Base state name (e.g., '1-3', '123')
    """
    idx = sum((1 << i) for i in range(3) if bases[i])
    return BASE_STATES.get(idx, {}).get('name', '---')


def get_position_name(position_code: str) -> str:
    """
    Get full position name from code.
    
    Args:
        position_code: Position code (e.g., 'SS', '1B')
    
    Returns:
        Full position name
    """
    return POSITIONS.get(position_code, {}).get('name', 'Unknown')


def get_team_name(team_code: str) -> str:
    """
    Get full team name from code.
    
    Args:
        team_code: Team code (e.g., 'NYY')
    
    Returns:
        Full team name
    """
    return TEAMS.get(team_code, {}).get('name', 'Unknown')


def get_team_park(team_code: str) -> str:
    """
    Get team's home park.
    
    Args:
        team_code: Team code
    
    Returns:
        Stadium name
    """
    return TEAMS.get(team_code, {}).get('park', 'Unknown')


def get_park_factor(park_name: str) -> float:
    """
    Get park run environment factor.
    
    Args:
        park_name: Stadium name
    
    Returns:
        Park factor (>1.0 favors offense)
    """
    return PARK_FACTORS.get(park_name, 1.0)


def get_division_teams(division: str) -> List[str]:
    """
    Get all teams in a division.
    
    Args:
        division: Division name (e.g., 'AL East')
    
    Returns:
        List of team codes
    """
    return [
        code for code, info in TEAMS.items()
        if info.get('division') == division
    ]


def classify_game_state(inning: int) -> str:
    """
    Classify game state by inning.
    
    Args:
        inning: Current inning number
    
    Returns:
        Game state classification
    """
    for state_name, info in GAME_STATES.items():
        min_inning, max_inning = info['inning_range']
        if min_inning <= inning <= max_inning:
            return state_name
    
    return 'extra_inning'


def get_run_value(outcome: str) -> float:
    """
    Get run value for outcome.
    
    Args:
        outcome: Outcome type
    
    Returns:
        Run value
    """
    return RUN_VALUES.get(outcome, 0.0)
