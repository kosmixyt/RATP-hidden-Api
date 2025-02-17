import requests
from urllib.parse import quote
import time
import os
from curl_cffi import requests
import json
from bs4 import BeautifulSoup


token = "cocasse"
base_url = f"http://host.docker.internal:3000/req?token={token}&url="

cf = None


class Arret:
    def __init__(self, status: int, name: int, ligne: "Ligne", id: str):  # Use forward reference for type hint
        self.status = status
        self.name = name
        self.ligne = ligne
        self.id = id

    def get_horaire(self, date: str, time: str) -> dict:
        # date must be in the format yyyy-mm-dd, time in hh:mm
        url = f"https://www.ratp.fr/horaires/blocs-horaires-next-passages/busratp/{self.ligne.id}/{self.id}?stopPlaceName={quote(self.name)}&type=later&departure_date={date}&departure_time={time}"
        print(url)
        headers, cookies = get_header_and_cookies(cf)
        res = requests.get(url, headers=headers, cookies=cookies, impersonate="chrome110")
        raw_text = res.text
        # Process the text to handle escape sequences
        processed_text = raw_text.encode("utf-8").decode("unicode_escape")
        processed_text = processed_text.replace(r"\/", "/")
        soup = BeautifulSoup(processed_text, 'html.parser')
        results = {}
        # Each timetable container corresponds to one destination.
        for container in soup.find_all("div", class_="ixxi-horaire-result-timetable"):
            dest_tag = container.find("span", class_="destination_label")
            if not dest_tag:
                continue
            destination = dest_tag.get_text(strip=True)
            tables = container.find_all("table", class_="timetable no_train_network is_busratp")
            # Ensure there are at least two tables: one for next passages and one for premier/dernier passages.
            if len(tables) < 2:
                continue
            # Extract passage times from the first table.
            passage_times = []
            for tr in tables[0].find_all("tr", class_="body-busratp"):
                td = tr.find("td", class_="time_label")
                if td:
                    passage_times.append(td.get_text(strip=True))
            # Extract premier and dernier passages from the second table.
            row = tables[1].find("tr", class_="body-rer")
            if row:
                premier = row.find("span", class_="first-wrap").get_text(strip=True)
                dernier = row.find("span", class_="last-wrap").get_text(strip=True)
            else:
                premier, dernier = None, None
            results[destination] = {
                "passages": passage_times,
                "premier": premier,
                "dernier": dernier
            }
        return results

class Ligne:
    def __init__(self, nom: str, id: str, picto: str, plan: str, nombre: int):
        self.nom = nom
        self.id = id;
        self.nombre = nombre

        self.picto = "https://www.ratp.fr" + picto
        self.plan = "https://www.ratp.fr" + plan
        self.pdfplan = "https://www.ratp.fr" + plan.replace("png", "pdf")
        self.arrets = []
    def get_arrets(self):
        url = f"https://www.ratp.fr/horaires/api/getStopPoints/busratp/{self.nombre}/{self.id}"
        print(url)
        headers, cookies = get_header_and_cookies(cf)
        res = requests.get(url, headers=headers, cookies=cookies, impersonate="chrome110")
        alls = []
        for arret in res.json():
            alls.append(Arret(arret["status"], arret["name"], self, arret["stop_place_id"]))
        self.arrets = alls
        return alls
    def get_arretByName(self, name: str) -> Arret:
        if len(self.arrets) == 0:
            self.get_arrets()
        for arret in self.arrets:
            if arret.name == name:
                return arret
        return None


    



def get_cloudflare(url: str) -> dict:
    url = f"{base_url}{quote(url)}"
    res = requests.get(url, headers={"Authorization": "cocasse"})
    return res.json()

def get_header_and_cookies(cf) -> (dict, dict):
    headers = {
        "User-Agent": cf["User-Agent"],
    }
    cookies = {
    }
    for cookie in cf["cookies"]:
        cookies[cookie["name"]] = cookie["value"]
    return headers, cookies


def get_perturbation(busLine: int, cf) -> str:
    headers, cookies = get_header_and_cookies(cf)
    for attempt in range(3):  # Retry up to 3 times
        res = requests.get(f"https://www.ratp.fr/horaires/api/getTrafficEventsLive/busratp/{busLine}", headers=headers, cookies=cookies, impersonate="chrome110")
        if "Just a moment..." not in res.text:
            json = res.json()
            if "perturbation" in json:
                return json["perturbation"]
            else:
                return None;
        print("Cloudflare Captured, retrying...")
        time.sleep(5)  # Wait for 5 seconds before retrying
    raise Exception("Cloudflare Captured after 3 attempts")



def get_ligne(ligne: int) -> Ligne:
    headers, cookies = get_header_and_cookies(cf)
    res = requests.get(f"https://www.ratp.fr/horaires/api/getLinesAutoComplete/busnoctilien/{ligne}?to=fo&cache=true", headers=headers, cookies=cookies, impersonate="chrome110")
    json = res.json()
    if len(json) != 1:
        raise Exception(f"Ligne not found {len(json)}")
    return Ligne(json[0]["name"], json[0]["id"], json[0]["pictoV2"], json[0]["pngPlan"], int(json[0]["code"]))





start = time.time()
ligne = 258
cf = get_cloudflare(f"https://www.ratp.fr/horaires/api/getTrafficEventsLive/busratp/{ligne}")
ln = get_ligne(ligne)
print(ln.nom)
print(ln.get_arrets())
arret = (ln.get_arretByName("La Défense-Métro-RER-Tramway"))
if arret is None:
    raise Exception("Arret not found")
text = arret.get_horaire("2025-02-17", "15:20")
print(text)