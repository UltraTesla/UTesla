def instance_by(values, types):
    for value, type_ in zip(values, types):
        assert isinstance(value, type_)
