#!/usr/bin/env python3
"""
Basic test script to verify the application structure and imports.
Run this before full deployment to catch any issues early.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that core modules can be imported."""
    print("Testing core module imports...")

    tests = []

    try:
        import baseball_manager_ai
        print("  ✓ baseball_manager_ai package")
        tests.append(True)
    except ImportError as e:
        print(f"  ✗ baseball_manager_ai package: {e}")
        tests.append(False)

    try:
        from baseball_manager_ai.utils import baseball_constants
        print("  ✓ baseball_constants")
        tests.append(True)
    except ImportError as e:
        print(f"  ✗ baseball_constants: {e}")
        tests.append(False)

    try:
        from baseball_manager_ai.utils import win_probability
        print("  ✓ win_probability")
        tests.append(True)
    except ImportError as e:
        print(f"  ✗ win_probability: {e}")
        tests.append(False)

    try:
        from baseball_manager_ai.simulation import game_simulator
        print("  ✓ game_simulator")
        tests.append(True)
    except ImportError as e:
        print(f"  ✗ game_simulator: {e}")
        tests.append(False)

    return all(tests)

def test_config_files():
    """Test that configuration files exist."""
    print("\nTesting configuration files...")

    config_files = [
        'config/model_config.yaml',
        'config/training_config.yaml',
        'config/simulation_config.yaml',
        'config/data_sources.yaml'
    ]

    tests = []
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"  ✓ {config_file}")
            tests.append(True)
        else:
            print(f"  ✗ {config_file}")
            tests.append(False)

    return all(tests)

def test_directories():
    """Test that required directories exist."""
    print("\nTesting directory structure...")

    directories = [
        'config',
        'data',
        'logs',
        'cache',
        'models'
    ]

    tests = []
    for directory in directories:
        if Path(directory).exists():
            print(f"  ✓ {directory}/")
            tests.append(True)
        else:
            print(f"  ✗ {directory}/")
            tests.append(False)

    return all(tests)

def test_baseball_constants():
    """Test baseball constants are accessible."""
    print("\nTesting baseball constants...")

    try:
        from baseball_manager_ai.utils.baseball_constants import TEAMS, POSITIONS

        print(f"  ✓ TEAMS: {len(TEAMS)} teams loaded")
        print(f"  ✓ POSITIONS: {len(POSITIONS)} positions defined")

        # Test a function
        from baseball_manager_ai.utils.baseball_constants import get_team_name
        team_name = get_team_name('NYY')
        print(f"  ✓ get_team_name('NYY') = '{team_name}'")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_win_probability():
    """Test win probability calculations."""
    print("\nTesting win probability...")

    try:
        from baseball_manager_ai.utils.win_probability import calculate_win_probability

        # Test calculation
        wp = calculate_win_probability(
            inning=9,
            outs=2,
            score_diff=1,
            is_home_team=True
        )

        print(f"  ✓ calculate_win_probability(9th inning, 2 outs, +1 run) = {wp:.3f}")

        if 0 <= wp <= 1:
            print(f"  ✓ Win probability in valid range [0, 1]")
            return True
        else:
            print(f"  ✗ Win probability out of range: {wp}")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_game_simulator():
    """Test game simulator."""
    print("\nTesting game simulator...")

    try:
        from baseball_manager_ai.simulation.game_simulator import GameSimulator

        simulator = GameSimulator(seed=42)
        print("  ✓ GameSimulator initialized")

        # Create dummy lineups
        home_lineup = [{'player_id': f'home_{i}', 'season_ops': 0.750} for i in range(9)]
        away_lineup = [{'player_id': f'away_{i}', 'season_ops': 0.750} for i in range(9)]

        pitcher = {'season_era': 4.0, 'season_k9': 8.5}

        # Simulate one game
        game = simulator.simulate_game(
            home_team='HOME',
            away_team='AWAY',
            home_lineup=home_lineup,
            away_lineup=away_lineup,
            home_pitcher=pitcher,
            away_pitcher=pitcher,
            verbose=False
        )

        print(f"  ✓ Simulated game: HOME {game.home_score} - {game.away_score} AWAY")
        print(f"  ✓ Game completed in {game.inning} innings")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("BASEBALL MANAGER AI - BASIC TESTS")
    print("=" * 60)
    print()

    results = {
        'imports': test_imports(),
        'config': test_config_files(),
        'directories': test_directories(),
        'constants': test_baseball_constants(),
        'win_probability': test_win_probability(),
        'simulator': test_game_simulator()
    }

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    all_passed = all(results.values())

    print()
    if all_passed:
        print("✓ All tests passed! Your application is ready for deployment.")
        print("\nNext steps:")
        print("  1. Set up your .env file with Supabase credentials")
        print("  2. Run: python -m baseball_manager_ai.api.model_server")
        print("  3. Visit: http://localhost:8000/health")
        return 0
    else:
        print("✗ Some tests failed. Please address the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
