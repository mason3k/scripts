from __future__ import annotations
import contextlib
import httpx
from bs4 import BeautifulSoup
import smtplib, ssl
import re
from functools import cached_property
from abc import ABC, abstractmethod
import _secrets
from email.message import EmailMessage
from urllib.parse import urlparse

DESIRED_MONTHS = range(3, 6)


class ApartmentSite(ABC):
    def __init__(self):
        self.html = self.get_html()

    @property
    def name(self) -> str:
        return urlparse(self.url).netloc

    @property
    @abstractmethod
    def url(self) -> str:
        """The url of the website to parse"""
        ...

    def get_html(self, *args, **kwargs) -> str:
        r = httpx.get(self.url, *args, **kwargs)
        r.raise_for_status()
        return r.text

    def __bool__(self) -> bool:
        return bool(self.available_apartments_msg)

    @cached_property
    def soup(self) -> BeautifulSoup:
        return BeautifulSoup(self.html, "html.parser")

    @cached_property
    @abstractmethod
    def available_apartments_msg(self) -> str:
        """Should return a descriptive message of the available apartments
        if there are any, otherwise the empty string or None"""
        ...


class TWallSite(ApartmentSite):
    """Base class for apartments listed by TWall Enterprise"""

    @cached_property
    def available_apartments_msg(self) -> str:
        msg = ""
        for dl in self.soup.find_all("dl"):
            availability = False
            bedrooms = False
            for dd in dl.find_all("dd"):
                content = str(dd.get_text())
                dd_class = dd["class"]
                if len(dd_class) > 1 and dd_class[1] == "js-listing-available":
                    availability = content.startswith(
                        tuple(str(month) for month in DESIRED_MONTHS)
                    )
                elif content.startswith("2 bd"):
                    bedrooms = True
                if all((availability, bedrooms)):
                    msg += dl.get_text()
                    break
        return msg


class VeritasSite(ApartmentSite):
    WANTED_APTS = [
        "108",
        "210",
        "310",
        "410",
        "337",
        "204",
        "304",
        "404",
        "104",
    ]

    @property
    def name(self) -> str:
        return "Veritas Village"

    @property
    def url(self):
        return "https://twall.appfolio.com/listings?1552018640986&filters%5Bproperty_list%5D=VERITAS%20VILLAGE%2C%20LLC"

    @cached_property
    def available_apartments_msg(self) -> str:
        msg = ""
        for dl in self.soup.find_all("dl"):
            bedrooms = False
            availability = False
            apt_addr = ";".join(
                address.get_text()
                for address in dl.parent.parent.select("span.u-pad-rm")
            )
            desired_apts = any(
                wanted_apt in apt_addr for wanted_apt in self.WANTED_APTS
            )
            for dd in dl.find_all("dd"):
                content = str(dd.get_text())
                dd_class = dd["class"]
                if len(dd_class) > 1 and dd_class[1] == "js-listing-available":
                    availability = content.startswith(
                        tuple(str(month) for month in DESIRED_MONTHS)
                    )
                elif content.startswith(("Studio", "1")):
                    bedrooms = True
                if all((availability, desired_apts, bedrooms)):
                    msg += dl.get_text()

        return msg


class MiddletonCenterSite(TWallSite):
    @property
    def name(self) -> str:
        return "Middleton Center"

    @property
    def url(self) -> str:
        return "https://twall.appfolio.com/listings?1551932808827&filters%5Bproperty_list%5D=MIDDLETON%20CENTER%20ALL%20PHASES"


class ConservancyBendSite(TWallSite):
    @property
    def name(self) -> str:
        return "Conservancy Bend"

    @property
    def url(self) -> str:
        return "https://twall.appfolio.com/listings?1552018640986&amp;filters%5Bproperty_list%5D=CONSERVANCY%20BEND"


class WingraCenterSite(ApartmentSite):
    @property
    def name(self) -> str:
        return "Wingra Center"

    @property
    def url(self) -> str:
        return "https://brunerrealty.appfolio.com/listings?1665708928491&filters%5Border_by%5D=date_posted"

    @cached_property
    def available_apartments_msg(self) -> str:
        msg = ""
        for dl in self.soup.find_all("dl"):
            bedrooms = False
            availability = False
            apt_addr = ";".join(
                address.get_text()
                for address in dl.parent.parent.select("span.u-pad-rm")
            )
            if "arbor" not in apt_addr.lower():
                continue
            for dd in dl.find_all("dd"):
                content = str(dd.get_text())
                dd_class = dd["class"]
                if len(dd_class) > 1 and dd_class[1] == "js-listing-available":
                    with contextlib.suppress(ValueError):
                        availability = int(content.split("/", 1)[0]) in DESIRED_MONTHS
                elif content.startswith("2 bd"):
                    bedrooms = True
                if availability and bedrooms:
                    msg += dl.get_text()

        return msg


class ValenciaSite(ApartmentSite):
    @property
    def name(self) -> str:
        return "Valencia"

    @property
    def url(self):
        return "https://primeurbanproperties.com/wp-content/themes/primeurbanproperties/ajax/get_units.php"

    def get_html(self) -> str:
        headers = {
            "authority": "primeurbanproperties.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "dnt": "1",
            "origin": "https://primeurbanproperties.com",
            "referer": "https://primeurbanproperties.com/property/valencia-place/",
            "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }

        data = {
            "property": "41",
            "den": "0",
            "bedrooms": "-1",
            "date": "05/01/2023",
            "sort": "price-down",
            "aprtlink": "1",
        }

        r = httpx.post(
            "https://primeurbanproperties.com/wp-content/themes/primeurbanproperties/ajax/get_units.php",
            headers=headers,
            data=data,
        )
        r.raise_for_status()

        return r.text

    @cached_property
    def available_apartments_msg(self) -> str:
        msg = ""
        for unit in self.soup.find_all(class_="unit-card"):
            unit_msg = '\n'.join(unit.stripped_strings)
            msg += f"{unit_msg} \n\n"
        return msg


class WingraShoresSite(ApartmentSite):
    @property
    def name(self) -> str:
        return "Wingra Shores"

    @property
    def url(self) -> str:
        return "https://jmichaelrealestate.com/property/2628-arbor-drive/"

    def get_html(self) -> str:
        return super().get_html(headers={"User-Agent": "Mozilla/5.0"})

    @cached_property
    def available_apartments_msg(self) -> str:
        msg = ""
        for href in self.soup.find_all(href=re.compile("unit")):
            link = href.attrs["href"]
            r = httpx.get(url=link, headers={"User-Agent": "Mozilla/5.0"})
            sub_soup = BeautifulSoup(r.text, "html.parser")
            available = sub_soup.find(
                "strong", text=re.compile("(?i)available")
            ).next_sibling
            if int(available.split("/", 1)[0]) in DESIRED_MONTHS:
                msg += (
                    f"Wingra Shores apartment available: {sub_soup.find('title').text}"
                )

        return msg


from email.message import EmailMessage


def main():
    try:
        sites: tuple[ApartmentSite] = (
            WingraCenterSite(),
            MiddletonCenterSite(),
            WingraShoresSite(),
            ConservancyBendSite(),
            ValenciaSite(),
        )
        msg = "\n\n".join(
            f"{site.name}\n{site.url}\n{msg}"
            for site in sites
            if (msg := site.available_apartments_msg)
        )
    except Exception as e:
        msg = f"Error in apartment script! {e}"
    if not msg.strip():
        return
    else:
        email_results(msg)


def build_email_message(msg: str) -> EmailMessage:
    email_msg = EmailMessage()
    email_msg.set_content(msg)
    email_msg["Subject"] = "New apartment opening"
    email_msg["From"] = _secrets.EMAIL  # Enter your address
    email_msg["To"] = _secrets.EMAIL  # Enter receiver address
    return email_msg


def email_results(msg: str) -> None:
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    email_msg = build_email_message(msg)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(_secrets.EMAIL, _secrets.PASSWORD)
        server.send_message(email_msg)


if __name__ == "__main__":
    main()
