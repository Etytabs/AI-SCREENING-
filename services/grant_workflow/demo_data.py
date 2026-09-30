"""Synthetic demonstration content.

Everything in this module is invented for demonstration. It is not an official NCST/NRIF
call, application, statistic or decision.
"""
from services.grant_workflow.models import DataOrigin
from services.grant_workflow.providers import HistoricalRecord

DEMO_CALL = {
    "name": "Climate Resilience Research Grant 2026 (synthetic demo)",
    "organization": "Demo National Research Fund (synthetic, NCST/NRIF-style)",
    "reference": "DEMO-CRG-2026",
    "description": "Synthetic grant call used to demonstrate the screening workflow. Not an official call.",
    "open_date": "2026-09-01",
    "close_date": "2026-11-15",
    "funding_min": 5_000_000,
    "funding_max": 50_000_000,
    "currency": "RWF",
    "domains": ["climate-smart agriculture", "water resource management", "early warning systems"],
}

DEMO_RFP_FILENAME = "DEMO-CRG-2026_call_document.txt"

DEMO_RFP_TEXT = """DEMO NATIONAL RESEARCH FUND
SYNTHETIC CALL FOR PROPOSALS
Climate Resilience Research Grant 2026
Reference: DEMO-CRG-2026
This document is synthetic demonstration content. It is not an official NCST or NRIF call.
1. Purpose
The call supports applied research that strengthens community resilience to climate change.
2. Thematic priorities
Proposals must address at least one of the following priorities: climate-smart agriculture, water resource management, or early warning systems for extreme weather.
3. Eligibility
The lead applicant must hold a PhD or equivalent doctoral qualification.
Applicants must be affiliated with a registered university or research institution.
The lead institution must be based in Rwanda.
Each project must include at least one partner organisation from local government or a community organisation.
\f4. Funding and duration
The maximum grant amount is RWF 50,000,000 per project.
The project duration must not exceed 24 months.
5. Required documents
Applicants must submit a full research proposal.
A detailed budget must be attached.
The CV of the principal investigator must be included.
A partner letter of commitment is required.
Proposals involving human participants must include an ethics approval or an ethics clearance plan.
6. Submission
Applications must be submitted through the fund portal no later than 15 November 2026.
7. Evaluation criteria
Proposals will be evaluated on scientific quality, relevance to the thematic priorities, feasibility and expected impact.
8. Declarations
Applicants must sign a declaration confirming that the proposal is original and disclosing any conflict of interest.
"""

_DECLARATION = """Declaration
I declare that this proposal is original work and I disclose no conflict of interest.
"""

_ETHICS = """Ethics clearance plan
The project will seek approval from the national research ethics committee before any data collection involving human participants.
Informed consent will be obtained from all participants.
"""

DEMO_APPLICATION_FILES: dict[str, str] = {
    # Eligible, complete, distinctive.
    "DEMO-APP-001/proposal.txt": """Title: Community flood early warning using low-cost river sensors
Applicant: Dr. Aline Mukamana
Email: a.mukamana@example.org
Institution: Kigali Institute of Climate Studies (synthetic)
Institution type: Registered research institution
Country: Rwanda
Domain: Early warning systems
Requested amount: RWF 42,000,000
Duration: 18 months
1. Summary
We propose a community-operated flood early warning system for the Sebeya catchment that uses low-cost ultrasonic river level sensors and SMS alerts. The project addresses early warning systems for extreme weather.
2. Research question
The research question is whether low-cost sensors maintained by trained community volunteers can deliver flood warnings at least two hours before peak water levels.
3. Methodology
Our approach installs twelve solar-powered ultrasonic sensors along the river, links them through a LoRaWAN gateway, and calibrates a hydrological forecast model with rainfall observations. We will use a stepped-wedge study design across six villages.
4. Dataset
Data collection will produce a two-year dataset of river levels, rainfall observations and alert logs.
5. Intervention and partners
The intervention trains forty community volunteers in sensor maintenance and alert dissemination across flood-prone villages. The Rubavu District disaster management office is a committed partner organisation.
6. Expected outcomes
Households in flood-prone villages will receive timely warnings, and district emergency teams will gain a validated early warning model for the rainy seasons.
7. Workplan
The project duration is 18 months.
""",
    "DEMO-APP-001/budget.txt": """Budget
Total requested: RWF 42,000,000
Personnel: RWF 16,000,000
Sensors and gateway equipment: RWF 14,000,000
Community training: RWF 7,000,000
Data management and dissemination: RWF 5,000,000
""",
    "DEMO-APP-001/cv.txt": """Curriculum Vitae
Dr. Aline Mukamana
PhD in Hydrology, 2016
Senior researcher in flood risk and hydrological modelling.
""",
    "DEMO-APP-001/partner_letter.txt": """Letter of commitment
The Rubavu District disaster management office, a local government partner organisation, commits to support sensor installation, volunteer coordination and the dissemination of flood alerts.
""",
    "DEMO-APP-001/ethics.txt": _ETHICS,
    "DEMO-APP-001/declaration.txt": _DECLARATION,
    # Strong similarity to a synthetic funded project.
    "DEMO-APP-002/proposal.txt": """Title: Climate-smart maize disease detection for smallholder farmers
Applicant: Dr. Eric Habimana
Email: e.habimana@example.org
Institution: University of the Northern Highlands (synthetic)
Country: Rwanda
Domain: Climate-smart agriculture
Requested amount: RWF 48,000,000
Duration: 24 months
1. Summary
This project will develop a mobile tool that detects maize leaf diseases using machine learning models trained on annotated maize leaf images collected from smallholder farms. The work addresses the climate-smart agriculture priority.
2. Research question
The research question is whether convolutional neural network classifiers can identify maize streak virus and northern leaf blight from smartphone photographs taken by farmers.
3. Methodology
The methodology combines field image collection with extension workers, expert annotation of leaf images, and training of a convolutional neural network classifier.
4. Dataset
The dataset will contain 15,000 annotated maize leaf images from five districts.
5. Application and intervention
The tool will be deployed to extension workers who advise farmers on early treatment. The pilot intervention will train 300 farmers to photograph affected leaves.
6. Workplan
The project duration is 24 months.
""",
    "DEMO-APP-002/budget.txt": """Budget
Total requested: RWF 48,000,000
Personnel: RWF 20,000,000
Field image collection: RWF 12,000,000
Model development and compute: RWF 9,000,000
Farmer training: RWF 7,000,000
""",
    "DEMO-APP-002/cv.txt": """Curriculum Vitae
Dr. Eric Habimana
PhD in Plant Pathology, 2014
Lecturer in crop protection and digital agriculture.
""",
    "DEMO-APP-002/partner_letter.txt": """Letter of commitment
The Musanze maize farmers cooperative, a community organisation, confirms that it is a committed partner organisation and will host field image collection.
""",
    "DEMO-APP-002/ethics.txt": _ETHICS,
    "DEMO-APP-002/declaration.txt": _DECLARATION,
    # Outside geography, over budget and duration, missing partner letter.
    "DEMO-APP-003/proposal.txt": """Title: Solar irrigation scheduling for drought-prone hillside farms
Applicant: James Otieno
Email: j.otieno@example.org
Institution: Lake Basin Agricultural University (synthetic)
Country: Kenya
Domain: Water resource management
Requested amount: RWF 65,000,000
Duration: 30 months
1. Summary
The project designs solar-powered drip irrigation schedules for hillside farms facing recurrent drought and contributes to water resource management.
2. Objectives
We aim to test whether soil moisture sensors combined with weather forecasts reduce irrigation water use while maintaining bean yields.
3. Methodology
The approach compares sensor-guided scheduling with farmer-managed irrigation on forty demonstration plots, supported by farmer interviews and yield measurements.
4. Workplan
The project duration is 30 months.
""",
    "DEMO-APP-003/budget.txt": """Budget
Total requested: RWF 65,000,000
Solar pumps and drip kits: RWF 30,000,000
Sensors: RWF 15,000,000
Personnel: RWF 20,000,000
""",
    "DEMO-APP-003/cv.txt": """Curriculum Vitae
James Otieno
MSc in Agricultural Engineering, 2019
Irrigation engineer with five years of field experience.
""",
    "DEMO-APP-003/declaration.txt": _DECLARATION,
    # Reuses passages from DEMO-APP-001; CV missing.
    "DEMO-APP-004/proposal.txt": """Title: Drought early warning dashboard for district planners
Applicant: Grace Uwimana
Email: g.uwimana@example.org
Institution: Eastern Province Planning Research Institute (synthetic)
Country: Rwanda
Domain: Early warning systems
Requested amount: RWF 38,000,000
Duration: 20 months
1. Summary
This project builds a drought early warning dashboard that combines satellite vegetation indices with market price data for district planners, contributing to early warning systems for extreme weather.
2. Research question
We investigate whether combined vegetation and price indicators provide earlier drought signals than rainfall alone.
3. Intervention and partners
The intervention trains forty community volunteers in sensor maintenance and alert dissemination across flood-prone villages.
4. Expected outcomes
Households in flood-prone villages will receive timely warnings, and district emergency teams will gain a validated early warning model for the rainy seasons.
5. Workplan
The project duration is 20 months.
""",
    "DEMO-APP-004/budget.txt": """Budget
Total requested: RWF 38,000,000
Satellite data and dashboard development: RWF 20,000,000
Personnel: RWF 18,000,000
""",
    "DEMO-APP-004/partner_letter.txt": """Letter of commitment
The Kayonza District planning office, a local government partner organisation, will co-design the dashboard and host training sessions.
""",
    "DEMO-APP-004/declaration.txt": _DECLARATION,
    # Thin submission: no amount, no duration, declaration missing.
    "DEMO-APP-005/proposal.txt": """Title: Household rainwater harvesting adoption study
Applicant: Dr. Claudine Ingabire
Email: c.ingabire@example.org
Institution: University of Bugesera (synthetic)
Country: Rwanda
Domain: Water resource management
1. Summary
This study will survey 400 households in Bugesera about rainwater harvesting adoption.
""",
    "DEMO-APP-005/budget.txt": """Budget
Budget items: water tanks, enumerators and travel.
Amounts will be confirmed after the inception phase.
""",
    "DEMO-APP-005/cv.txt": """Curriculum Vitae
Dr. Claudine Ingabire
PhD in Environmental Economics, 2018
""",
    "DEMO-APP-005/partner_letter.txt": """Letter of commitment
The Bugesera women's water committee, a community organisation, is a committed partner organisation for household outreach.
""",
}

HISTORICAL_RECORDS = [
    HistoricalRecord(
        record_id="HIST-2024-118",
        title="AI-based crop disease detection using machine learning for maize farmers",
        text=(
            "This project developed a mobile tool that detects maize leaf diseases using machine "
            "learning models trained on annotated maize leaf images collected from smallholder farms. "
            "The research question was whether convolutional neural network classifiers can identify "
            "maize streak virus and northern leaf blight from smartphone photographs taken by farmers. "
            "The methodology combined field image collection with extension workers, expert annotation "
            "of leaf images, and training of a convolutional neural network classifier. The dataset "
            "contained 12,000 annotated maize leaf images from four districts. The tool was deployed to "
            "extension workers who advised farmers on early treatment. The pilot intervention trained "
            "200 farmers to photograph affected leaves."
        ),
        source_type="funded_project",
        year=2024,
        outcome="Funded / completed",
        organization="Demo National Research Fund (synthetic)",
        data_origin=DataOrigin.SYNTHETIC,
    ),
    HistoricalRecord(
        record_id="HIST-2025-031",
        title="Climate-smart irrigation analytics for smallholder agriculture",
        text=(
            "The project analysed irrigation practices of smallholder farmers and built a scheduling "
            "advisory using rainfall forecasts. The methodology combined household surveys with plot-level "
            "water measurements in two districts. The dataset included weekly irrigation records from 150 "
            "farms. The intervention delivered SMS irrigation advice to participating farmers."
        ),
        source_type="historical_application",
        year=2025,
        outcome="Funded",
        organization="Demo National Research Fund (synthetic)",
        data_origin=DataOrigin.SYNTHETIC,
    ),
    HistoricalRecord(
        record_id="HIST-2024-074",
        title="Digital health early warning and referral system",
        text=(
            "The project designed a digital early warning and referral system for community health "
            "workers. The approach used a mobile application to report danger signs and a rules-based "
            "model to prioritise referrals. The dataset consisted of anonymised referral records from "
            "health centres."
        ),
        source_type="historical_application",
        year=2024,
        outcome="Not selected",
        organization="Demo National Research Fund (synthetic)",
        data_origin=DataOrigin.SYNTHETIC,
    ),
    HistoricalRecord(
        record_id="HIST-2023-052",
        title="River level monitoring for flood preparedness",
        text=(
            "The project installed manual river gauges and trained district staff to report water levels "
            "by phone. The methodology relied on daily manual readings and seasonal flood risk maps. The "
            "dataset contained three years of manual gauge readings."
        ),
        source_type="funded_project",
        year=2023,
        outcome="Funded / completed",
        organization="Demo National Research Fund (synthetic)",
        data_origin=DataOrigin.SYNTHETIC,
    ),
]
