import requests


file='C:/xampp/htdocs/async_data.xml'
headers = {'Content-Type': 'application/xml'}
open_file = open(file,'r')
file_contents = open_file.read()
#print(file_contents)
response = requests.post('http://localhost:8000/async_post/', data=file_contents, headers=headers)
print(str(response))