"""Registry of verified-scrapable news sites, grouped by research field.

Every entry here was live-probed: feed reachable, per-item dates parseable, the
content selector yields the full public article body, and images extract. Sites
that failed any of those checks are listed in README_NewsScraper.md with the
reason -- do not re-add them without re-verifying.

Run `python -B verify_sites.py` to re-check every entry after upstream changes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Site:
    name: str
    homepage: str
    feed: str | None
    content_selectors: tuple[str, ...]
    title_selectors: tuple[str, ...] = ("article h1", "main h1", "h1")
    hero_selectors: tuple[str, ...] = ()
    field: str = "science"
    low_volume: bool = False


# Display order of the category dropdown.
FIELDS: dict[str, str] = {
    "science": "Science & technology",
    "military": "Military & defense",
    "space": "Space & aviation",
    "physics": "Physics & quantum",
    "chemistry": "Chemistry & chemical industry",
    "materials": "Materials & nanotechnology",
    "agriculture": "Agriculture",
    "livestock": "Livestock & veterinary",
    "fisheries": "Fisheries & aquaculture",
    "food": "Food industry",
    "light_industry": "Light industry",
    "heavy_industry": "Heavy industry & machinery",
    "metals": "Metals & mining",
    "energy": "Power & energy",
    "geoscience": "Geography, geology & hydrology",
    "environment": "Environment & waste",
    "computing": "Computing & internet",
    "ai": "Artificial intelligence",
    "electronics": "Electronics & semiconductors",
    "robotics": "Robotics & automation",
    "medical": "Medicine & biotechnology",
    "medical_tech": "Medical technology & imaging",
    "transport": "Transport, shipping & rail",
    "construction": "Construction & urban development",
}


SITES: dict[str, Site] = {
    # ------------------------------------------------------------------ science
    "SciTechDaily": Site(
        "SciTechDaily", "https://scitechdaily.com/", None,
        ("article .entry-content", ".post-content.entry-content"),
        field="science",
    ),
    "ScienceDaily": Site(
        "ScienceDaily", "https://www.sciencedaily.com/",
        "https://www.sciencedaily.com/rss/all.xml", ("#story_text",),
        field="science",
    ),
    "Science News Explores": Site(
        "Science News Explores", "https://www.snexplores.org/",
        "https://www.snexplores.org/feed",
        ("article .single__content___jOVhr", "article .rich-text", "article"),
        field="science",
    ),
    "ScienceAlert": Site(
        "ScienceAlert", "https://www.sciencealert.com/",
        "https://www.sciencealert.com/feed", ("article .entry-content",),
        field="science",
    ),
    "Live Science": Site(
        "Live Science", "https://www.livescience.com/",
        "https://www.livescience.com/feeds/all", (".article__body",),
        field="science",
    ),
    "Sci.News": Site(
        "Sci.News", "https://www.sci.news/",
        "https://www.sci.news/feed", ("article .entry-content",),
        field="science",
    ),
    "Nature News": Site(
        "Nature News", "https://www.nature.com/",
        "https://www.nature.com/nature.rss", ("main article",),
        field="science",
    ),
    "New Atlas": Site(
        "New Atlas", "https://newatlas.com/",
        "https://newatlas.com/index.rss", ("main article",),
        field="science",
    ),
    "Innovation News Network": Site(
        "Innovation News Network", "https://www.innovationnewsnetwork.com/",
        "https://www.innovationnewsnetwork.com/feed/", (".td-post-content",),
        field="science",
    ),
    "Knowable Magazine": Site(
        "Knowable Magazine", "https://knowablemagazine.org/",
        "https://knowablemagazine.org/rss", (".article-text",),
        field="science",
    ),

    # ----------------------------------------------------------------- military
    "Defense News": Site(
        "Defense News", "https://www.defensenews.com/",
        "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
        ("article",), field="military",
    ),
    "Defense One": Site(
        "Defense One", "https://www.defenseone.com/",
        "https://www.defenseone.com/rss/all/", (".content-body",),
        field="military",
    ),
    "DefenseScoop": Site(
        "DefenseScoop", "https://defensescoop.com/",
        "https://defensescoop.com/feed/", ("main article",),
        field="military",
    ),
    "Naval News": Site(
        "Naval News", "https://www.navalnews.com/",
        "https://www.navalnews.com/feed/",
        (".elementor-widget-theme-post-content",), field="military",
    ),
    "The War Zone": Site(
        "The War Zone", "https://www.twz.com/",
        "https://www.twz.com/feed", ("article .entry-content",),
        field="military",
    ),
    "Breaking Defense": Site(
        "Breaking Defense", "https://breakingdefense.com/",
        "https://breakingdefense.com/feed/", ("article .content",),
        field="military",
    ),
    "Defence Blog": Site(
        "Defence Blog", "https://defence-blog.com/",
        "https://defence-blog.com/feed/", (".td-post-content",),
        field="military",
    ),
    "Overt Defense": Site(
        "Overt Defense", "https://www.overtdefense.com/",
        "https://www.overtdefense.com/feed/", ("main article",),
        field="military",
    ),
    "Naval Technology": Site(
        "Naval Technology", "https://www.naval-technology.com/",
        "https://www.naval-technology.com/feed/", (".article-content",),
        field="military",
    ),
    "Air Force Technology": Site(
        "Air Force Technology", "https://www.airforce-technology.com/",
        "https://www.airforce-technology.com/feed/", (".article-content",),
        field="military",
    ),

    # -------------------------------------------------------------------- space
    "Space.com": Site(
        "Space.com", "https://www.space.com/",
        "https://www.space.com/feeds/all", ("article",), field="space",
    ),
    "SpaceNews": Site(
        "SpaceNews", "https://spacenews.com/",
        "https://spacenews.com/feed/", ("article .entry-content",),
        field="space",
    ),
    "NASA": Site(
        "NASA", "https://www.nasa.gov/",
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        ("article .entry-content",), field="space",
    ),
    "Universe Today": Site(
        "Universe Today", "https://www.universetoday.com/",
        "https://www.universetoday.com/feed", (".article-content",),
        field="space",
    ),
    "Spaceflight Now": Site(
        "Spaceflight Now", "https://spaceflightnow.com/",
        "https://spaceflightnow.com/feed/", ("article .entry-content",),
        field="space",
    ),
    "SpaceDaily": Site(
        "SpaceDaily", "https://www.spacedaily.com/",
        "https://www.spacedaily.com/spacedaily.xml",
        ("article .entry-content",), field="space",
    ),

    # ------------------------------------------------------------------ physics
    "Physics World": Site(
        "Physics World", "https://physicsworld.com/",
        "https://physicsworld.com/feed/", ("article .entry-content",),
        field="physics",
    ),
    "The Quantum Insider": Site(
        "The Quantum Insider", "https://thequantuminsider.com/",
        "https://thequantuminsider.com/feed/",
        (".elementor-widget-theme-post-content",), field="physics",
    ),

    # ---------------------------------------------------------------- chemistry
    "Chemical Engineering": Site(
        "Chemical Engineering", "https://www.chemengonline.com/",
        "https://www.chemengonline.com/feed/", ("article",),
        field="chemistry",
    ),
    "Advanced Science News": Site(
        "Advanced Science News", "https://www.advancedsciencenews.com/",
        "https://www.advancedsciencenews.com/feed/", (".et_pb_post_content",),
        field="chemistry",
    ),

    # ---------------------------------------------------------------- materials
    "3D Printing Industry": Site(
        "3D Printing Industry", "https://3dprintingindustry.com/",
        "https://3dprintingindustry.com/feed/", ("article .entry-content",),
        field="materials",
    ),
    "Composites World": Site(
        "Composites World", "https://www.compositesworld.com/",
        "https://www.compositesworld.com/rss/articles", (".article-body",),
        field="materials",
    ),
    "Graphene Info": Site(
        "Graphene Info", "https://www.graphene-info.com/",
        "https://www.graphene-info.com/rss.xml", ("main article",),
        field="materials",
    ),
    "Plastics Today": Site(
        "Plastics Today", "https://www.plasticstoday.com/",
        "https://www.plasticstoday.com/rss.xml", (".ArticleBase-BodyContent",),
        field="materials",
    ),

    # -------------------------------------------------------------- agriculture
    "AgFunderNews": Site(
        "AgFunderNews", "https://agfundernews.com/",
        "https://agfundernews.com/feed", (".article-content",),
        field="agriculture",
    ),
    "Farm Progress": Site(
        "Farm Progress", "https://www.farmprogress.com/",
        "https://www.farmprogress.com/rss.xml", (".ArticleBase-BodyContent",),
        field="agriculture",
    ),
    "Farm Equipment": Site(
        "Farm Equipment", "https://www.farm-equipment.com/",
        "https://www.farm-equipment.com/rss/articles", (".article-body",),
        field="agriculture",
    ),
    "Seed World": Site(
        "Seed World", "https://www.seedworld.com/",
        "https://www.seedworld.com/feed/",
        (".elementor-widget-theme-post-content",), field="agriculture",
    ),
    "Modern Farmer": Site(
        "Modern Farmer", "https://modernfarmer.com/",
        "https://modernfarmer.com/feed/", ("main article",),
        field="agriculture", low_volume=True,
    ),

    # ---------------------------------------------------------------- livestock
    "Feedstuffs": Site(
        "Feedstuffs", "https://www.feedstuffs.com/",
        "https://www.feedstuffs.com/rss.xml",
        (".ArticleBase-Body", ".ArticleBase-BodyContent"),
        field="livestock",
    ),
    "Beef Magazine": Site(
        "Beef Magazine", "https://www.beefmagazine.com/",
        "https://www.beefmagazine.com/rss.xml", (".ArticleBase-BodyContent",),
        field="livestock",
    ),
    "National Hog Farmer": Site(
        "National Hog Farmer", "https://www.nationalhogfarmer.com/",
        "https://www.nationalhogfarmer.com/rss.xml", (".ArticleBase-BodyContent",),
        field="livestock",
    ),

    # ---------------------------------------------------------------- fisheries
    "Aquaculture Magazine": Site(
        "Aquaculture Magazine", "https://aquaculturemag.com/",
        "https://aquaculturemag.com/feed/",
        (".elementor-widget-theme-post-content",), field="fisheries",
    ),
    "Global Seafood Alliance": Site(
        "Global Seafood Alliance", "https://www.globalseafood.org/",
        "https://www.globalseafood.org/feed/", ("main article",),
        field="fisheries",
    ),
    "Undercurrent News": Site(
        "Undercurrent News", "https://www.undercurrentnews.com/",
        "https://www.undercurrentnews.com/feed/", ("article",),
        field="fisheries",
    ),

    # --------------------------------------------------------------------- food
    "Food Dive": Site(
        "Food Dive", "https://www.fooddive.com/",
        "https://www.fooddive.com/feeds/news/", ("article .article-body",),
        field="food",
    ),
    "Food Engineering": Site(
        "Food Engineering", "https://www.foodengineeringmag.com/",
        "https://www.foodengineeringmag.com/rss/articles", ("article .content",),
        field="food",
    ),
    "Food Safety News": Site(
        "Food Safety News", "https://www.foodsafetynews.com/",
        "https://www.foodsafetynews.com/feed/", ("main article",),
        field="food",
    ),

    # ----------------------------------------------------------- light industry
    "Textile World": Site(
        "Textile World", "https://www.textileworld.com/",
        "https://www.textileworld.com/feed/", (".td-post-content",),
        field="light_industry",
    ),
    "Innovation in Textiles": Site(
        "Innovation in Textiles", "https://www.innovationintextiles.com/",
        "https://www.innovationintextiles.com/rss/", ("section.body",),
        field="light_industry",
    ),
    "Apparel Resources": Site(
        "Apparel Resources", "https://apparelresources.com/",
        "https://apparelresources.com/feed/", ("article .entry-content",),
        field="light_industry",
    ),
    "Just Style": Site(
        "Just Style", "https://www.just-style.com/",
        "https://www.just-style.com/feed/", (".article-content",),
        field="light_industry",
    ),
    "Packaging Digest": Site(
        "Packaging Digest", "https://www.packagingdigest.com/",
        "https://www.packagingdigest.com/rss.xml", (".ArticleBase-BodyContent",),
        field="light_industry",
    ),

    # ----------------------------------------------------------- heavy industry
    "Assembly Magazine": Site(
        "Assembly Magazine", "https://www.assemblymag.com/",
        "https://www.assemblymag.com/rss/articles", ("article .content",),
        field="heavy_industry",
    ),
    "Modern Machine Shop": Site(
        "Modern Machine Shop", "https://www.mmsonline.com/",
        "https://www.mmsonline.com/rss/articles", (".article-body",),
        field="heavy_industry",
    ),
    "Production Machining": Site(
        "Production Machining", "https://www.productionmachining.com/",
        "https://www.productionmachining.com/rss/articles", (".article-body",),
        field="heavy_industry",
    ),
    "Plant Engineering": Site(
        "Plant Engineering", "https://www.plantengineering.com/",
        "https://www.plantengineering.com/feed/", ("article .entry-content",),
        field="heavy_industry",
    ),
    "Marine Log": Site(
        "Marine Log", "https://www.marinelog.com/",
        "https://www.marinelog.com/feed/", ("section.section-block",),
        field="heavy_industry",
    ),
    "Seatrade Maritime": Site(
        "Seatrade Maritime", "https://www.seatrade-maritime.com/",
        "https://www.seatrade-maritime.com/rss.xml", (".ArticleBase-BodyContent",),
        field="heavy_industry",
    ),

    # ------------------------------------------------------------------- metals
    "International Mining": Site(
        "International Mining", "https://im-mining.com/",
        "https://im-mining.com/feed/", (".post-content",), field="metals",
    ),
    "Mining Technology": Site(
        "Mining Technology", "https://www.mining-technology.com/",
        "https://www.mining-technology.com/feed/", (".article-content",),
        field="metals",
    ),
    "Northern Miner": Site(
        "Northern Miner", "https://www.northernminer.com/",
        "https://www.northernminer.com/feed/", ("article .entry-content",),
        field="metals",
    ),
    "Canadian Mining Journal": Site(
        "Canadian Mining Journal", "https://www.canadianminingjournal.com/",
        "https://www.canadianminingjournal.com/feed/", (".post-inner-content",),
        field="metals",
    ),
    "Australian Mining": Site(
        "Australian Mining", "https://www.australianmining.com.au/",
        "https://www.australianmining.com.au/feed/", (".entry-content",),
        field="metals",
    ),
    "Coal Age": Site(
        "Coal Age", "https://www.coalage.com/",
        "https://www.coalage.com/feed/", ("article .entry-content",),
        field="metals",
    ),
    "Light Metal Age": Site(
        "Light Metal Age", "https://www.lightmetalage.com/",
        "https://www.lightmetalage.com/feed/", ("article .entry-content",),
        field="metals",
    ),
    "Powder Metallurgy Review": Site(
        "Powder Metallurgy Review", "https://www.pm-review.com/",
        "https://www.pm-review.com/feed/", ("article .content",),
        field="metals",
    ),
    "Mining.com": Site(
        "Mining.com", "https://www.mining.com/",
        "https://www.mining.com/feed/", ("article .content",),
        field="metals",
    ),

    # ------------------------------------------------------------------- energy
    "Utility Dive": Site(
        "Utility Dive", "https://www.utilitydive.com/",
        "https://www.utilitydive.com/feeds/news/", ("article .article-body",),
        field="energy",
    ),
    "POWER Magazine": Site(
        "POWER Magazine", "https://www.powermag.com/",
        "https://www.powermag.com/feed/", ("article .article-body",),
        field="energy",
    ),
    "pv magazine": Site(
        "pv magazine", "https://www.pv-magazine.com/",
        "https://www.pv-magazine.com/feed/", (".entry-content",),
        field="energy",
    ),
    "Renewable Energy World": Site(
        "Renewable Energy World", "https://www.renewableenergyworld.com/",
        "https://www.renewableenergyworld.com/feed/", (".entry-content",),
        field="energy",
    ),
    "Electrek": Site(
        "Electrek", "https://electrek.co/",
        "https://electrek.co/feed/", (".post-content",), field="energy",
    ),
    "Energy Storage News": Site(
        "Energy Storage News", "https://www.energy-storage.news/",
        "https://www.energy-storage.news/feed/",
        (".elementor-widget-theme-post-content",), field="energy",
    ),
    "Solar Power World": Site(
        "Solar Power World", "https://www.solarpowerworldonline.com/",
        "https://www.solarpowerworldonline.com/feed/",
        ("article .entry-content",), field="energy",
    ),
    "Windpower Engineering": Site(
        "Windpower Engineering", "https://www.windpowerengineering.com/",
        "https://www.windpowerengineering.com/feed/",
        ("article .entry-content",), field="energy", low_volume=True,
    ),
    "World Nuclear News": Site(
        "World Nuclear News", "https://world-nuclear-news.org/",
        "https://world-nuclear-news.org/rss",
        ("div[itemprop='articleBody']",), field="energy",
    ),
    "Nuclear Engineering International": Site(
        "Nuclear Engineering International", "https://www.neimagazine.com/",
        "https://www.neimagazine.com/feed/", (".article-content",),
        field="energy", low_volume=True,
    ),
    "Power Engineering": Site(
        "Power Engineering", "https://www.power-eng.com/",
        "https://www.power-eng.com/feed/", (".entry-content",), field="energy",
    ),
    "Modern Power Systems": Site(
        "Modern Power Systems", "https://www.modernpowersystems.com/",
        "https://www.modernpowersystems.com/rss", (".article-content",),
        field="energy",
    ),
    "Offshore Wind Biz": Site(
        "Offshore Wind Biz", "https://www.offshorewind.biz/",
        "https://www.offshorewind.biz/feed/", (".article__body",), field="energy",
    ),

    # --------------------------------------------------------------- geoscience
    "Eos": Site(
        "Eos", "https://eos.org/", "https://eos.org/feed",
        ("article .entry-content",), field="geoscience",
    ),
    "AGU Newsroom": Site(
        "AGU Newsroom", "https://news.agu.org/",
        "https://news.agu.org/feed/", ("article .entry-content",),
        field="geoscience",
    ),
    "Geology Page": Site(
        "Geology Page", "https://www.geologypage.com/",
        "https://www.geologypage.com/feed", (".td-post-content",),
        field="geoscience",
    ),
    "Geospatial World": Site(
        "Geospatial World", "https://geospatialworld.net/",
        "https://geospatialworld.net/feed/",
        (".elementor-widget-theme-post-content",), field="geoscience",
    ),
    "Geography Realm": Site(
        "Geography Realm", "https://www.geographyrealm.com/",
        "https://www.geographyrealm.com/feed/", ("article .entry-content",),
        field="geoscience",
    ),
    "The Watchers": Site(
        "The Watchers", "https://watchers.news/",
        "https://watchers.news/feed/", ("article .entry-content",),
        field="geoscience",
    ),
    "Temblor": Site(
        "Temblor", "https://temblor.net/",
        "https://temblor.net/feed/", ("article .entry-content",),
        field="geoscience", low_volume=True,
    ),

    # -------------------------------------------------------------- environment
    "Waste Dive": Site(
        "Waste Dive", "https://www.wastedive.com/",
        "https://www.wastedive.com/feeds/news/", ("article .article-body",),
        field="environment",
    ),
    "Circular Online": Site(
        "Circular Online", "https://www.circularonline.co.uk/",
        "https://www.circularonline.co.uk/feed/", ("article .entry-content",),
        field="environment",
    ),
    "Envirotec Magazine": Site(
        "Envirotec Magazine", "https://envirotecmagazine.com/",
        "https://envirotecmagazine.com/feed/", (".td-post-content",),
        field="environment",
    ),
    "Mongabay": Site(
        "Mongabay", "https://news.mongabay.com/",
        "https://news.mongabay.com/feed/", ("main article",),
        field="environment",
    ),
    "Carbon Brief": Site(
        "Carbon Brief", "https://www.carbonbrief.org/",
        "https://www.carbonbrief.org/feed/", ("main article",),
        field="environment",
    ),
    "Yale Environment 360": Site(
        "Yale Environment 360", "https://e360.yale.edu/",
        "https://e360.yale.edu/feed.xml", (".article__body",),
        field="environment",
    ),

    # ---------------------------------------------------------------- computing
    "Ars Technica": Site(
        "Ars Technica", "https://arstechnica.com/",
        "https://feeds.arstechnica.com/arstechnica/index", (".post-content",),
        field="computing",
    ),
    "The Register": Site(
        "The Register", "https://www.theregister.com/",
        "https://www.theregister.com/headlines.atom", ("main article",),
        field="computing",
    ),
    "TechCrunch": Site(
        "TechCrunch", "https://techcrunch.com/",
        "https://techcrunch.com/feed/", (".entry-content",),
        field="computing",
    ),
    "Engadget": Site(
        "Engadget", "https://www.engadget.com/",
        "https://www.engadget.com/rss.xml", ("main article",),
        field="computing",
    ),
    "Tom's Hardware": Site(
        "Tom's Hardware", "https://www.tomshardware.com/",
        "https://www.tomshardware.com/feeds/all", ("article",),
        field="computing",
    ),
    "Computerworld": Site(
        "Computerworld", "https://www.computerworld.com/",
        "https://www.computerworld.com/feed/", ("article .entry-content",),
        field="computing",
    ),
    "InfoWorld": Site(
        "InfoWorld", "https://www.infoworld.com/",
        "https://www.infoworld.com/feed/", ("article .entry-content",),
        field="computing",
    ),
    "Network World": Site(
        "Network World", "https://www.networkworld.com/",
        "https://www.networkworld.com/feed/", ("article .entry-content",),
        field="computing",
    ),
    "BleepingComputer": Site(
        "BleepingComputer", "https://www.bleepingcomputer.com/",
        "https://www.bleepingcomputer.com/feed/", ("article",),
        field="computing",
    ),
    "The Hacker News": Site(
        "The Hacker News", "https://thehackernews.com/",
        "https://feeds.feedburner.com/TheHackersNews", (".post-body",),
        field="computing",
    ),
    "CIO Dive": Site(
        "CIO Dive", "https://www.ciodive.com/",
        "https://www.ciodive.com/feeds/news/", ("article .article-body",),
        field="computing",
    ),
    "Hackaday": Site(
        "Hackaday", "https://hackaday.com/",
        "https://hackaday.com/feed/", ("article .entry-content",),
        field="computing",
    ),

    # -------------------------------------------------- artificial intelligence
    "The Decoder": Site(
        "The Decoder", "https://the-decoder.com/",
        "https://the-decoder.com/feed/", ("article .entry-content",),
        field="ai",
    ),
    "AI Business": Site(
        "AI Business", "https://aibusiness.com/",
        "https://aibusiness.com/rss.xml", (".ArticleBase-Body",),
        field="ai",
    ),
    "Synced": Site(
        "Synced", "https://syncedreview.com/",
        "https://syncedreview.com/feed/", ("article .entry-content",),
        field="ai",
    ),

    # -------------------------------------------------------------- electronics
    "IEEE Spectrum": Site(
        "IEEE Spectrum", "https://spectrum.ieee.org/",
        "https://spectrum.ieee.org/feeds/feed.rss", (".body-description",),
        field="electronics",
    ),
    "EE Times": Site(
        "EE Times", "https://www.eetimes.com/",
        "https://www.eetimes.com/feed/", ("article",), field="electronics",
    ),
    "Semiconductor Engineering": Site(
        "Semiconductor Engineering", "https://semiengineering.com/",
        "https://semiengineering.com/feed/", (".post_cnt",),
        field="electronics",
    ),
    "Power Electronics News": Site(
        "Power Electronics News", "https://www.powerelectronicsnews.com/",
        "https://www.powerelectronicsnews.com/feed/",
        ("article .entry-content",), field="electronics",
    ),
    "EDN": Site(
        "EDN", "https://www.edn.com/",
        "https://www.edn.com/feed/", ("article .entry-content",),
        field="electronics",
    ),
    "Electronics Weekly": Site(
        "Electronics Weekly", "https://www.electronicsweekly.com/",
        "https://www.electronicsweekly.com/feed/", (".entry-content",),
        field="electronics",
    ),

    # ----------------------------------------------------------------- robotics
    "The Robot Report": Site(
        "The Robot Report", "https://www.therobotreport.com/",
        "https://www.therobotreport.com/feed/", ("article .entry-content",),
        field="robotics",
    ),
    "Drone Life": Site(
        "Drone Life", "https://dronelife.com/",
        "https://dronelife.com/feed/", ("article .entry-content",),
        field="robotics",
    ),
    "Manufacturing Dive": Site(
        "Manufacturing Dive", "https://www.manufacturingdive.com/",
        "https://www.manufacturingdive.com/feeds/news/",
        ("article .article-body",), field="robotics",
    ),

    # ------------------------------------------------------------------ medical
    "News-Medical": Site(
        "News-Medical", "https://www.news-medical.net/",
        "https://www.news-medical.net/syndication.axd?format=rss",
        ("div[itemprop='articleBody']",), field="medical",
    ),
    "GEN": Site(
        "GEN", "https://www.genengnews.com/",
        "https://www.genengnews.com/feed/", (".td-post-content",),
        field="medical",
    ),

    # ------------------------------------------------------- medical technology
    "Medical Design and Outsourcing": Site(
        "Medical Design and Outsourcing", "https://www.medicaldesignandoutsourcing.com/",
        "https://www.medicaldesignandoutsourcing.com/feed/",
        ("article .entry-content",), field="medical_tech",
    ),
    "MedTech Dive": Site(
        "MedTech Dive", "https://www.medtechdive.com/",
        "https://www.medtechdive.com/feeds/news/", ("article .article-body",),
        field="medical_tech",
    ),
    "Radiology Business": Site(
        "Radiology Business", "https://radiologybusiness.com/",
        "https://radiologybusiness.com/rss.xml", ("main article",),
        field="medical_tech",
    ),
    "Physics World Medical": Site(
        "Physics World Medical", "https://physicsworld.com/c/medical-physics/",
        "https://physicsworld.com/c/medical-physics/feed/",
        ("article .entry-content",), field="medical_tech",
    ),
    "Healthcare Dive": Site(
        "Healthcare Dive", "https://www.healthcaredive.com/",
        "https://www.healthcaredive.com/feeds/news/", ("article .article-body",),
        field="medical_tech",
    ),
    "MedPage Today": Site(
        "MedPage Today", "https://www.medpagetoday.com/",
        "https://www.medpagetoday.com/rss/headlines.xml",
        ("div[itemprop='articleBody']",), field="medical_tech",
    ),
    "Drug Discovery and Development": Site(
        "Drug Discovery and Development", "https://www.drugdiscoverytrends.com/",
        "https://www.drugdiscoverytrends.com/feed/", ("article .entry-content",),
        field="medical_tech",
    ),
    "Pharmaceutical Technology": Site(
        "Pharmaceutical Technology", "https://www.pharmaceutical-technology.com/",
        "https://www.pharmaceutical-technology.com/feed/", (".article-content",),
        field="medical_tech",
    ),

    # ---------------------------------------------------------------- transport
    "Railway Gazette": Site(
        "Railway Gazette", "https://www.railwaygazette.com/",
        "https://www.railwaygazette.com/rss", ("main article",),
        field="transport",
    ),
    "Marine Insight": Site(
        "Marine Insight", "https://www.marineinsight.com/",
        "https://www.marineinsight.com/feed/", ("article .entry-content",),
        field="transport",
    ),
    "gCaptain": Site(
        "gCaptain", "https://gcaptain.com/",
        "https://gcaptain.com/feed/", ("main.article .body",),
        field="transport",
    ),
    "Offshore Energy": Site(
        "Offshore Energy", "https://www.offshore-energy.biz/",
        "https://www.offshore-energy.biz/feed/", (".article__body",),
        field="transport",
    ),
    "Truck News": Site(
        "Truck News", "https://www.trucknews.com/",
        "https://www.trucknews.com/feed/", ("main article",),
        field="transport",
    ),
    "Supply Chain Dive": Site(
        "Supply Chain Dive", "https://www.supplychaindive.com/",
        "https://www.supplychaindive.com/feeds/news/",
        ("article .article-body",), field="transport",
    ),
    "The Maritime Executive": Site(
        "The Maritime Executive", "https://maritime-executive.com/",
        "https://maritime-executive.com/articles.rss", ("article",),
        field="transport",
    ),
    "Splash247": Site(
        "Splash247", "https://splash247.com/",
        "https://splash247.com/feed/", ("article .entry-content",),
        field="transport",
    ),
    "Port Technology": Site(
        "Port Technology", "https://www.porttechnology.org/",
        "https://www.porttechnology.org/feed/",
        (".elementor-widget-theme-post-content",), field="transport",
    ),
    "FreightWaves": Site(
        "FreightWaves", "https://www.freightwaves.com/",
        "https://www.freightwaves.com/feed", ("article .entry-content",),
        field="transport",
    ),

    # ------------------------------------------------------------- construction
    "Construction Dive": Site(
        "Construction Dive", "https://www.constructiondive.com/",
        "https://www.constructiondive.com/feeds/news/",
        ("article .article-body",),
        hero_selectors=("article figure.inside_story",), field="construction",
    ),
    "Smart Cities Dive": Site(
        "Smart Cities Dive", "https://www.smartcitiesdive.com/",
        "https://www.smartcitiesdive.com/feeds/news/",
        ("article .article-body",), field="construction",
    ),
    "ENR": Site(
        # /articles/ carry the full public body; /blogs/ posts are paywalled and
        # fail gracefully rather than saving a teaser.
        "ENR", "https://www.enr.com/",
        "https://www.enr.com/rss/articles", ("article .content",),
        field="construction",
    ),
    "Global Construction Review": Site(
        "Global Construction Review", "https://www.globalconstructionreview.com/",
        "https://www.globalconstructionreview.com/feed/",
        ("article .entry-content",), field="construction",
    ),
    "New Civil Engineer": Site(
        "New Civil Engineer", "https://www.newcivilengineer.com/",
        "https://www.newcivilengineer.com/feed/", ("article",),
        field="construction",
    ),
    "Architectural Record": Site(
        "Architectural Record", "https://www.architecturalrecord.com/",
        "https://www.architecturalrecord.com/rss/articles", ("article .content",),
        field="construction",
    ),
}


def sites_in_field(field: str) -> list[Site]:
    """Registered sites for one field key, in registry order."""
    return [site for site in SITES.values() if site.field == field]


def field_label(field: str) -> str:
    return FIELDS.get(field, field)


# ---------------------------------------------------- DPRK-Korean folder naming
# Scraped articles are filed in folders named `<category>_<sub-category>(문서-영문)`
# in DPRK Korean, e.g. 군사_장갑차(문서-영문), 콤퓨터_인공지능(문서-영문). The category
# is the field; the sub-category is fixed per source, reflecting what that source
# mostly covers. A source not listed here (e.g. one the user adds) falls back to
# DEFAULT_SUBCATEGORY.
DEFAULT_SUBCATEGORY = "새기술"

FIELD_CATEGORY: dict[str, str] = {
    "science": "과학기술",
    "military": "군사",
    "space": "우주항공",
    "physics": "물리",
    "chemistry": "화학",
    "materials": "재료",
    "agriculture": "농업",
    "livestock": "수의축산",
    "fisheries": "수산업",
    "food": "식료공업",
    "light_industry": "경공업",
    "heavy_industry": "중공업",
    "metals": "금속공업",
    "energy": "전력",
    "geoscience": "지리",
    "environment": "환경",
    "computing": "콤퓨터",
    "ai": "정보기술",
    "electronics": "전자",
    "robotics": "로보트",
    "medical": "의학",
    "medical_tech": "의료기술",
    "transport": "수송",
    "construction": "건설",
}

SITE_SUBCATEGORY: dict[str, str] = {
    # science (과학기술)
    "SciTechDaily": "새기술", "ScienceDaily": "종합과학",
    "Science News Explores": "청소년과학", "ScienceAlert": "과학상식",
    "Live Science": "생활과학", "Sci.News": "과학소식", "Nature News": "자연과학",
    "New Atlas": "최신기술", "Innovation News Network": "발명",
    "Knowable Magazine": "과학해설",
    # military (군사)
    "Defense News": "국방", "Defense One": "군사기술", "DefenseScoop": "군사기술",
    "Naval News": "함선", "The War Zone": "전쟁무기", "Breaking Defense": "국방속보",
    "Defence Blog": "무기", "Overt Defense": "군사장비",
    "Naval Technology": "해군", "Air Force Technology": "공군",
    # space (우주항공)
    "Space.com": "우주", "SpaceNews": "우주산업", "NASA": "우주개발",
    "Universe Today": "천문", "Spaceflight Now": "우주비행", "SpaceDaily": "우주소식",
    # physics (물리)
    "Physics World": "물리학", "The Quantum Insider": "양자기술",
    # chemistry (화학)
    "Chemical Engineering": "화학공학", "Advanced Science News": "첨단화학",
    # materials (재료)
    "3D Printing Industry": "3차원인쇄", "Composites World": "복합재료",
    "Graphene Info": "그라펜", "Plastics Today": "수지",
    # agriculture (농업)
    "AgFunderNews": "농업기술", "Farm Progress": "영농", "Farm Equipment": "농기계",
    "Seed World": "종자", "Modern Farmer": "현대농업",
    # livestock (수의축산)
    "Feedstuffs": "사료", "Beef Magazine": "소사육", "National Hog Farmer": "돼지사육",
    # fisheries (수산업)
    "Aquaculture Magazine": "양식", "Global Seafood Alliance": "양식", "Undercurrent News": "수산",
    # food (식료공업)
    "Food Dive": "식품산업", "Food Engineering": "식품공학", "Food Safety News": "식품안전",
    # light_industry (경공업)
    "Textile World": "방직", "Innovation in Textiles": "섬유기술",
    "Apparel Resources": "피복", "Just Style": "의류", "Packaging Digest": "포장",
    # heavy_industry (중공업)
    "Assembly Magazine": "조립생산", "Modern Machine Shop": "기계가공",
    "Production Machining": "정밀가공", "Plant Engineering": "공장설비",
    "Marine Log": "조선", "Seatrade Maritime": "해운",
    # metals (금속)
    "International Mining": "채굴", "Mining Technology": "채굴기술",
    "Northern Miner": "광산", "Canadian Mining Journal": "광업",
    "Australian Mining": "광산개발", "Coal Age": "탄광기술",
    "Light Metal Age": "경금속", "Powder Metallurgy Review": "분말야금",
    "Mining.com": "채취",
    # energy (전력)
    "Utility Dive": "전력공급", "POWER Magazine": "발전", "pv magazine": "태양광",
    "Renewable Energy World": "재생에네르기", "Electrek": "전기자동차",
    "Energy Storage News": "축전지", "Solar Power World": "태양전지",
    "Windpower Engineering": "풍력", "World Nuclear News": "원자력",
    "Nuclear Engineering International": "원자로", "Power Engineering": "전력공학",
    "Modern Power Systems": "전력계통", "Offshore Wind Biz": "해상풍력",
    # geoscience (지리)
    "Eos": "지구과학", "AGU Newsroom": "지구물리", "Geology Page": "지질",
    "Geospatial World": "측지", "Geography Realm": "지리학",
    "The Watchers": "자연재해", "Temblor": "지진",
    # environment (환경)
    "Waste Dive": "페기물", "Circular Online": "재자원화",
    "Envirotec Magazine": "환경기술", "Mongabay": "생태환경",
    "Carbon Brief": "기후", "Yale Environment 360": "환경보호",
    # computing (콤퓨터)
    "Ars Technica": "정보기술", "The Register": "콤퓨터소식",
    "TechCrunch": "정보산업", "Engadget": "전자제품", "Tom's Hardware": "콤퓨터부품",
    "Computerworld": "기업정보화", "InfoWorld": "쏘프트웨어", "Network World": "망기술",
    "BleepingComputer": "정보보안", "The Hacker News": "사이버보안",
    "CIO Dive": "정보관리", "Hackaday": "전자공작",
    # ai (정보기술)
    "The Decoder": "인공지능", "AI Business": "인공지능", "Synced": "인공지능",
    # electronics (전자)
    "IEEE Spectrum": "전자공학", "EE Times": "전자기술",
    "Semiconductor Engineering": "반도체", "Power Electronics News": "전력전자",
    "EDN": "전자설계", "Electronics Weekly": "전자소식",
    # robotics (로보트)
    "The Robot Report": "산업로보트", "Drone Life": "무인기",
    "Manufacturing Dive": "생산자동화",
    # medical (의학)
    "News-Medical": "의학소식", "GEN": "유전공학",
    # medical_tech (의료기술)
    "Medical Design and Outsourcing": "의료기기", "MedTech Dive": "의료산업",
    "Radiology Business": "방사선진단", "Physics World Medical": "의학물리",
    "Healthcare Dive": "보건의료", "MedPage Today": "임상의학",
    "Drug Discovery and Development": "신약개발", "Pharmaceutical Technology": "제약기술",
    # transport (수송)
    "Railway Gazette": "철도", "Marine Insight": "선박", "gCaptain": "항해",
    "Offshore Energy": "해양자원", "Truck News": "화물수송",
    "Supply Chain Dive": "물류", "The Maritime Executive": "해운경영",
    "Splash247": "해상운송", "Port Technology": "항만", "FreightWaves": "수송물류",
    # construction (건설)
    "Construction Dive": "건설산업", "Smart Cities Dive": "도시개발",
    "ENR": "건설공학", "Global Construction Review": "국제건설",
    "New Civil Engineer": "토목", "Architectural Record": "건축",
}


def folder_label(site: Site) -> str:
    """`<category>_<sub-category>(문서-영문)` for a site, in DPRK Korean."""
    category = FIELD_CATEGORY.get(site.field, field_label(site.field))
    subcategory = SITE_SUBCATEGORY.get(site.name, DEFAULT_SUBCATEGORY)
    return f"{category}_{subcategory}(문서-영문)"


# --------------------------------------------------------------- custom sites
# Sites the user adds through the GUI live here, not in this source file, so the
# curated registry above stays hand-maintained and code review stays clean.
CUSTOM_SITES_FILE = Path(__file__).with_name("custom_sites.json")


def _site_to_dict(site: Site) -> dict:
    return {
        "name": site.name, "homepage": site.homepage, "feed": site.feed,
        "content_selectors": list(site.content_selectors),
        "title_selectors": list(site.title_selectors),
        "hero_selectors": list(site.hero_selectors),
        "field": site.field, "low_volume": site.low_volume,
    }


def _site_from_dict(row: dict) -> Site:
    return Site(
        row["name"], row.get("homepage", ""), row.get("feed"),
        tuple(row["content_selectors"]),
        title_selectors=tuple(row.get("title_selectors")
                              or ("article h1", "main h1", "h1")),
        hero_selectors=tuple(row.get("hero_selectors", ())),
        field=row.get("field", "science"),
        low_volume=row.get("low_volume", False),
    )


def load_custom_sites() -> None:
    """Merge user-added sites from custom_sites.json into SITES (idempotent)."""
    if not CUSTOM_SITES_FILE.exists():
        return
    try:
        rows = json.loads(CUSTOM_SITES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    for row in rows:
        try:
            site = _site_from_dict(row)
        except (KeyError, TypeError):
            continue
        if site.field in FIELDS and site.name not in SITES:
            SITES[site.name] = site


def register_site(site: Site) -> None:
    """Add a verified site to the live registry and persist it for next launch."""
    SITES[site.name] = site
    rows: list[dict] = []
    if CUSTOM_SITES_FILE.exists():
        try:
            rows = json.loads(CUSTOM_SITES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            rows = []
    rows = [r for r in rows if r.get("name") != site.name]
    rows.append(_site_to_dict(site))
    tmp = CUSTOM_SITES_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CUSTOM_SITES_FILE)


load_custom_sites()
