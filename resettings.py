from utils import class_public_dict


class SettingsBag(object):
    @classmethod
    def as_dict(cls):
        context = class_public_dict(cls)

        return context