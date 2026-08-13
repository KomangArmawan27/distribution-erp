from pydantic import BaseModel, ConfigDict, Field


class GroupBase(BaseModel):
    group_noid: int = Field(ge=0)
    group_name: str = Field(max_length=50)
    group_value: str = Field(max_length=100)


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    group_noid: int | None = Field(default=None, ge=0)
    group_name: str | None = Field(default=None, max_length=50)
    group_value: str | None = Field(default=None, max_length=100)


class GroupRead(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    group_id: int