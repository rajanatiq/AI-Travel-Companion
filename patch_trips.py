import os

filepath = r'C:\Users\mq202\PycharmProjects\AI Travel Companion\app\routes\trips.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'from app.services.image_service import ImageService' not in content:
    content = content.replace('from app.services.places_service import PlacesService', 'from app.services.places_service import PlacesService\nfrom app.services.image_service import ImageService')

# Update format_trip_detail
old_format = '''        status=trip.status,
        created_at=trip.created_at,
        updated_at=trip.updated_at,'''

new_format = '''        status=trip.status,
        cover_photo=trip.cover_photo,
        created_at=trip.created_at,
        updated_at=trip.updated_at,'''
content = content.replace(old_format, new_format)

# Update list_trips
old_list = '''            pace=t.pace,
            status=t.status,
            created_at=t.created_at,
            updated_at=t.updated_at'''
new_list = '''            pace=t.pace,
            status=t.status,
            cover_photo=t.cover_photo,
            created_at=t.created_at,
            updated_at=t.updated_at'''
content = content.replace(old_list, new_list)

# Update create_trip
old_create = '''    trip_id = uuid.uuid4()
    new_trip = Trip(
        id=trip_id,
        user_id=current_user.id,
        destination=req.destination,
        start_date=start_d,'''
new_create = '''    cover_photo = await ImageService.get_city_image(req.destination, db)

    trip_id = uuid.uuid4()
    new_trip = Trip(
        id=trip_id,
        user_id=current_user.id,
        destination=req.destination,
        cover_photo=cover_photo,
        start_date=start_d,'''
content = content.replace(old_create, new_create)

# Update update_trip return
old_update = '''        status=trip.status,
        created_at=trip.created_at,'''
new_update = '''        status=trip.status,
        cover_photo=trip.cover_photo,
        created_at=trip.created_at,'''
content = content.replace(old_update, new_update)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched trips.py successfully!")
