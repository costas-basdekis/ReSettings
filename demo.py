from resettings import SettingsBag as SB, setting_reference_factory as SR

class Default(SB):
    DEBUG = True
    TEMPLATE_DEBUG = SR.DEBUG


class Dev(Default):
    DEBUG = True


class Live(Default):
    DEBUG = False


if __name__ == '__main__':
    DEV_CONFIG = Dev.as_dict()
    LIVE_CONFIG = Live.as_dict()

    print 'dev', DEV_CONFIG
    print 'live', LIVE_CONFIG
