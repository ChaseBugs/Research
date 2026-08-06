# 연구자료 수집·생성 도구

Windows용 4개 Tab 프로그람입니다. 맨 위 **작업 폴더**를 모든 Tab이 공유하며, 그 폴더의
SQLite 데이터베이스 `research_ledger.db`에 내려받은 모든 자료가 기록됩니다. 이 기록으로 날짜·폴더와 상관없이 매번 겹치지 않게 하고, 리력 Tab이 통계를 냅니다.

| Tab | 하는 일 | 저장 위치 |
| --- | --- | --- |
| **Scrapping** | 공개 뉴스 기사를 DOCX로 수집 (24개 분야, 144개 사이트) | `Scraped_News/` |
| **Generate** | 키워드 → 기술 100가지 → 기술별 설명문서(그림 포함) 생성 | `Generated_Docs/<키워드>_<날짜>/` |
| **원문도서** | 키워드에 해당한 특허·논문 PDF 내리적재 | `Source_Books/<키워드>_<날짜>/` |
| **리력** | 내려받은 모든 자료의 일별·주별·월별 건수와 목록 | — |

## 실행

```powershell
python -m pip install -r requirements.txt
python -B news_scraper_gui.py
```

또는 `Run_NewsScraper.bat`를 두 번 눌러 실행할 수 있습니다.

## Scrapping Tab

**분야**를 고르고 **사이트**를 고른 다음, `YYYY-MM-DD` 형식으로 시작/끝 날짜를 입력하고 **수집 시작**을 누릅니다.
사이트 목록의 첫 항목인 `★ 이 분야 전체`를 고르면 그 분야의 모든 사이트를 한 번에 수집합니다.

### 기술 기사만 분리

`기술 기사만 분리` 를 켜면, 수집한 각 기사를 AI(Groq/g4f)가 **기술 기사** 인지 **소식 기사**(발표·계약·자금·인사·시장
소식 등 기술적 내용이 없는 것)인지 판정합니다. 소식으로 판정된 기사는 버리지 않고 `보도기사/` 하위 폴더로
따로 모읍니다. 기사 하나마다 판정 호출이 한 번 들어가므로 기본값은 꺼짐입니다. Groq 엔진을 쓰려면 Generate 탭에서
설정한 API 키가 필요합니다. 완료창에 `기술 N, 소식 M` 으로 개수를 보여줍니다.

### 새 사이트 추가

사이트 목록 옆의 **＋ 새 사이트 추가** 단추를 누르면 창이 열립니다. 분야를 고르고 **사이트 이름**과 **RSS 피드
주소**만 넣은 뒤 **검증 후 추가**를 누르면:

- 프로그람이 피드 접속·기사 날짜·**전체 본문**·이미지를 실제로 확인하고, 본문 선택자를 자동으로 찾습니다.
- 수집이 가능하면 목록에 바로 추가되고, 불가능하면 그 이유를 대화창으로 알려줍니다(맛보기만 제공, 봇 차단, 피드
  오류 등).

추가한 사이트는 `custom_sites.json`에 저장되어 다음에 프로그람을 켤 때도 그대로 남습니다. 본문 선택자는 직접
입력할 필요가 없습니다.

## Generate Tab

키워드(대개 기술 이름)를 입력하고 **주제 생성**을 누르면, 그 키워드에 관련된 구체적인 기술 이름을 최대 100개
나렬합니다. 실례로 `탄광마을현대화`를 넣으면 그와 관련한 기술 100가지가 목록에 나타납니다.

그다음 **문서 생성**을 누르면, 목록의 각 기술을 제목으로 하여 초보자용 상세 설명서를 만듭니다. 각 문서에는
개요·원리·사용법·응용분야·구현단계·주의사항이 들어가고, AI가 그린 그림이 포함됩니다. `생성할 문서 수`로 한 번에
만들 문서 개수를 정합니다(문서 하나에 텍스트+그림 생성으로 수십 초 걸립니다).

- **엔진**은 두 가지 중에 고릅니다:
  - **g4f** — API 키가 필요 없습니다. 편하지만 가끔 느리거나 실패할 수 있습니다.
  - **Groq** — 무료이지만 API 키가 필요합니다(console.groq.com 에서 발급). 빠르고 안정적입니다. 키는 한 번
    입력하면 저장되어 다음에도 유지됩니다(`ai_config.json`).
- 그림 생성은 두 엔진 모두 Pollinations(무료, 키 불필요)를 씁니다.
- 문서는 영어로 작성됩니다.

## 원문도서 Tab

키워드를 넣고 **특허**·**arXiv** 중 출처를 고른 뒤 **검색**을 누르면 결과가 나렬됩니다. 목록에서 골라
**선택 PDF 내리적재**를 하거나, 아무것도 안 고르고 **전체 내리적재**로 모두 받을 수 있습니다.

- **합법적인 공개 출처만** 씁니다: Google Patents(특허는 공개문서), arXiv(오픈액세스 논문).
- LibGen·Z-Library·Anna's Archive·Sci-Hub 같은 불법복제 사이트는 **연결하지 않습니다**(저작권).
- 제목에 한글이 있거나 한국(korea/korean) 발행인 자료, `KR` 특허번호는 자동으로 제외합니다.

## 리력 Tab

작업 폴더에 기록된 모든 자료(수집기사·생성문서·원문도서)를 보여줍니다. 시작/끝 날짜를 정하고
일별·주별·월별 단위를 고르면 기간별 건수표와 개별 목록이 나타납니다. 목록 항목을 두 번 누르면 그 파일의
폴더가 열립니다. 같은 자료는 기록에 있으면 다시 내려받거나 생성하지 않습니다.

## 분야와 사이트

전체 목록은 `python -B news_scraper.py --list` 로도 볼 수 있습니다.

| 분야 | 사이트 수 | 사이트 |
| --- | --- | --- |
| 과학/기술 일반 | 10 | SciTechDaily, ScienceDaily, Science News Explores, ScienceAlert, Live Science, Sci.News, Nature News, New Atlas, Innovation News Network, Knowable Magazine |
| 군사/국방 | 8 | Defense News, Defense One, DefenseScoop, Naval News, The War Zone, Breaking Defense, Defence Blog, Overt Defense |
| 우주/항공 | 6 | Space.com, SpaceNews, NASA, Universe Today, Spaceflight Now, SpaceDaily |
| 물리/양자 | 2 | Physics World, The Quantum Insider |
| 화학/화학공업 | 2 | Chemical Engineering, Advanced Science News |
| 재료/나노 | 4 | 3D Printing Industry, Composites World, Graphene Info, Plastics Today |
| 농업 | 5 | AgFunderNews, Farm Progress, Farm Equipment, Seed World, Modern Farmer* |
| 축산/수산 | 5 | Feedstuffs, Beef Magazine, National Hog Farmer, Aquaculture Magazine, Undercurrent News |
| 식료공업 | 3 | Food Dive, Food Engineering, Food Safety News |
| 경공업 | 5 | Textile World, Innovation in Textiles, Apparel Resources, Just Style, Packaging Digest |
| 중공업/기계 | 6 | Assembly Magazine, Modern Machine Shop, Production Machining, Plant Engineering, Marine Log, Seatrade Maritime |
| 금속/광업 | 8 | International Mining, Mining Technology, Northern Miner, Canadian Mining Journal, Australian Mining, Coal Age, Light Metal Age, Powder Metallurgy Review |
| 전력/에네르기 | 13 | Utility Dive, POWER Magazine, pv magazine, Renewable Energy World, Electrek, Energy Storage News, Solar Power World, Windpower Engineering*, World Nuclear News, Nuclear Engineering International*, Power Engineering, Modern Power Systems, Offshore Wind Biz |
| 지리/지질/수문 | 7 | Eos, AGU Newsroom, Geology Page, Geospatial World, Geography Realm, The Watchers, Temblor* |
| 환경/페기물 | 6 | Waste Dive, Circular Online, Envirotec Magazine, Mongabay, Carbon Brief, Yale Environment 360 |
| 콤퓨터/인터네트/AI | 12 | Ars Technica, The Register, TechCrunch, Engadget, Tom's Hardware, Computerworld, InfoWorld, Network World, BleepingComputer, The Hacker News, CIO Dive, Hackaday |
| 전자/반도체 | 6 | IEEE Spectrum, EE Times, Semiconductor Engineering, Power Electronics News, EDN, Electronics Weekly |
| 로보트/자동화 | 3 | The Robot Report, Drone Life, Manufacturing Dive |
| 의학/생명공학 | 2 | News-Medical, GEN |
| 의료기술/영상 | 8 | Medical Design and Outsourcing, MedTech Dive, Radiology Business, Physics World Medical, Healthcare Dive, MedPage Today, Drug Discovery and Development, Pharmaceutical Technology |
| 운수/해운/철도 | 10 | Railway Gazette, Marine Insight, gCaptain, Offshore Energy, Truck News, Supply Chain Dive, The Maritime Executive, Splash247, Port Technology, FreightWaves |
| 건설/도시 | 5 | Construction Dive, Smart Cities Dive, ENR, Global Construction Review, New Civil Engineer |

`*` 표시는 갱신이 드문 사이트입니다. 기사가 적게 나와도 고장이 아닙니다.

SciTechDaily는 페이지네이션을 따라 지정 날짜까지 탐색합니다. 나머지 사이트는 공식 RSS가 제공하는 최근 기사 범위에서
수집하며, 입력 시작일이 RSS 보존 범위보다 오래되면 진행창에 경고를 표시합니다.

## 제외 키워드

`exclude_keywords.txt`에 적은 낱말이 기사 **제목이나 본문**에 들어 있으면 그 기사는 저장하지 않습니다.
한 줄에 하나씩 적고, `#`로 시작하는 줄은 주석입니다. 대소문자는 구별하지 않습니다.

- 영문 낱말은 낱말 단위로 맞춰봅니다. `ai`는 `said`나 `airplane` 안에서는 걸리지 않습니다.
- 조선말 낱말은 글자 그대로 포함되면 걸립니다.

검사는 그림을 내려받기 **전에** 진행하므로 제외된 기사는 통신량을 쓰지 않습니다.

## 중복 건너뛰기 (전역·날짜 무관)

내려받은 모든 자료(수집기사·생성문서·원문도서)는 작업 폴더의 **SQLite** 데이터베이스 `research_ledger.db`
한 곳에 기록됩니다. 중복 판정은 **저장 폴더나 날짜와 상관없이 전역으로** 적용됩니다 — 어제 다른 폴더에 받은
기사도 오늘 다시 나오면 건너뜁니다.

- **주소**가 같으면 내려받기 전에 건너뜁니다.
- **제목**이 같으면 건너뜁니다. 비교할 때 대소문자, 문장부호, 띄여쓰기를 무시하므로 같은 기사가 다른 주소로
  다시 올라와도 걸러집니다.
- 종류(기사/문서/도서)별로 따로 관리하므로 서로 섞이지 않습니다.

GUI의 `이미 수집한 기사 건너뛰기`를 끄거나 명령줄에서 `--no-history`를 주면 이 기능을 쓰지 않습니다(다시 받음).
예전 버전의 `_history.json`·`activity_log.jsonl`은 처음 실행할 때 SQLite로 **자동 이전**됩니다.
이력을 지우려면 `research_ledger.db`를 삭제하십시오.

## 사이트당 최대 기사 수

한 사이트가 수집 전체를 차지하지 않도록 사이트당 기사 수를 제한합니다. 기본값은 50이고 `0`은 무제한입니다.
최신 기사부터 채웁니다.

## 저장 위치

수집한 날짜별로, `분야_세부분야(문서-영문)` 형식의 조선말 폴더에 영문 문서를 저장합니다. **분야**는 category,
**세부분야**는 출처(사이트)별로 정해진 조선말 소분류입니다. 수집 기간이나 출처 이름은 폴더명에 넣지 않습니다.

```
Scraped_News/08-01/
    군사_함선(문서-영문)/           (Naval News)
        <기사 제목>.docx
        보도기사/                  (기술성이 낮은 기사, 판정 켠 경우만)
            <기사 제목>.docx
    군사_국방(문서-영문)/           (Defense News)
        <기사 제목>.docx
```

분야 전체를 수집하면 그 분야의 각 사이트가 **자기 세부분야 폴더**로 나뉘어 저장됩니다. 예를 들어 물리 분야를
수집하면 `물리_물리학(문서-영문)`(Physics World)과 `물리_양자기술(문서-영문)`(The Quantum Insider)이 만들어집니다.

세부분야 대응표는 `sites.py`의 `FIELD_CATEGORY`(분야→category)와 `SITE_SUBCATEGORY`(사이트→세부분야)에
있습니다. 목록에 없는 사이트(직접 추가한 것 등)는 세부분야가 `새기술`로 붙습니다.

한 기사가 실패해도 그 사이트의 나머지 기사는 계속 수집하며, 한 사이트가 통째로 실패해도 분야의 나머지 사이트는
계속 수집합니다. 문제가 있을 때만 `failures.txt`(실패한 주소)·`_skipped.txt`(제외/중복 건너뜀)가 폴더에
생깁니다.

## 명령줄

```powershell
# 등록된 분야와 사이트 보기
python -B news_scraper.py --list

# 사이트 하나
python -B news_scraper.py --site "ScienceDaily" --start 2026-07-20 --end 2026-07-22 --output D:\Research\Scraped_News

# 분야 전체
python -B news_scraper.py --field military --start 2026-07-20 --end 2026-07-22 --limit 30 --output D:\Research\Scraped_News

# 중복 건너뛰기 없이, 제외 키워드 파일을 따로 지정
python -B news_scraper.py --field space --start 2026-07-20 --end 2026-07-22 --no-history --keywords D:\Research\my_keywords.txt
```

## 사이트 상태 확인

RSS 주소와 페이지 구조는 시간이 지나면 바뀝니다. 수집이 갑자기 안 되면 먼저 이것을 돌리십시오.

```powershell
python -B verify_sites.py                      # 전체
python -B verify_sites.py --field energy       # 한 분야
python -B verify_sites.py --site "NASA"        # 한 사이트
```

각 사이트의 기사 수, 최신 날짜, 본문 길이, 그림 수를 표로 보여줍니다. 실패한 사이트는 `sites.py`의 `feed`
주소나 `content_selectors`를 고치고, 되살릴 수 없으면 항목을 지운 뒤 아래 제외 목록에 적으십시오.

## 사이트 추가 기준

새 사이트는 다음 네 가지를 **실제로 확인한 뒤에만** `sites.py`에 추가합니다.

1. RSS(또는 목록 페이지)에 접속되는가
2. 기사마다 날짜를 읽을 수 있는가
3. 선택자로 **전체 공개 본문**이 잡히는가 (맛보기만 나오면 안 됩니다)
4. 그림을 내려받을 수 있는가

## 검토했지만 제외한 주소

아래 주소는 실제로 시험해 보고 제외한 것입니다. 다시 시험하느라 시간을 쓰지 마십시오.
(마지막 확인: 2026-07-25)

**로그인/구독/봇 차단 (403)**
Scientific American, Military Times, Shephard Media, RealAgriculture, Phys.org(기사 403),
Medical Xpress(기사 403), Big Think(기사 403), ChemistryViews, VentureBeat, All About Circuits(기사 403),
APS Physics, AgWeb, MarkTechPost, Mining.com, Unite.AI, Dairy Herd, Photonics,
Smart Energy International(503), Control Engineering, Equipment World, Manufacturing.net, The Manufacturer,
Metal AM, Recycling International, Ceramic Tech News, Happi, Perfumer Flavorist, PrintWeek, Nonwovens Industry,
Labels and Labeling(기사 403), Tech Xplore(기사 403), Cosmos Magazine, Inside Climate News, Pollution Solutions,
AuntMinnie, MassDevice, Healthcare IT News, GPS World

**공식 피드가 없어지거나 옮겨감 (404 / 410)**
AZoM, AZoNano, Army Recognition, Automation World, Automation.com, Chemistry World, EurekAlert, IoT For All,
Militaryaerospace, Successful Farming, T&D World, Design News, Machine Design, FlightGlobal, Hydrogen Insight,
Nanowerk, Optics.org, World Construction Today, ConstructConnect, CAAIN, MaterialsViews, MRS Bulletin, MIT News,
ChemXplore, ChemAnalyst, IndustryWeek, American Machinist, Control Global, Hydraulics Pneumatics, The Fabricator,
KHL International Construction, Mining Weekly, Mining Magazine, Steel Times International, SteelOrbis, Foundry Management,
Kitco Mining, Metal Tech News, Cosmetics Design(410), Packaging Europe, WhatTheyThink, Nonwovens Industry,
Food Processing, Food Navigator, Food Manufacture, Bakery and Snacks, Dairy Reporter, Confectionery News, New Food Magazine,
All About Feed, Dairy Global, Pig Progress, Poultry World, SeafoodSource, The Fish Site, Fish Farming Expert,
Directions Magazine, Earth.com, GIM International, Hydro International, Smart Water Magazine, USGS News, WaterWorld,
Water Technology, Water and Wastes Digest, British Plastics, Chemical Processing, Process Engineering, Electronic Design,
Electropages, BioSpace, European Pharmaceutical Review, Health Imaging, Waste Management World, Resource Magazine,
Environment Energy Leader, Recharge News, Nuclear Newswire, Global Railway Review, International Railway Journal(403),
Railway Age(403), Bridge Design Engineering, Building Design Construction

**주소 확인 실패 또는 접속 불안정**
Green Car Congress(DNS), Materials Today(SSL), AgriTechTomorrow(DNS), Chemical Engineering World(SSL),
Advanced Materials News(DNS), Medgadget(SSL), Electronic Products·Planet Analog(edn.com 접속 불안정)

**피드에 날짜가 없거나 비여 있음**
Agriland, Analytics India Magazine, IoT World Today, World Grain, Fibre2Fashion, World Footwear, Furniture Today,
Riviera Maritime, Welding Productivity, Aluminium Insider, ICIS, Baking Business, Food Business News, Progressive Railroading,
NOAA Research, Construction Briefing, World Highways, Fierce Biotech

**본문을 뽑아낼 수 없음**
ZDNET, Recycling Today, Interesting Engineering, ESA, Embedded, Future Farming, Aviation Week,
Slashdot(요약만 제공), Quanta Magazine(선택자가 불안정), Science News(구독벽으로 맛보기만 나옴),
3DPrint.com, Ecotextile News, Knitting Industry, Canadian Mining Journal(초기엔 실패했으나 이후 선택자 발견해 추가),
Marine Log(초기엔 실패했으나 이후 선택자 발견해 추가), Imaging Technology News, Anthropocene Magazine(초기 실패 후 추가),
Seatrade Maritime(초기 실패 후 추가), Chemeurope, Knowable Magazine(초기 실패 후 추가), Beef·Feedstuffs·National Hog Farmer(Informa 플랫폼 선택자 발견해 추가),
Packaging Digest·Plastics Today(Informa 플랫폼), Printing Impressions(뉴스데스크 맛보기만), Labiotech(최신 기사 구독벽으로 본문 불안정),
Seatrade Maritime(일부 기사 맛보기)

**독립적인 공개 뉴스 아카이브가 아님**
LinkedIn AI-Weekly, Kernel

**참고**
- ENR 은 `/articles/` 는 전체 본문이 나오지만 `/blogs/` 글은 구독벽입니다. 블로그 글은 저장하지 않고 건너뜁니다.
- Informa/Endeavor 계열(Feedstuffs, Beef, National Hog Farmer, Packaging Digest, Plastics Today, Farm Progress)은
  본문 선택자가 `.ArticleBase-Body` 또는 `.ArticleBase-BodyContent` 입니다.

**다시 시험해서 추가한 것**
Breaking Defense — 이전에는 봇 차단으로 제외했으나 2026-07-25 확인 결과 정상이여서 추가했습니다.
