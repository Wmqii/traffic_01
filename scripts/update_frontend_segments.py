import json

with open('data-pipeline/alignment/config/segment_geometry.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result = 'const segmentGeometry = {\n'
for seg in data['segments']:
    coords = seg['coordinates']
    result += f"    '{seg['segment_id']}': [[{coords[0][0]}, {coords[0][1]}], [{coords[1][0]}, {coords[1][1]}]],\n"
result += '  };';

with open('frontend/assets/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('const segmentGeometry = {')
end = content.find('};', start) + 2
new_content = content[:start] + result + content[end:]

with open('frontend/assets/app.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Updated frontend/assets/app.js with {len(data["segments"])} segments')
