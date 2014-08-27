from resettings import SettingsBag as SB


class Default(SB):
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG


class Dev(Default):
    DEBUG = True


class Live(Default):
    DEBUG = False


if __name__ == '__main__':
    DEV_CONFIG = Dev.as_dict()
    LIVE_CONFIG = Live.as_dict()

    print 'dev', DEV_CONFIG
    print 'live', LIVE_CONFIG
