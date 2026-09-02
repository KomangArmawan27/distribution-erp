from pydantic import BaseModel, ConfigDict, Field


class DocumentTypeCreate(BaseModel):
    doctype_code: str = Field(..., max_length=30)
    doctype_name: str = Field(..., max_length=100)


class DocumentTypeUpdate(BaseModel):
    doctype_code: str | None = Field(None, max_length=30)
    doctype_name: str | None = Field(None, max_length=100)


class DocumentTypeRead(BaseModel):
    doctype_id: int
    doctype_code: str
    doctype_name: str
    model_config = ConfigDict(from_attributes=True)


class FlowStateCreate(BaseModel):
    doctype_id: int
    docflow_seq: int
    flow_state: str = Field(..., max_length=50)


class FlowStateUpdate(BaseModel):
    docflow_seq: int | None = None
    flow_state: str | None = Field(None, max_length=50)


class FlowStateRead(BaseModel):
    flow_id: int
    doctype_id: int
    docflow_seq: int
    flow_state: str
    model_config = ConfigDict(from_attributes=True)


class FlowTransitionCreate(BaseModel):
    doctype_id: int
    from_seq: int
    to_seq: int
    action_label: str = Field(..., max_length=50)
    min_role: int = 1


class FlowTransitionUpdate(BaseModel):
    action_label: str | None = Field(None, max_length=50)
    min_role: int | None = None


class FlowTransitionRead(BaseModel):
    transition_id: int
    doctype_id: int
    from_seq: int
    to_seq: int
    action_label: str
    min_role: int
    model_config = ConfigDict(from_attributes=True)


class StateUpdateIn(BaseModel):
    to_seq: int
