import  yaml
import importlib

plugins = None
with open('plugins.yaml', 'r') as file:
    plugins = yaml.safe_load(file)

for uid in plugins:

    parts = plugins[uid]['class'].rsplit('.', 1)
    if len(parts) == 1:
        module_str = ""
        cls = parts[0]
    elif len(parts) == 2:
        module_str = parts[0]
        cls = parts[1]
    else:
        print(f">> Error: {cls}")
        continue

    prefix = plugins[uid]['prefix']
    print(f"On s'occupe de {uid}")
    print(f"|  classe = {cls}")
    print(f"|  prefix = {prefix}")

    module = importlib.import_module("plugins.welcome")
    if not hasattr(module, cls):
        print(f">> No such class: {cls}")
        continue

    ClassReference = getattr(module, cls)
    instance = ClassReference(uid, prefix=prefix)
    print(instance)

