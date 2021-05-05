from bs4 import BeautifulSoup
import requests
url = "https://www.drugs.com/comments/abaloparatide/for-osteoporosis.html"
#url = ""
r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser")
# conditions = soup.find("select", attrs={"name":"condSelect"}).find_all("option")
# conds = {condition.text.split(" (")[0] : ROOT+condition['value'] for condition in conditions if not "All conditions" in condition.text}
soup.find("h1").text.split(" to treat ")[-1]