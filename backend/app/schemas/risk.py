from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    sender_id: str = Field(..., examples=["ACC0019"])
    receiver_id: str = Field(..., examples=["ACC0115"])
    amount: float = Field(..., gt=0, examples=[24500])
    channel: str = Field("UPI_APP", examples=["PAYMENT_LINK"])
    city: str = Field("Delhi", examples=["Mumbai"])
    device_id: str = Field("DEV-NEW-1", examples=["DEV-NEW-1"])


class SeedResetResponse(BaseModel):
    message: str
