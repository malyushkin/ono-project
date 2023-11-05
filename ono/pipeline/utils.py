def source_slug_mapper_maker(d):
    _d = {}
    for key in d.keys():
        for value in d[key]:
            _d[value] = key
    return _d
