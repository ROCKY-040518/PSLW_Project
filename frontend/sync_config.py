import re

with open('home.html', 'r', encoding='utf-8') as f:
    home_content = f.read()

m = re.search(r'<script id="tailwind-config">.*?</script>', home_content, re.DOTALL)
if m:
    home_config = m.group(0)
    
    with open('summary.html', 'r', encoding='utf-8') as f:
        summary_content = f.read()
        
    summary_content = re.sub(r'<script id="tailwind-config">.*?</script>', home_config.replace('\\', '\\\\'), summary_content, flags=re.DOTALL)
    
    with open('summary.html', 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print("Tailwind config synced successfully.")
else:
    print("Could not find tailwind config in home.html")
