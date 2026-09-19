from typing import Optional
from pydantic import BaseModel, Field

class TrackPredictRequest(BaseModel):
    song_name:str
    artist_name:str
    album_name: Optional[str] = "Unknown"
    genre:Optional[str]="Unknown"
    platform:str="windows"
    shuffle_mode:bool=False
    reason_start:str="trackdone"
    skips_last_3m:int=Field(default=0, ge=0)
    skips_last_15m:int=Field(default=0,ge=0)
    seconds_since_last_skip:float=Field(default=10000.0,ge=0.0)
    consecutive_listens_streak:int=Field(default=0,ge=0)
    previous_song_skipped:bool=False


class DualPolicyAction(BaseModel):
    cdn_buffer_policy:str
    recommender_policy:str
    explanation:str


class SkipPredictionResponse(BaseModel):
    song_name:str
    artist_name:str
    skip_probability:float
    is_skip_predicted:bool
    decision_threshold:float=0.776
    risk_tier:str
    actions:DualPolicyAction