content=open('backend/main.py', encoding='utf-8').read()
idx1 = content.find('CREATE TABLE IF NOT EXISTS summaries')
print(content[idx1:idx1+400])

idx2 = content.find('def upload_audio')
print(content[idx2:idx2+1000])
