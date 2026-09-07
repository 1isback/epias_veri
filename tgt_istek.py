import requests

url = "https://giris.epias.com.tr/cas/v1/tickets"

payload = "username=yusufefe.erer@sankoenerji.com.tr&password=Efe982114."

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/plain"
}

response = requests.post(url, data=payload, headers=headers)

print(response.status_code) # Response HTTP Status Code
print(response.text) # TGT value like: TGT-*******