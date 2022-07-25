import pathlib

from newsroom.web.default_settings import ELASTICSEARCH_SETTINGS, BLUEPRINTS as DEFAULT_BLUEPRINT, \
    CORE_APPS as DEFAULT_CORE_APPS, CELERY_BEAT_SCHEDULE as CELERY_BEAT_SCHEDULE_DEFAULT

SERVER_PATH = pathlib.Path(__file__).resolve().parent
CLIENT_PATH = SERVER_PATH.parent.joinpath("client")

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
]

CORE_APPS = [
    app
    for app in DEFAULT_CORE_APPS
    if app not in [
        'newsroom.media_utils',
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
        wire_must_not={'bool': {'must': [  # filter out
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
