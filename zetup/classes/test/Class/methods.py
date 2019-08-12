import zetup

member, metamember = zetup.class_member_module(__name__, ['method'])


@member
def method(self):
    pass
