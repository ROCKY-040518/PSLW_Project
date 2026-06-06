import re

def fix_fouc_home():
    with open('home.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Remove Copilot's wrong script
    wrong_script = "<script>if (localStorage.getItem('dark_mode') === 'true') document.documentElement.classList.add('dark');</script>"
    content = content.replace(wrong_script, "")

    # 2. Add proper FOUC script before </head>
    proper_script = """<script>
        if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        }
    </script>
</head>"""
    if proper_script not in content:
        content = content.replace('</head>', proper_script)
    
    with open('home.html', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_fouc_summary():
    with open('summary.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove Copilot's wrong script
    wrong_script = "<script>if (localStorage.getItem('dark_mode') === 'true') document.documentElement.classList.add('dark');</script>"
    content = content.replace(wrong_script, "")

    # 2. Fix JS logic
    wrong_js = "if (localStorage.getItem('dark_mode') === 'true' || document.documentElement.classList.contains('dark')) {"
    proper_js = "if (localStorage.getItem('theme') === 'dark' || document.documentElement.classList.contains('dark')) {"
    content = content.replace(wrong_js, proper_js)

    with open('summary.html', 'w', encoding='utf-8') as f:
        f.write(content)

fix_fouc_home()
fix_fouc_summary()
print("FOUC fixes applied!")
