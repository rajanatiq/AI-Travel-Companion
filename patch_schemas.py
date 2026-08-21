filepath = r'C:\Users\mq202\PycharmProjects\AI Travel Companion\app\schemas.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''class TripSummaryResponse(BaseModel):
    id: uuid.UUID
    destination: str
    start_date: str
    end_date: str
    budget_total: float
    interests: List[str]
    pace: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)'''

new_block = '''class TripSummaryResponse(BaseModel):
    id: uuid.UUID
    destination: str
    start_date: str
    end_date: str
    budget_total: float
    interests: List[str]
    pace: str
    status: str
    cover_photo: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched schemas.py")
else:
    print("Could not patch schemas.py")
