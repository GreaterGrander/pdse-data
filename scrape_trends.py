#!/usr/bin/env python3
"""
Pulls real daily Wikipedia pageview counts for a list of public-domain
characters from the official, free, keyless Wikimedia Pageviews API, and
writes/updates data.json in the repo root.

No API key, no pip installs, no rate-limit workarounds needed -- just
Python's standard library. This is the MVP-simple version.
"""

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"
HISTORY_DAYS = 14   # how many days of daily pageviews to pull per character

# Wikimedia asks every API client to identify itself with a real User-Agent.
# Put a real contact (your site URL or email) here before running.
USER_AGENT = "PDSE-Bot/1.0 (greaterandgrander@gmail.com)"

# (symbol, exact Wikipedia article title) -- add more rows to scale past 18.
# Titles must match the article exactly as it appears in the en.wikipedia.org
# URL (with spaces instead of underscores). If a title is wrong, that row
# just falls back to a flat line instead of breaking the whole run.
CHARACTERS = [
    # --- Original board ---
    ("SHLK", "Sherlock Holmes"),
    ("DRAC", "Dracula"),
    ("FRNK", "Frankenstein's monster"),
    ("DRFR", "Victor Frankenstein"),
    ("ALIC", "Alice (Wonderland)"),
    ("PETR", "Peter Pan"),
    ("ROBH", "Robin Hood"),
    ("ZORR", "Zorro"),
    ("TARZ", "Tarzan"),
    ("HYDE", "Mr. Hyde"),
    ("SNOW", "Snow White"),
    ("CNDR", "Cinderella"),
    ("PINO", "Pinocchio"),
    ("QUAS", "Quasimodo"),
    ("PHAN", "Erik (The Phantom of the Opera)"),
    ("AHAB", "Captain Ahab"),
    ("HOOK", "Captain Hook"),
    ("MHAT", "Mad Hatter"),
    ("DQUI", "Don Quixote"),
    ("ATLA", "Atlas (mythology)"),
    ("ELBE", "Elizabeth Bennet"),
    ("MRDA", "Mr. Darcy"),
    ("BENN", "Bennet family"),
    ("GEWI", "George Wickham"),
    ("WICO", "Mr William Collins"),  # verify (may be "Mr. Collins")
    ("LCDB", "Lady Catherine de Bourgh"),
    ("ISHM", "Ishmael (Moby-Dick)"),
    ("MOBY", "Moby_Dick_(whale)"),
    ("WHIT", "White Rabbit"),
    ("CATP", "Caterpillar (Alice's Adventures in Wonderland)"),
    ("CHES", "Cheshire Cat"),
    ("HARE", "March Hare"),
    ("QUEN", "Queen of Hearts (Alice's Adventures in Wonderland)"),
    ("SACL", "Santa Claus"),
    ("MSCL", "Mrs. Claus"),
    ("EBSC", "Ebenezer Scrooge"),
    ("KRMP", "Krampus"),
 
    # --- Robin Hood ---
    ("FTUC", "Friar Tuck"),
    ("SHRF", "Sheriff of Nottingham"),
    ("LJHN", "Little John"),
    ("MARN", "Maid Marian"),
    ("WSCR", "Will Scarlet"),
    ("GISB", "Guy of Gisborne"),
 
    # --- Dracula ---
    ("MINA", "Mina Harker"),
    ("HELS", "Abraham Van Helsing"),
    ("JHRK", "Jonathan Harker"),
    ("RNFD", "Renfield"),  # verify
    ("LUCY", "Lucy Westenra"),
 
    # --- Sherlock Holmes ---
    ("MORI", "Professor Moriarty"),
    ("WATS", "Dr. Watson"),
    ("ADLR", "Irene Adler"),
    ("MYCR", "Mycroft Holmes"),
    ("LEST", "Inspector Lestrade"),
    ("HUDS", "Mrs. Hudson"),
 
    # --- Frankenstein ---
    ("BRDE", "Bride of Frankenstein"),  # the 1935 film article; character page title unverified
    ("LAVZ", "Elizabeth Lavenza"),  # verify
 
    # --- Wizard of Oz ---
    ("DORO", "Dorothy Gale"),
    ("SCRE", "Scarecrow (Oz)"),
    ("TINW", "Tin Woodman"),
    ("LION", "Cowardly Lion"),
    ("WIZD", "Wizard (Oz)"),  # verify
    ("WWOW", "Wicked Witch of the West"),
    ("GLND", "Glinda"),
    ("TOTO", "Toto (Oz)"),
 
    # --- Hunchback of Notre Dame ---
    ("FROL", "Claude Frollo"),
    ("ESME", "Esmeralda (The Hunchback of Notre-Dame)"),  # verify
 
    # --- Alice in Wonderland / Looking-Glass ---
    ("JABB", "Jabberwocky"),
    ("TWDL", "Tweedledum and Tweedledee"),
    ("HUMP", "Humpty Dumpty"),
 
    # --- Jekyll & Hyde ---
    ("JEKL", "Strange Case of Dr Jekyll and Mr Hyde"),
 
    # --- Cthulhu Mythos ---
    ("CTHU", "Cthulhu"),
    ("NYAR", "Nyarlathotep"),
    ("AZTH", "Azathoth"),
 
    # --- Greek mythology ---
    ("HRCL", "Heracles"),
    ("ZEUS", "Zeus"),
    ("HERA", "Hera"),
    ("PERS", "Persephone"),
    ("HELN", "Helen of Troy"),
    ("ARES", "Ares"),
    ("ODYS", "Odysseus"),
    ("ATHN", "Athena"),
    ("APOL", "Apollo"),
    ("ARTM", "Artemis"),
    ("POSE", "Poseidon"),
    ("HADE", "Hades"),
    ("APHR", "Aphrodite"),
    ("HRMS", "Hermes"),
    ("DION", "Dionysus"),
    ("ACHL", "Achilles"),
    ("PRSU", "Perseus"),
    ("MEDU", "Medusa"),
    ("THES", "Theseus"),
    ("MINO", "Minotaur"),
    ("PAND", "Pandora"),
    ("PROM", "Prometheus"),
    ("ORPH", "Orpheus"),
 
    # --- American folklore ---
    ("BUNY", "Paul Bunyan"),
    ("BABE", "Babe the Blue Ox"),
 
    # --- Treasure Island ---
    ("LJSL", "Long John Silver"),
    ("JIMH", "Jim Hawkins"),
 
    # --- Jules Verne ---
    ("NEMO", "Captain Nemo"),
 
    # --- Arthurian legend ---
    ("ARTH", "King Arthur"),
    ("CAML", "Camelot"),
    ("GUIN", "Guinevere"),
    ("GLHD", "Galahad"),
    ("LNCL", "Lancelot"),
    ("MERL", "Merlin"),
    ("MORG", "Morgan le Fay"),
    ("MRDR", "Mordred"),
    ("GAWN", "Gawain"),
 
    # --- Adventure heroes ---
    ("QUAT", "Allan Quatermain"),
    ("SNBD", "Sinbad the Sailor"),
 
    # --- Sleepy Hollow ---
    ("HDLS", "Headless Horseman"),
    ("ICHA", "Ichabod Crane"),
 
    # --- Arabian Nights ---
    ("ALAD", "Aladdin"),
    ("ALBB", "Ali Baba"),
    ("SCHE", "Scheherazade"),
 
    # --- Beowulf ---
    ("BEOW", "Beowulf (hero)"),
    ("GREN", "Grendel"),
    ("GRMO", "Grendel's mother"),
    ("HROT", "Hrothgar"),
 
    # --- Wilde / Swift ---
    ("DGRY", "Dorian Gray"),  # verify
    ("GULV", "Lemuel Gulliver"),
 
    # --- Mark Twain ---
    ("HUCK", "Huckleberry Finn"),
    ("TSWY", "Tom Sawyer"),
    ("BECK", "Becky Thatcher"),
 
    # --- The Three Musketeers ---
    ("DART", "D'Artagnan"),
    ("ATHO", "Athos (musketeer)"),  # verify
    ("PORT", "Porthos"),  # verify
    ("ARAM", "Aramis"),  # verify
    ("MILA", "Milady de Winter"),
 
    # --- Folklore & fairy tales ---
    ("NESS", "Loch Ness Monster"),
    ("LRRH", "Little Red Riding Hood"),
    ("BBWF", "Big Bad Wolf"),
    ("RAPU", "Rapunzel"),
    ("WRWF", "Werewolf"),
    ("PIPR", "Pied Piper of Hamelin"),
    ("MUMY", "Mummy"),
    ("GEPP", "Geppetto"),
 
    # --- Norse mythology ---
    ("THOR", "Thor"),
    ("ODIN", "Odin"),
    ("FREY", "Freyja"),
    ("LOKI", "Loki"),
    ("FRGG", "Frigg"),
    ("BALD", "Baldr"),
    ("HEIM", "Heimdallr"),
    ("FENR", "Fenrir"),
 
    # --- H.G. Wells ---
    ("MORL", "Morlock"),
 
    # --- Death ---
    ("DEAT", "Death (personification)"),
    ("GRIM", "Grim Reaper"),
 
    # --- Bible ---
    ("DAVD", "David"),
    ("GOLI", "Goliath"),
    ("JESU", "Jesus"),
    ("MOSE", "Moses"),
    ("NOAH", "Noah"),
    ("ADAM", "Adam"),
    ("EVEE", "Eve"),
    ("CAIN", "Cain"),
    ("SMSN", "Samson"),
    ("SOLO", "Solomon"),
    ("SATN", "Satan"),
    ("JUDS", "Judas Iscariot"),
    ("JONA", "Jonah"),
 
    # --- Shakespeare ---
    ("ROME", "Romeo Montague"),
    ("JULI", "Juliet Capulet"),
    ("MERC", "Mercutio"),
    ("TYBL", "Tybalt"),
    ("HAML", "Prince Hamlet"),  # verify
    ("OPHE", "Ophelia"),
 
    # --- Faust ---
    ("FAUS", "Faust"),
    ("MEPH", "Mephistopheles"),
 
    # --- A Christmas Carol ---
    ("BCRT", "Bob Cratchit"),
    ("TTIM", "Tiny Tim"),
    ("MRLY", "Jacob Marley"),
]


def fetch_pageviews(article):
    """Returns a list of daily view counts for the last HISTORY_DAYS days."""
    end = datetime.utcnow().date() - timedelta(days=1)  # yesterday (today is incomplete)
    start = end - timedelta(days=HISTORY_DAYS - 1)
    title = urllib.parse.quote(article.replace(" ", "_"), safe="")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/user/{title}/daily/"
        f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        return [item["views"] for item in data.get("items", [])]
    except Exception as e:
        print(f"Failed to fetch '{article}': {e}")
        return []


def to_index(views):
    """Compresses raw daily view counts onto a 0-100-ish scale so the
    board's existing price formula (unchanged) still looks right."""
    return min(99, round(math.sqrt(max(views, 0))))


def main():
    out = []
    for symbol, article in CHARACTERS:
        raw = fetch_pageviews(article)
        hist = [to_index(v) for v in raw] if raw else [10] * HISTORY_DAYS
        out.append([symbol, article, hist])
        time.sleep(0.5)  # polite pause; nowhere near Wikimedia's limits

    DATA_FILE.write_text(json.dumps(out, indent=2))
    print(f"Wrote {len(out)} characters to {DATA_FILE}")


if __name__ == "__main__":
    main()
