import zetup

__all__ = ('class_member_module', )


class class_member_module(zetup.module):

    __package__ = zetup

    @property
    def owner(self):
        return self.__dict__.get('owner')

    @owner.setter
    def owner(self, classobj):
        self.__dict__['owner'] = classobj
        for obj in self.members:
            classobj.member(obj)
        for obj in self.metamembers:
            classobj.metamember(obj)

    def __init__(self, name, api):
        super(class_member_module, self).__init__(
            name, api,
            __iter__=lambda: iter((self.member, self.metamember)))

        self.__dict__['members'] = []
        self.__dict__['metamembers'] = []

    def member(self, obj):
        # assert self.type is not None, (
        #     "{!r} was not correctly registered as member_module of a {!r}"
        #     .format(self, zetup.class_package))
        # return self.type.member(obj)
        self.members.append(obj)

    def metamember(self, obj):
        # assert self.type is not None, (
        #     "{!r} was not correctly registered as member_module of a {!r}"
        #     .format(self, zetup.class_package))
        # return self.type.metamember(obj)
        self.metamembers.append(obj)
