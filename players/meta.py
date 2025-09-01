class StaticMethodMaker(type):
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for i in attrs:
            if not i.startswith('__'):
                new_attrs[i] = staticmethod(attrs.get(i))
        return super().__new__(cls, name, bases, new_attrs)
