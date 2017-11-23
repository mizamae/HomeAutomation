import requests


file_contents=b'{"_type":"location","tid":"ad","acc":67,"batt":81,"conn":"m","lat":42.8171802,"lon":-1.6013,"tst":1510572418}'
headers = {'Content-Type': 'application/json'}

#print(file_contents)
response = requests.post('http://localhost:8000/owntracks/mizamae/', data=file_contents, headers=headers)
print(str(response))