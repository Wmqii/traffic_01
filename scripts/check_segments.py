with open('frontend/assets/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('const segmentGeometry = {')
end = content.find('};', start) + 2
geometry_str = content[start:end]

count = geometry_str.count("'SEG-")
print(f'Segments in app.js: {count}')
