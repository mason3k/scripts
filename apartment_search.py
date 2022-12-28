from __future__ import annotations
import contextlib
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import smtplib, ssl
import re
from functools import cached_property
from abc import ABC, abstractmethod
import _secrets

DESIRED_MONTHS = range(3, 6)


class ApartmentSite(ABC):
    def __init__(self):
        self.html = self.get_html()

    @property
    @abstractmethod
    def url(self) -> str:
        """The url of the website to parse"""
        ...

    def get_html(self) -> str:
        page = urlopen(self.url)
        html_bytes = page.read()
        return html_bytes.decode("utf-8")

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


class MiddletonCenter(TWallSite):
    @property
    def url(self) -> str:
        return "https://twall.appfolio.com/listings?1551932808827&filters%5Bproperty_list%5D=MIDDLETON%20CENTER%20ALL%20PHASES"


class ConservancyBend(TWallSite):
    @property
    def url(self) -> str:
        return "https://twall.appfolio.com/listings?1552018640986&amp;filters%5Bproperty_list%5D=CONSERVANCY%20BEND"


class WingraCenter(ApartmentSite):
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
                        availability = int(content.split("/", 1)[0]) in range(2, 7)
                elif content.startswith("2 bd"):
                    bedrooms = True
                if availability and bedrooms:
                    msg += dl.get_text()

        return msg


class WingraShores(ApartmentSite):
    @property
    def url(self) -> str:
        return "https://jmichaelrealestate.com/property/2628-arbor-drive/"

    def get_html(self) -> str:
        req = Request(
            url=self.url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return urlopen(req).read().decode()

    @cached_property
    def available_apartments_msg(self) -> str:
        msg = ""
        for href in self.soup.find_all(href=re.compile("unit")):
            link = href.attrs["href"]
            req = Request(url=link, headers={"User-Agent": "Mozilla/5.0"})
            sub_html = urlopen(req).read().decode()
            sub_soup = BeautifulSoup(sub_html, "html.parser")
            available = sub_soup.find(
                "strong", text=re.compile("(?i)available")
            ).next_sibling
            if int(available.split("/", 1)[0]) in DESIRED_MONTHS:
                msg += (
                    f"Wingra Shores apartment available: {sub_soup.find('title').text}"
                )

        return msg


def main():
    try:
        sites: tuple[ApartmentSite] = (
            WingraCenter(),
            MiddletonCenter(),
            WingraShores(),
            ConservancyBend(),
        )
        msg = "\n\n".join(site.available_apartments_msg for site in sites)
    except Exception as e:
        msg = f"Error in apartment script! {e}"
    if not msg.strip():
        return
    else:
        email_results(msg)


def email_results(msg):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = _secrets.EMAIL  # Enter your address
    receiver_email = _secrets.EMAIL  # Enter receiver address
    message = """\
        Subject: New Apartment Opening

        """
    message += msg

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, _secrets.PASSWORD)
        server.sendmail(sender_email, receiver_email, message)

if __name__ == "__main__":
    main()
