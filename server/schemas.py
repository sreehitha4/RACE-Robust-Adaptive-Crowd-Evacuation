from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


Point = tuple[FiniteFloat, FiniteFloat]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExitSchema(StrictModel):
    id: str | int
    polygon: list[Point] = Field(min_length=3)


class EnvironmentMessage(StrictModel):
    type: Literal["environment"] = "environment"
    width: FiniteFloat = Field(gt=0)
    height: FiniteFloat = Field(gt=0)
    walls: list[list[Point]]
    obstacles: list[list[Point]]
    exits: list[ExitSchema]


class AgentMessage(StrictModel):
    id: str | int
    x: FiniteFloat
    y: FiniteFloat
    vx: FiniteFloat
    vy: FiniteFloat
    state: str
    predicted: list[Point] | None = None


class FrameMessage(StrictModel):
    type: Literal["frame"] = "frame"
    simulation_time: FiniteFloat = Field(ge=0)
    total_agents: int = Field(ge=0)
    evacuated: int = Field(ge=0)
    agents: list[AgentMessage]
    density: FiniteFloat | None = Field(default=None, ge=0)
    prediction_model: str | None = None
