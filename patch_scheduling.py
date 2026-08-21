import os
filepath = r'C:\Users\mq202\PycharmProjects\AI Travel Companion\app\engine\scheduling.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix Lunch logic
lunch_old = '''                    # Pick real food spot if available
                    if real_food_spots and food_idx < len(real_food_spots):
                        f_spot = real_food_spots[food_idx % len(real_food_spots)]
                        food_idx += 1'''

lunch_new = '''                    # Pick real food spot if available
                    f_spot = None
                    while food_idx < len(real_food_spots):
                        potential = real_food_spots[food_idx]
                        food_idx += 1
                        if potential.get("place_id") not in used_place_ids:
                            f_spot = potential
                            used_place_ids.add(potential.get("place_id"))
                            break

                    if f_spot:'''
content = content.replace(lunch_old, lunch_new)

# Fix photo_url inside Lunch append (this requires replacing the exact line)
content = re.sub(r'\"photo_url\": real_food_spots\[\(food_idx \- 1\) \% len\(real_food_spots\)\]\.get\(\"photo_url\", \"\"\)\s*if\s*real_food_spots and food_idx > 0 else \"\",', '"photo_url": f_spot.get("photo_url", "") if f_spot else "",', content)

# Fix Dinner logic
dinner_old = '''                    if real_food_spots:
                        f_spot = real_food_spots[food_idx % len(real_food_spots)]
                        food_idx += 1'''
dinner_new = '''                    f_spot = None
                    while food_idx < len(real_food_spots):
                        potential = real_food_spots[food_idx]
                        food_idx += 1
                        if potential.get("place_id") not in used_place_ids:
                            f_spot = potential
                            used_place_ids.add(potential.get("place_id"))
                            break

                    if f_spot:'''
content = content.replace(dinner_old, dinner_new)

# Fix photo_url inside Dinner append
content = re.sub(r'\"photo_url\": real_food_spots\[\(food_idx \- 1\) \% len\(real_food_spots\)\]\.get\(\"photo_url\", \"\"\)\s*if\s*real_food_spots and food_idx > 0 else \"\",', '"photo_url": f_spot.get("photo_url", "") if f_spot else "",', content)


# Fix Sightseeing duplicate fallback logic
fallback_old = '''                if not best_candidate and scored_candidates:
                    best_candidate = scored_candidates[pois_scheduled % len(scored_candidates)]'''
fallback_new = '''                # If no unique unused candidates remain, we stop scheduling POIs for today to prevent duplicates
                # We do not fallback to modulo!'''
content = content.replace(fallback_old, fallback_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched scheduling.py!")
