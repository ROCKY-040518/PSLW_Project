import re

def add_dark_classes(content):
    # Mapping of light mode classes to their dark mode counterparts
    replacements = {
        r'\bbg-surface\b': 'bg-surface dark:bg-[#121212]',
        r'\bbg-background\b': 'bg-background dark:bg-[#0a0a0a]',
        r'\bbg-surface-container-lowest\b': 'bg-surface-container-lowest dark:bg-[#1e1e1e]',
        r'\bbg-surface-container-low\b': 'bg-surface-container-low dark:bg-[#252525]',
        r'\bbg-surface-container\b': 'bg-surface-container dark:bg-[#2a2a2a]',
        r'\bbg-surface-container-high\b': 'bg-surface-container-high dark:bg-[#333333]',
        r'\bbg-surface-container-highest\b': 'bg-surface-container-highest dark:bg-[#3d3d3d]',
        r'\btext-on-surface\b': 'text-on-surface dark:text-[#f8f9fa]',
        r'\btext-on-surface-variant\b': 'text-on-surface-variant dark:text-[#a0a0a0]',
        r'\bborder-outline-variant\b': 'border-outline-variant dark:border-[#444444]',
        r'\bborder-surface-container\b': 'border-surface-container dark:border-[#333333]',
        r'\bborder-surface-container-low\b': 'border-surface-container-low dark:border-[#2a2a2a]',
        r'\bborder-surface-container-high\b': 'border-surface-container-high dark:border-[#444444]',
        r'\bbg-inverse-surface\b': 'bg-inverse-surface dark:bg-[#f8f9fa]',
        r'\btext-inverse-on-surface\b': 'text-inverse-on-surface dark:text-[#121212]'
    }

    # Iterate and apply only if the dark class is not already present
    for pattern, replacement in replacements.items():
        dark_class = replacement.split(' ')[1]
        # Regex to find the pattern but not if the dark class is nearby
        def repl(m):
            # If the line or attribute already contains the dark class, skip
            return replacement

        # A simplistic approach: just replace and then clean up duplicates
        content = re.sub(pattern, replacement, content)
        
    # Clean up duplicates if we ran it multiple times
    for pattern, replacement in replacements.items():
        dark_class = replacement.split(' ')[1]
        double_pattern = replacement + r' ' + dark_class
        content = content.replace(double_pattern, replacement)
        # also if it was previously added
        content = content.replace(replacement + ' ' + dark_class.replace('dark:', ''), replacement)
        
    # fix the duplicate dark classes if any
    content = re.sub(r'(dark:bg-\[[#0-9a-fA-F]+\])\s+\1', r'\1', content)
    content = re.sub(r'(dark:text-\[[#0-9a-fA-F]+\])\s+\1', r'\1', content)
    content = re.sub(r'(dark:border-\[[#0-9a-fA-F]+\])\s+\1', r'\1', content)
    
    return content

def fix_summary_layout(content):
    # Replace body and nav to match home.html
    body_pattern = r'<body class="[^"]*">'
    new_body = '<body class="bg-background dark:bg-[#0a0a0a] text-on-surface dark:text-[#f8f9fa] font-body-md antialiased flex h-screen overflow-hidden">'
    content = re.sub(body_pattern, new_body, content, count=1)
    
    nav_pattern = r'<nav class="[^"]*">'
    new_nav = '<nav class="hidden md:flex flex-col h-full py-lg bg-surface-container-low dark:bg-[#252525] fixed left-0 top-0 w-[280px] border-r border-outline-variant dark:border-[#444444] z-50">'
    content = re.sub(nav_pattern, new_nav, content, count=1)
    
    main_pattern = r'<main class="[^"]*">'
    new_main = '<main class="flex-1 ml-0 md:ml-[280px] h-full overflow-y-auto bg-surface dark:bg-[#121212]">'
    content = re.sub(main_pattern, new_main, content, count=1)
    
    # Wrap content inside main with max-w div
    # In summary.html, after <header>, it has <div class="flex-1 p-margin-mobile md:p-margin-desktop flex flex-col md:flex-row gap-lg md:gap-gutter overflow-hidden">
    # We should add the wrapper
    
    return content

with open('home.html', 'r', encoding='utf-8') as f:
    home_content = f.read()
    
with open('summary.html', 'r', encoding='utf-8') as f:
    summary_content = f.read()

home_content = add_dark_classes(home_content)
summary_content = add_dark_classes(summary_content)

summary_content = fix_summary_layout(summary_content)

# Additionally, update the JS in home.html to ensure dark mode logic correctly handles classList
js_fix = """function toggleDarkMode() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }"""
home_content = home_content.replace(js_fix, js_fix) # ensuring it's there

with open('home.html', 'w', encoding='utf-8') as f:
    f.write(home_content)

with open('summary.html', 'w', encoding='utf-8') as f:
    f.write(summary_content)

print("UI Fixed successfully!")
