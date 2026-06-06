import re

def safe_replace(content):
    # 1. body
    content = content.replace(
        '<body class="bg-background text-on-surface font-body-md antialiased flex h-screen overflow-hidden">',
        '<body class="bg-background dark:bg-[#121212] text-on-surface dark:text-[#f8f9fa] font-body-md antialiased flex h-screen overflow-hidden">'
    )
    content = content.replace(
        '<body class="bg-surface text-on-surface font-body-md min-h-screen flex">',
        '<body class="bg-background dark:bg-[#121212] text-on-surface dark:text-[#f8f9fa] font-body-md antialiased flex h-screen overflow-hidden">'
    )
    # 2. nav
    content = content.replace(
        '<nav class="hidden md:flex flex-col h-full py-lg bg-surface-container-low fixed left-0 top-0 w-[280px] border-r border-outline-variant z-50">',
        '<nav class="hidden md:flex flex-col h-full py-lg bg-surface-container-low dark:bg-[#1e1e1e] fixed left-0 top-0 w-[280px] border-r border-outline-variant dark:border-[#333333] z-50">'
    )
    # 3. main
    content = content.replace(
        '<main class="flex-1 ml-0 md:ml-[280px] h-full overflow-y-auto bg-surface">',
        '<main class="flex-1 ml-0 md:ml-[280px] h-full overflow-y-auto bg-surface dark:bg-[#121212]">'
    )
    content = content.replace(
        '<main class="flex-1 md:ml-[280px] min-h-screen flex flex-col max-w-[max-width] mx-auto w-full">',
        '<main class="flex-1 md:ml-[280px] h-full overflow-y-auto bg-surface dark:bg-[#121212] flex flex-col max-w-[max-width] mx-auto w-full">'
    )
    
    # Cards
    content = content.replace(
        'bg-surface-container-lowest border border-outline-variant',
        'bg-surface-container-lowest dark:bg-[#1e1e1e] border border-outline-variant dark:border-[#333333]'
    )
    
    # Specific layout div
    content = content.replace(
        '<div class="flex-1 p-margin-mobile md:p-margin-desktop flex flex-col md:flex-row gap-lg md:gap-gutter overflow-hidden">',
        '<div class="max-w-[1440px] mx-auto px-margin-mobile md:px-margin-desktop py-xl flex-1 flex flex-col md:flex-row gap-lg md:gap-gutter overflow-hidden">'
    )
    
    # Header bg
    content = content.replace(
        'bg-surface sticky',
        'bg-surface dark:bg-[#121212] sticky'
    )
    
    # Text colors
    content = content.replace(
        'text-on-surface ',
        'text-on-surface dark:text-[#f8f9fa] '
    )
    content = content.replace(
        'text-on-surface"',
        'text-on-surface dark:text-[#f8f9fa]"'
    )
    content = content.replace(
        'text-on-surface-variant ',
        'text-on-surface-variant dark:text-[#a0a0a0] '
    )
    content = content.replace(
        'text-on-surface-variant"',
        'text-on-surface-variant dark:text-[#a0a0a0]"'
    )

    # Clean up accidental duplicates
    content = content.replace('dark:text-[#f8f9fa]-variant', 'dark:text-[#a0a0a0]')
    content = content.replace('dark:text-[#f8f9fa] dark:text-[#a0a0a0]', 'dark:text-[#a0a0a0]')
    content = content.replace('dark:text-[#f8f9fa] dark:text-[#f8f9fa]', 'dark:text-[#f8f9fa]')
    content = content.replace('dark:text-[#a0a0a0] dark:text-[#a0a0a0]', 'dark:text-[#a0a0a0]')
    content = content.replace('dark:bg-[#121212] dark:bg-[#121212]', 'dark:bg-[#121212]')
    content = content.replace('dark:bg-[#1e1e1e] dark:bg-[#1e1e1e]', 'dark:bg-[#1e1e1e]')
    content = content.replace('dark:border-[#333333] dark:border-[#333333]', 'dark:border-[#333333]')
    
    return content

for file in ['home.html', 'summary.html']:
    with open(file, 'r', encoding='utf-8') as f:
        html = f.read()
    html = safe_replace(html)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(html)
    
print("Dark Mode Injection Complete!")
