content=open('backend/main.py', encoding='utf-8').read()
idx = content.find('@app.get("/api/summaries')
print(content[idx:idx+1500])
