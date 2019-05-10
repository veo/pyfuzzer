# pyfuzzer
Python fuzz tool,Multi-threading,Support POST and GET


## GET
pyfuzzer.py http://www.example.com/file/$.pdf payloads.txt
## POST
pyfuzzer.py http://www.example.com/login.php payloads.txt --data 'username=admin&password=$'

log in data.log and request data in data/
