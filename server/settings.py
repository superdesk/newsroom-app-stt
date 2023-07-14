import pathlib

from flask_babel import lazy_gettext
from newsroom.web.default_settings import ELASTICSEARCH_SETTINGS, BLUEPRINTS as DEFAULT_BLUEPRINT, \
    CORE_APPS as DEFAULT_CORE_APPS, CELERY_BEAT_SCHEDULE as CELERY_BEAT_SCHEDULE_DEFAULT

SERVER_PATH = pathlib.Path(__file__).resolve().parent
CLIENT_PATH = SERVER_PATH.parent.joinpath("client")
TRANSLATIONS_PATH = SERVER_PATH.joinpath("translations")

SITE_NAME = 'Mediapankki'
COPYRIGHT_HOLDER = 'STT'

USER_MANUAL = 'https://stt.fi/ajankohtaista-tietoa-media-asiakkaille/stt-mediapankki/'
PRIVACY_POLICY = PRIVACY_POLICY_EN = 'https://stt.fi/tietosuoja/'
TERMS_AND_CONDITIONS = TERMS_AND_CONDITIONS_EN = 'https://stt.fi/kayttoehdot/'
CONTACT_ADDRESS = 'https://stt.fi/yhteystiedot/'
CONTACT_ADDRESS_EN = 'https://stt.fi/en/contact/'

INSTALLED_APPS = [
    'stt.external_links',
    'stt.filters',
    'newsroom.auth.saml',
]

AGENDA_GROUPS = [
    {
        "field": "sttdepartment",
        "label": lazy_gettext("Department"),
        "nested": {
            "parent": "subject",
            "field": "scheme",
            "value": "sttdepartment",
            "include_planning": True,
        },
    },
    {
        "field": "sttsubj",
        "label": lazy_gettext("Subject"),
        "nested": {
            "parent": "subject",
            "field": "scheme",
            "value": "sttsubj",
            "include_planning": True,
        },
    },
    {
        "field": "event_type",
        "label": lazy_gettext("Event Type"),
        "nested": {
            "parent": "subject",
            "field": "scheme",
            "value": "event_type",
        },
    },
    {
        "field": "stturgency",
        "label": lazy_gettext("Importance"),
        "nested": {
            "parent": "subject",
            "field": "scheme",
            "value": "stturgency",
            "include_planning": True,
        },
    },
]

WIRE_GROUPS = [
    {
        "field": "sttdepartment",
        "label": lazy_gettext("Department"),
        "nested": {
            "parent": "subject",
            "field": "scheme",
            "value": "sttdepartment",
        },
    },
    {
        "field": "genre",
        "label": lazy_gettext("Genre"),
    },
    {
        "field": "sttversion",
        "label": lazy_gettext("Version"),
        "nested": {
            "parent": "subject",
            "field": "scheme",
            "value": "sttversion",
        },
    },
]

CORE_APPS = [
    app
    for app in DEFAULT_CORE_APPS
    if app not in [
        'newsroom.news_api',
        'newsroom.news_api.api_tokens',
        'newsroom.news_api.api_audit',
        'newsroom.monitoring',
        'newsroom.company_expiry_alerts',
    ]
]

BLUEPRINTS = [
    blueprint
    for blueprint in DEFAULT_BLUEPRINT
    if blueprint not in [
        'newsroom.monitoring',
        'newsroom.news_api.api_tokens',
    ]
]

LANGUAGES = ['fi', 'en']
DEFAULT_LANGUAGE = 'fi'

COMPANY_TYPES = [
    dict(
        id='premium',
        name='Premium',
        # no filter, gets all
    ),
    dict(
        id='non-premium',
        name='Non-premium',
        wire_must_not={'bool': {'filter': [  # filter out
            {'term': {'sttdone1': '5'}},  # premium
            {'range': {'embargoed': {'gte': 'now'}}},  # with embargo
        ]}},
    ),
    dict(
        id='non-media',
        name='Non-media',
        wire_must_not={'range': {'embargoed': {'gte': 'now'}}},  # filter out embargo
    ),
]

WATERMARK_IMAGE = None

CELERY_BEAT_SCHEDULE = {key: val for key, val in CELERY_BEAT_SCHEDULE_DEFAULT.items()
                        if key == 'newsroom.company_expiry'}

ENABLE_WATCH_LISTS = False

NEWS_API_ENABLED = False

# SDAN-695
ELASTICSEARCH_SETTINGS['settings']['query_string'] = {'analyze_wildcard': True}

PREPEND_EMBARGOED_TO_WIRE_SEARCH = True

SAML_CLIENTS = [
    "eduskunta",
]
