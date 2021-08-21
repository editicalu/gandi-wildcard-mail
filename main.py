#!/bin/python3
from itertools import product
from requests import get, patch, post
from json import loads

def api_get(url):
    return get(url, headers={'Authorization': f"Apikey {API_KEY}"})
def api_patch(url, body):
    return patch(url, json=body, headers={'Authorization': f"Apikey {API_KEY}"})
def api_post(url, body):
    return post(url, json=body, headers={'Authorization': f"Apikey {API_KEY}"})

import requests
from requests import get

print("This application will add a bunch of wildcards to one mail address.")
print("In order to start, please request an API key using the dashboard.")
print("You can find your API key as follows:")
print()
print(" 1. Go to the dashboard on https://admin.gandi.net/")
print(" 2. Click on your username in the upper right corner and pick \"User Settings\"")
print(" 3. Choose \"Manage the user account and security settings\"")
print(" 4. In the tab Security, you can set up the 'Production API key'.")

API_KEY = input("Please enter your API key: ")

print("Fetching domains...")
print("Pick the domain you wish to edit.")

# https://api.gandi.net/docs/domains/
res = api_get("https://api.gandi.net/v5/domain/domains")
domains_api = loads(res.text)
if res.status_code != 200:
    print("Something went wrong while fetching domains.")
    if res.status_code == 403:
        print("You have no access to domains.")
    if res.status_code == 401:
        print("Could not authorize you. Did you enter the correct API key?")
    exit(1)

# Get a list of domains
domains = list(map(lambda item: (item['fqdn']), domains_api))
for idx, domain in enumerate(domains):
    print(f"{idx+1}: {domain}")

# Domain selection
selection = None
while selection is None:
    selection_opt = input("Please enter the domain/number you want to edit: ")
    if selection_opt in domains:
        idx_opt = domains.index(selection_opt)
        selection = domains_api[idx_opt]
    else:
        try:
            number = int(selection_opt) - 1
            if number >= 0:
                selection = domains_api[number]
        except:
            pass

domain_id = selection['id']
domain_fqdn = selection['fqdn']

# Email selection
# https://api.gandi.net/docs/email/
print("Fetching existing mailboxes...")
api_response = api_get(f"https://api.gandi.net/v5/email/mailboxes/{domain_fqdn}")
if api_response.status_code != 200:
    print("Something went wrong when fetching mailboxes.")
    exit(1)

full_mailboxes = loads(api_response.text)
mails = list(map(lambda mailbox: mailbox["address"], full_mailboxes))

print()
print("Please enter the mailbox which you want all mails to be redirected to.")
print("Enter the part before @, so for 'bob@example.com', enter 'bob'.")
print("If the mailbox exists, we will modify it. If it doesn't exist, it will be created.")
print("Be sure there's some quota left to create a mailbox in this case.")
mail_alias = input("Mailbox: ")
mail = f"{mail_alias}@{domain_fqdn}"

if mail in mails:
    print("Existing mailbox found with this name. Existing aliases will be overwritten.")
    uuid = next(filter(lambda a: a["address"] == mail, full_mailboxes))["id"]
    password = None
else:
    print("We couldn't find any mailbox. We'll create a new one.")
    print("Be sure there's some quota left to create a mailbox!")
    password= None
    while password is None:
        password = input("Please enter a password for the newly created mailbox (SHOWN HERE IN PLAINTEXT): ")
        if len(password) < 8:
            print("Password must be 8 characters long")

    uuid = None

mail = f"{mail_alias}@{domain_fqdn}"
print(f"All mail to an @{domain_fqdn} address (starting with 2 alphabetic characters) will be redirected to {mail}")
input("Press enter to apply.")

# Permutations
alphabet = "abcdefghijklmnopqrstuvwxyz"
perm = product(alphabet, repeat=2)
permstar = map(lambda item: ''.join(item) + "*", perm)

print("Sending request. It can take a while for Gandi to reply to the request.")
if uuid is None:
    data = {
        "password": password,
        "mailbox_type": "standard",
        "login": mail_alias,
        "aliases": list(permstar)
    }
    res = api_post(f"https://api.gandi.net/v5/email/mailboxes/{domain_fqdn}", data)
    if res.status_code != 202:
        print(f"Something went wrong: {res.status_code}")
        print(res.text)
        exit(1)
else:
    data = {"aliases": list(permstar)}
    res = api_patch(f"https://api.gandi.net/v5/email/mailboxes/{domain_fqdn}/{uuid}", data)
    if res.status_code != 202:
        print(f"Something went wrong: {res.status_code}")
        print(res.text)
        exit(1)



print()
print()
print("Done! You will now receive all email to addresses that start with two alphabetic characters.")
print("If this script was useful to you, please consider donating :) https://paypal.me/wardsegers")