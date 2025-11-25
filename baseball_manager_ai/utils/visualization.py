"""
Visualization utilities for baseball analysis and decision tracking.

Provides charts and visualizations for:
- Game timelines and win probability
- Decision outcomes
- Lineup comparisons
- Strategy analysis
"""

import logging
from typing import Dict, List, Tuple, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available; visualization functions will not work")

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def plot_game_timeline(
    game_log: List[Dict],
    title: str = "Game Timeline",
    figsize: Tuple[int, int] = (14, 6),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot game timeline with score progression.
    
    Args:
        game_log: List of inning results
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure (optional)
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    df = pd.DataFrame(game_log)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
    
    # Score progression
    ax1.plot(df['inning'], df['home_score'], 'o-', label='Home', linewidth=2, markersize=6)
    ax1.plot(df['inning'], df['away_score'], 's-', label='Away', linewidth=2, markersize=6)
    
    ax1.fill_between(df['inning'], df['home_score'], df['away_score'], 
                     where=(df['home_score'] >= df['away_score']), 
                     alpha=0.2, color='green', label='Home Leading')
    ax1.fill_between(df['inning'], df['home_score'], df['away_score'],
                     where=(df['home_score'] < df['away_score']),
                     alpha=0.2, color='red', label='Away Leading')
    
    ax1.set_xlabel('Inning')
    ax1.set_ylabel('Runs')
    ax1.set_title(title)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Runs per inning
    home_runs_per = df['home_runs'].diff().fillna(df['home_runs'].iloc[0])
    away_runs_per = df['away_runs'].diff().fillna(df['away_runs'].iloc[0])
    
    x = np.arange(len(df))
    width = 0.35
    
    ax2.bar(x - width/2, home_runs_per, width, label='Home', alpha=0.8)
    ax2.bar(x + width/2, away_runs_per, width, label='Away', alpha=0.8)
    
    ax2.set_xlabel('Inning')
    ax2.set_ylabel('Runs This Inning')
    ax2.set_title('Runs Per Inning')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df['inning'])
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved game timeline to {save_path}")
    
    return fig


def plot_win_probability_chart(
    wp_history: pd.DataFrame,
    title: str = "Win Probability Chart",
    figsize: Tuple[int, int] = (14, 6),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot win probability throughout game.
    
    Args:
        wp_history: DataFrame with columns: timestamp, inning, home_wp, away_wp
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot WP for both teams
    ax.plot(wp_history['timestamp'], wp_history['home_wp'], 'o-', 
            label='Home WP', linewidth=2, markersize=4, color='blue')
    ax.plot(wp_history['timestamp'], wp_history['away_wp'], 's-',
            label='Away WP', linewidth=2, markersize=4, color='red')
    
    # Add 50% line
    ax.axhline(y=0.5, color='black', linestyle='--', alpha=0.3, label='Even Odds')
    
    # Fill between lines
    ax.fill_between(wp_history['timestamp'], 
                   wp_history['home_wp'],
                   0.5,
                   where=(wp_history['home_wp'] >= 0.5),
                   alpha=0.2, color='blue', label='Home Advantage')
    ax.fill_between(wp_history['timestamp'],
                   wp_history['away_wp'],
                   0.5,
                   where=(wp_history['away_wp'] >= 0.5),
                   alpha=0.2, color='red', label='Away Advantage')
    
    # Mark inning changes
    if 'inning' in wp_history.columns:
        inning_changes = wp_history[wp_history['inning'].diff() != 0]
        for _, row in inning_changes.iterrows():
            ax.axvline(x=row['timestamp'], color='gray', linestyle=':', alpha=0.5)
    
    ax.set_xlabel('Play Number')
    ax.set_ylabel('Win Probability')
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved WP chart to {save_path}")
    
    return fig


def plot_decision_comparison(
    decisions: List[Dict],
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot decision outcome comparison.
    
    Args:
        decisions: List of decision dictionaries with:
            - decision_type
            - outcome ('success', 'failure', 'neutral')
            - wpa (Win Probability Added)
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    df = pd.DataFrame(decisions)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Decision outcomes by type
    decision_counts = df.groupby(['decision_type', 'outcome']).size().unstack(fill_value=0)
    decision_counts.plot(kind='bar', ax=ax1, color=['red', 'gray', 'green'])
    
    ax1.set_title('Decision Outcomes by Type')
    ax1.set_ylabel('Count')
    ax1.set_xlabel('Decision Type')
    ax1.legend(title='Outcome')
    ax1.grid(True, alpha=0.3, axis='y')
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # WPA by decision type
    wpa_by_type = df.groupby('decision_type')['wpa'].agg(['mean', 'std', 'count'])
    wpa_by_type = wpa_by_type.sort_values('mean', ascending=True)
    
    ax2.barh(range(len(wpa_by_type)), wpa_by_type['mean'], 
            xerr=wpa_by_type['std'], capsize=5, alpha=0.7)
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_yticks(range(len(wpa_by_type)))
    ax2.set_yticklabels(wpa_by_type.index)
    ax2.set_xlabel('Average WPA')
    ax2.set_title('Decision Quality (WPA)')
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved decision comparison to {save_path}")
    
    return fig


def plot_lineup_heatmap(
    lineup_stats: pd.DataFrame,
    stat_column: str = 'ops',
    title: str = "Lineup Statistics",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot heatmap of lineup statistics.
    
    Args:
        lineup_stats: DataFrame with player stats by position
        stat_column: Column to visualize
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    if not HAS_SEABORN:
        logger.warning("seaborn not available; using matplotlib heatmap")
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap data
    positions = lineup_stats.get('position', range(len(lineup_stats)))
    values = lineup_stats[stat_column]
    
    # Create color map
    cmap = plt.cm.RdYlGn
    norm = plt.Normalize(vmin=values.min(), vmax=values.max())
    colors = cmap(norm(values))
    
    # Bar chart with color gradient
    bars = ax.bar(range(len(lineup_stats)), values, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{value:.2f}',
               ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Player/Position')
    ax.set_ylabel(stat_column.upper())
    ax.set_title(title)
    ax.set_xticks(range(len(lineup_stats)))
    ax.set_xticklabels(positions, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label(stat_column.upper())
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved lineup heatmap to {save_path}")
    
    return fig


def plot_wpa_by_play(
    play_data: pd.DataFrame,
    figsize: Tuple[int, int] = (14, 6),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot WPA for each play in sequence.
    
    Args:
        play_data: DataFrame with columns: play_number, description, wpa
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = ['green' if x > 0 else 'red' for x in play_data['wpa']]
    
    ax.bar(range(len(play_data)), play_data['wpa'], color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    ax.set_xlabel('Play Number')
    ax.set_ylabel('Win Probability Added')
    ax.set_title('WPA by Play')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved WPA plot to {save_path}")
    
    return fig


def plot_run_expectancy_matrix(
    re_matrix: np.ndarray,
    figsize: Tuple[int, int] = (10, 8),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot run expectancy matrix as heatmap.
    
    Args:
        re_matrix: 8x3 RE24 matrix
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    base_states = ['---', '1--', '-2-', '12-', '--3', '1-3', '-23', '123']
    outs_labels = ['0 outs', '1 out', '2 outs']
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if HAS_SEABORN:
        sns.heatmap(re_matrix.T, annot=True, fmt='.2f', cmap='YlGn',
                   xticklabels=base_states, yticklabels=outs_labels,
                   cbar_kws={'label': 'Expected Runs'}, ax=ax)
    else:
        # Manual heatmap
        im = ax.imshow(re_matrix.T, cmap='YlGn', aspect='auto')
        ax.set_xticks(range(len(base_states)))
        ax.set_yticks(range(len(outs_labels)))
        ax.set_xticklabels(base_states)
        ax.set_yticklabels(outs_labels)
        
        # Add values
        for i in range(len(base_states)):
            for j in range(len(outs_labels)):
                text = ax.text(i, j, f'{re_matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontweight='bold')
        
        plt.colorbar(im, ax=ax, label='Expected Runs')
    
    ax.set_xlabel('Base State')
    ax.set_ylabel('Outs')
    ax.set_title('Run Expectancy Matrix (RE24)')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved RE matrix to {save_path}")
    
    return fig


def plot_player_spray_chart(
    batted_balls: pd.DataFrame,
    title: str = "Spray Chart",
    figsize: Tuple[int, int] = (10, 10),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot batted ball spray chart.
    
    Args:
        batted_balls: DataFrame with columns: x, y, hit_type, outcome
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Define colors for different hit types
    hit_colors = {
        'ground_ball': 'brown',
        'line_drive': 'red',
        'fly_ball': 'blue',
        'popup': 'gray'
    }
    
    hit_markers = {
        'ground_ball': 'o',
        'line_drive': 's',
        'fly_ball': '^',
        'popup': 'v'
    }
    
    # Plot each batted ball
    for hit_type in batted_balls['hit_type'].unique():
        data = batted_balls[batted_balls['hit_type'] == hit_type]
        ax.scatter(data['x'], data['y'], 
                  c=hit_colors.get(hit_type, 'black'),
                  marker=hit_markers.get(hit_type, 'o'),
                  label=hit_type.replace('_', ' ').title(),
                  alpha=0.7, s=50)
    
    # Draw baseball field outline
    field_circle = plt.Circle((0, 0), 300, fill=False, color='black', linewidth=2)
    ax.add_patch(field_circle)
    
    # Add foul lines
    ax.plot([0, 300], [0, 300], 'k-', linewidth=2)
    ax.plot([0, 300], [0, -300], 'k-', linewidth=2)
    
    ax.set_xlabel('Horizontal Distance (ft)')
    ax.set_ylabel('Vertical Distance (ft)')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved spray chart to {save_path}")
    
    return fig


def plot_pitcher_arsenal(
    pitch_data: pd.DataFrame,
    title: str = "Pitch Arsenal",
    figsize: Tuple[int, int] = (12, 8),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot pitcher pitch mix and effectiveness.
    
    Args:
        pitch_data: DataFrame with columns: pitch_type, velocity, spin_rate, result
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
    
    # Pitch usage
    pitch_counts = pitch_data['pitch_type'].value_counts()
    ax1.pie(pitch_counts.values, labels=pitch_counts.index, autopct='%1.1f%%')
    ax1.set_title('Pitch Usage')
    
    # Velocity by pitch type
    velocity_by_type = pitch_data.groupby('pitch_type')['velocity'].mean()
    ax2.bar(range(len(velocity_by_type)), velocity_by_type.values)
    ax2.set_xticks(range(len(velocity_by_type)))
    ax2.set_xticklabels(velocity_by_type.index, rotation=45)
    ax2.set_ylabel('Velocity (mph)')
    ax2.set_title('Average Velocity')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Results by pitch type
    if 'result' in pitch_data.columns:
        result_by_type = pd.crosstab(pitch_data['pitch_type'], pitch_data['result'])
        result_by_type.plot(kind='bar', ax=ax3)
        ax3.set_title('Pitch Results')
        ax3.set_xlabel('Pitch Type')
        ax3.set_ylabel('Count')
        ax3.legend(title='Result')
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # Spin rate distribution
    if 'spin_rate' in pitch_data.columns:
        pitch_data.boxplot(column='spin_rate', by='pitch_type', ax=ax4)
        ax4.set_title('Spin Rate Distribution')
        ax4.set_xlabel('Pitch Type')
        ax4.set_ylabel('Spin Rate (RPM)')
    
    plt.suptitle(title)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved pitcher arsenal to {save_path}")
    
    return fig


def plot_batter_spray_heatmap(
    batted_balls: pd.DataFrame,
    title: str = "Spray Heatmap",
    figsize: Tuple[int, int] = (10, 8),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Create heatmap of batted ball locations.
    
    Args:
        batted_balls: DataFrame with x, y coordinates
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create 2D histogram
    if HAS_SEABORN:
        sns.kdeplot(x=batted_balls['x'], y=batted_balls['y'], 
                   cmap='Reds', fill=True, alpha=0.7, ax=ax)
    else:
        # Manual hexbin
        hb = ax.hexbin(batted_balls['x'], batted_balls['y'], 
                      gridsize=20, cmap='Reds', alpha=0.7)
        plt.colorbar(hb, ax=ax, label='Density')
    
    # Draw field outline
    field_circle = plt.Circle((0, 0), 300, fill=False, color='black', linewidth=2)
    ax.add_patch(field_circle)
    
    ax.set_xlabel('Horizontal Distance (ft)')
    ax.set_ylabel('Vertical Distance (ft)')
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved spray heatmap to {save_path}")
    
    return fig


def plot_strategy_analysis(
    strategy_data: pd.DataFrame,
    metric: str = 'success_rate',
    title: str = "Strategy Analysis",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot effectiveness of different strategies.
    
    Args:
        strategy_data: DataFrame with strategy performance metrics
        metric: Metric to visualize
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    strategies = strategy_data['strategy']
    values = strategy_data[metric]
    
    # Sort by metric value
    sorted_idx = np.argsort(values)
    strategies = strategies.iloc[sorted_idx]
    values = values.iloc[sorted_idx]
    
    bars = ax.barh(range(len(strategies)), values, alpha=0.7)
    
    # Color bars based on value
    for i, (bar, value) in enumerate(zip(bars, values)):
        if value > 0.6:  # High success
            bar.set_color('green')
        elif value > 0.4:  # Medium success
            bar.set_color('orange')
        else:  # Low success
            bar.set_color('red')
    
    ax.set_yticks(range(len(strategies)))
    ax.set_yticklabels(strategies)
    ax.set_xlabel(metric.replace('_', ' ').title())
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, v in enumerate(values):
        ax.text(v + 0.01, i, f'{v:.3f}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved strategy analysis to {save_path}")
    
    return fig


def plot_interactive_win_probability(
    wp_history: pd.DataFrame,
    title: str = "Interactive Win Probability"
) -> Optional[any]:
    """
    Create interactive win probability chart using Plotly.
    
    Args:
        wp_history: DataFrame with win probability data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    if not HAS_PLOTLY:
        logger.warning("Plotly not available for interactive visualization")
        return None
    
    fig = go.Figure()
    
    # Add home team WP
    fig.add_trace(go.Scatter(
        x=wp_history['timestamp'],
        y=wp_history['home_wp'],
        mode='lines+markers',
        name='Home WP',
        line=dict(color='blue', width=3),
        marker=dict(size=6)
    ))
    
    # Add away team WP
    fig.add_trace(go.Scatter(
        x=wp_history['timestamp'],
        y=wp_history['away_wp'],
        mode='lines+markers',
        name='Away WP',
        line=dict(color='red', width=3),
        marker=dict(size=6)
    ))
    
    # Add 50% line
    fig.add_hline(y=0.5, line_dash="dash", line_color="black", opacity=0.5)
    
    # Mark inning changes
    if 'inning' in wp_history.columns:
        inning_changes = wp_history[wp_history['inning'].diff() != 0]
        for _, row in inning_changes.iterrows():
            fig.add_vline(x=row['timestamp'], line_dash="dot", 
                         line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=title,
        xaxis_title="Play Number",
        yaxis_title="Win Probability",
        yaxis=dict(range=[0, 1]),
        hovermode='x unified',
        template="plotly_white"
    )
    
    return fig


def plot_defensive_alignment(
    alignment_data: pd.DataFrame,
    title: str = "Defensive Alignment",
    figsize: Tuple[int, int] = (10, 8),
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Plot defensive positioning on field.
    
    Args:
        alignment_data: DataFrame with player positions (x, y coordinates)
        title: Chart title
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Draw baseball diamond
    diamond_x = [0, -90, 0, 90, 0]
    diamond_y = [0, 90, 180, 90, 0]
    ax.plot(diamond_x, diamond_y, 'k-', linewidth=2)
    
    # Plot player positions
    for _, player in alignment_data.iterrows():
        ax.scatter(player['x'], player['y'], s=200, alpha=0.7)
        ax.annotate(player['position'], (player['x'], player['y']),
                   xytext=(5, 5), textcoords='offset points',
                   fontweight='bold', fontsize=8)
    
    ax.set_xlim(-150, 150)
    ax.set_ylim(-50, 250)
    ax.set_xlabel('Horizontal Position')
    ax.set_ylabel('Vertical Position')
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved defensive alignment to {save_path}")
    
    return fig


def create_dashboard_summary(
    game_data: Dict,
    save_path: Optional[str] = None
) -> Optional[any]:
    """
    Create comprehensive dashboard with multiple visualizations.
    
    Args:
        game_data: Dictionary containing all game data
        save_path: Path to save dashboard
    
    Returns:
        Matplotlib figure object
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for visualization")
        return None
    
    fig = plt.figure(figsize=(16, 12))
    
    # Create subplot grid
    gs = fig.add_gridspec(3, 3)
    
    # Game timeline (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    if 'game_log' in game_data:
        df = pd.DataFrame(game_data['game_log'])
        ax1.plot(df['inning'], df['home_score'], 'o-', label='Home')
        ax1.plot(df['inning'], df['away_score'], 's-', label='Away')
        ax1.set_title('Score Progression')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
    
    # Win probability (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    if 'wp_history' in game_data:
        wp_df = game_data['wp_history']
        ax2.plot(wp_df['timestamp'], wp_df['home_wp'], 'b-', label='Home WP')
        ax2.plot(wp_df['timestamp'], wp_df['away_wp'], 'r-', label='Away WP')
        ax2.axhline(y=0.5, color='k', linestyle='--', alpha=0.3)
        ax2.set_title('Win Probability')
        ax2.set_ylim(0, 1)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # WPA by play (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    if 'play_data' in game_data:
        play_df = game_data['play_data']
        colors = ['green' if x > 0 else 'red' for x in play_df['wpa']]
        ax3.bar(range(len(play_df)), play_df['wpa'], color=colors, alpha=0.7)
        ax3.axhline(y=0, color='k', linewidth=1)
        ax3.set_title('WPA by Play')
        ax3.grid(True, alpha=0.3, axis='y')
    
    # Decision outcomes (middle row)
    ax4 = fig.add_subplot(gs[1, :])
    if 'decisions' in game_data:
        df = pd.DataFrame(game_data['decisions'])
        decision_counts = df.groupby(['decision_type', 'outcome']).size().unstack(fill_value=0)
        decision_counts.plot(kind='bar', ax=ax4)
        ax4.set_title('Decision Outcomes')
        ax4.legend(title='Outcome')
        ax4.grid(True, alpha=0.3, axis='y')
    
    # Lineup performance (bottom left)
    ax5 = fig.add_subplot(gs[2, 0])
    if 'lineup_stats' in game_data:
        lineup_df = game_data['lineup_stats']
        if 'ops' in lineup_df.columns:
            ax5.bar(range(len(lineup_df)), lineup_df['ops'])
            ax5.set_title('Lineup OPS')
            ax5.set_xticks(range(len(lineup_df)))
            ax5.set_xticklabels(lineup_df.get('position', range(len(lineup_df))), rotation=45)
            ax5.grid(True, alpha=0.3, axis='y')
    
    # Strategy effectiveness (bottom middle)
    ax6 = fig.add_subplot(gs[2, 1])
    if 'strategy_data' in game_data:
        strat_df = game_data['strategy_data']
        if 'success_rate' in strat_df.columns:
            ax6.barh(range(len(strat_df)), strat_df['success_rate'])
            ax6.set_yticks(range(len(strat_df)))
            ax6.set_yticklabels(strat_df['strategy'])
            ax6.set_title('Strategy Success Rate')
            ax6.grid(True, alpha=0.3, axis='x')
    
    # Run expectancy (bottom right)
    ax7 = fig.add_subplot(gs[2, 2])
    if 're_matrix' in game_data:
        re_matrix = game_data['re_matrix']
        im = ax7.imshow(re_matrix.T, cmap='YlGn', aspect='auto')
        ax7.set_title('Run Expectancy')
        plt.colorbar(im, ax=ax7)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved dashboard to {save_path}")
    
    return fig


# Utility functions
def set_plot_style(style: str = 'seaborn-v0_8'):
    """
    Set matplotlib plotting style.
    
    Args:
        style: matplotlib style name
    """
    if HAS_MATPLOTLIB:
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
        logger.info(f"Set plot style to: {style}")


def save_figure(fig: any, filename: str, dpi: int = 150, **kwargs):
    """
    Save figure with consistent settings.
    
    Args:
        fig: matplotlib figure object
        filename: output filename
        dpi: resolution
        **kwargs: additional arguments to savefig
    """
    if HAS_MATPLOTLIB and fig is not None:
        fig.savefig(filename, dpi=dpi, bbox_inches='tight', **kwargs)
        logger.info(f"Saved figure to: {filename}")
