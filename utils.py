import json


class SetEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def dump_json(data, filename, confirm=True, indent=None):
    with open(filename, "w") as f:
        json.dump(data, f, cls=SetEncoder, indent=indent, ensure_ascii=False)
        if confirm:
            print(f'✅ Saved "{filename}"')
