import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all dark: classes that we added
    content = re.sub(r' dark:(bg|text|border)-\[[#0-9a-fA-F]+\]', '', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

clean_file('home.html')
clean_file('summary.html')
print("Cleaned up")
