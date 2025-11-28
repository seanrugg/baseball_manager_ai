from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Game(Base):
    __tablename__ = 'games'

    id = Column(String(50), primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    home_team = Column(String(3), nullable=False, index=True)
    away_team = Column(String(3), nullable=False, index=True)
    home_score = Column(Integer)
    away_score = Column(Integer)
    stadium = Column(String(100))
    weather = Column(String(50))
    attendance = Column(Integer)
    game_duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    play_by_play = relationship("PlayByPlay", back_populates="game")
    decisions = relationship("ManagerDecision", back_populates="game")


class Player(Base):
    __tablename__ = 'players'

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    team = Column(String(3), index=True)
    position = Column(String(2))
    bats = Column(String(1))
    throws = Column(String(1))
    height = Column(String(10))
    weight = Column(Integer)
    born = Column(DateTime)
    season_avg = Column(Float)
    season_ops = Column(Float)
    season_era = Column(Float)
    season_k9 = Column(Float)
    season_bb9 = Column(Float)
    season_whip = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlayByPlay(Base):
    __tablename__ = 'play_by_play'

    id = Column(String(50), primary_key=True)
    game_id = Column(String(50), ForeignKey('games.id'), nullable=False, index=True)
    inning = Column(Integer, nullable=False)
    inning_state = Column(String(1))
    batter_id = Column(String(50))
    pitcher_id = Column(String(50))
    result = Column(String(50))
    result_description = Column(Text)
    runs_scored = Column(Integer)
    rbi = Column(Integer)
    home_run = Column(Boolean, default=False)
    strikeout = Column(Boolean, default=False)
    walk = Column(Boolean, default=False)
    outs = Column(Integer)
    bases_state = Column(String(10))
    win_probability_added = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="play_by_play")


class ManagerDecision(Base):
    __tablename__ = 'manager_decisions'

    id = Column(String(50), primary_key=True)
    game_id = Column(String(50), ForeignKey('games.id'), nullable=False, index=True)
    inning = Column(Integer, nullable=False)
    outs = Column(Integer)
    bases_state = Column(String(10))
    decision_type = Column(String(50), nullable=False)
    team = Column(String(3), nullable=False)
    player_id = Column(String(50))
    description = Column(Text)
    success = Column(Boolean)
    win_probability_before = Column(Float)
    win_probability_after = Column(Float)
    win_probability_added = Column(Float)
    expected_runs_before = Column(Float)
    expected_runs_after = Column(Float)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game", back_populates="decisions")


class SimulationResult(Base):
    __tablename__ = 'simulation_results'

    id = Column(String(50), primary_key=True)
    home_team = Column(String(3), nullable=False, index=True)
    away_team = Column(String(3), nullable=False, index=True)
    num_simulations = Column(Integer, nullable=False)
    home_win_probability = Column(Float, nullable=False)
    away_win_probability = Column(Float, nullable=False)
    average_home_score = Column(Float)
    average_away_score = Column(Float)
    home_run_diff = Column(Float)
    extra_innings_percentage = Column(Float)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class TeamStats(Base):
    __tablename__ = 'team_stats'

    id = Column(String(50), primary_key=True)
    team = Column(String(3), nullable=False, index=True)
    season = Column(Integer, nullable=False)
    wins = Column(Integer)
    losses = Column(Integer)
    runs_for = Column(Integer)
    runs_against = Column(Integer)
    batting_avg = Column(Float)
    on_base_pct = Column(Float)
    slugging_pct = Column(Float)
    ops = Column(Float)
    era = Column(Float)
    strikeout_rate = Column(Float)
    walk_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
