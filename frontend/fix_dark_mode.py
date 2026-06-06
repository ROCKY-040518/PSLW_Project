import re

def process_home(content):
    # 1. Inputs and Selects
    # find class="..." inside inputs and selects and append dark:bg-[#1e1e1e] dark:border-gray-700 dark:text-gray-200
    
    def repl_class(m):
        cls = m.group(1)
        if 'dark:bg-' not in cls:
            cls += ' dark:bg-[#1e1e1e] dark:border-gray-700 dark:text-gray-200'
        return f'class="{cls}"'

    content = re.sub(r'<input[^>]+class="([^"]+)"', lambda m: m.group(0).replace(f'class="{m.group(1)}"', repl_class(m)), content)
    content = re.sub(r'<select[^>]+class="([^"]+)"', lambda m: m.group(0).replace(f'class="{m.group(1)}"', repl_class(m)), content)
    
    # 2. Table Header
    content = content.replace(
        '<thead class="bg-surface-container-low border-b border-outline-variant">',
        '<thead class="bg-surface-container-low dark:bg-[#252525] border-b border-outline-variant dark:border-gray-700">'
    )
    
    # 3. Drop Zone and Cards
    # Some cards are already processed by previous script but might miss the text/border or exact bg
    # The user asked for "dark:bg-[#1e1e1e]"
    content = content.replace(
        'bg-surface-container-lowest border border-outline-variant',
        'bg-surface-container-lowest dark:bg-[#1e1e1e] border border-outline-variant dark:border-gray-700 dark:text-gray-200'
    )
    
    content = content.replace(
        'bg-surface-container-lowest p-xl',
        'bg-surface-container-lowest dark:bg-[#1e1e1e] p-xl dark:border-gray-700 dark:text-gray-200'
    )
    
    content = content.replace(
        'bg-surface-container-low rounded-xl',
        'bg-surface-container-low dark:bg-[#252525] rounded-xl dark:border-gray-700 dark:text-gray-200'
    )
    
    # Table rows are dynamically generated in JS, let's fix the JS template in home.html
    js_tr = "tr.className = 'border-b border-surface-container hover:bg-surface-container-low transition-colors';"
    js_tr_dark = "tr.className = 'border-b border-surface-container dark:border-gray-700 hover:bg-surface-container-low dark:hover:bg-[#2a2a2a] transition-colors dark:text-gray-200';"
    content = content.replace(js_tr, js_tr_dark)
    
    js_td = "className = 'py-3 px-4 font-body-sm text-body-sm text-on-surface';"
    js_td_dark = "className = 'py-3 px-4 font-body-sm text-body-sm text-on-surface dark:text-[#cccccc]';"
    content = content.replace(js_td, js_td_dark)

    return content

with open('home.html', 'r', encoding='utf-8') as f:
    home_html = f.read()

home_html = process_home(home_html)

with open('home.html', 'w', encoding='utf-8') as f:
    f.write(home_html)

# Extract Nav from home.html
nav_match = re.search(r'(<nav.*?</nav>)', home_html, re.DOTALL)
nav_html = nav_match.group(1)

# Modify Nav for summary.html
nav_html = re.sub(r"switchView\('view-[a-z]+'\); return false;", "window.location.href='home.html';", nav_html)

with open('summary.html', 'r', encoding='utf-8') as f:
    summary_html = f.read()

# Replace Nav
summary_html = re.sub(r'<nav.*?</nav>', nav_html.replace('\\', '\\\\'), summary_html, flags=re.DOTALL)

# Add Dark Mode init script to <head>
init_script = """<script>
    if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
</script>
</head>"""
summary_html = summary_html.replace('</head>', init_script)

# Add Dark Mode classes to STT boxes and Summary boxes
summary_html = summary_html.replace(
    'bg-surface-container-lowest p-lg rounded-xl shadow-sm border border-outline-variant',
    'bg-surface-container-lowest dark:bg-[#1e1e1e] p-lg rounded-xl shadow-sm border border-outline-variant dark:border-gray-700 dark:text-gray-200'
)

# And the main left side STT area
summary_html = summary_html.replace(
    'bg-surface-container-lowest rounded-lg border border-outline-variant h-[calc(100vh-140px)]',
    'bg-surface-container-lowest dark:bg-[#1e1e1e] rounded-lg border border-outline-variant dark:border-gray-700 h-[calc(100vh-140px)]'
)
summary_html = summary_html.replace(
    'bg-surface-bright flex items-center justify-between rounded-t-lg',
    'bg-surface-bright dark:bg-[#252525] flex items-center justify-between rounded-t-lg dark:border-gray-700'
)

with open('summary.html', 'w', encoding='utf-8') as f:
    f.write(summary_html)

print("Fix applied successfully!")
