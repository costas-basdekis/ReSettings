from resettings import SettingsBag as SB, setting_reference_factory as SR

class Default(SB):
    DEBUG = True
    TEMPLATE_DEBUG = SR.DEBUG
    PROTOCOL = 'https'
    FULL_PROTOCOL = SR.PROTOCOL + '://'
    DOMAIN = 'example.com'
    HOST = 'dev.' + SR.DOMAIN
    ENDPOINT = SR.FULL_PROTOCOL + SR.HOST


class Dev(Default):
    DEBUG = True
    PROTOCOL = 'http'


class Live(Default):
    DEBUG = False
    HOST = 'live.' + SR.DOMAIN


if __name__ == '__main__':
    DEV_CONFIG = Dev.as_dict()
    LIVE_CONFIG = Live.as_dict()

    print 'dev', DEV_CONFIG
    print 'live', LIVE_CONFIG
