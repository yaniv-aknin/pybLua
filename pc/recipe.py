import cStringIO as StringIO
import os

class RecipeError(Exception):
    pass

def loadRecipeLines(path, stuffGarbageCollection=True):
    result = []
    directory = os.path.dirname(path)
    lines = file(path).readlines()
    for line in lines:
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith('+'):
            filename = line[1:].strip()
            new_path = os.path.join(directory, filename)
            result.extend(line.rstrip() for line in file(new_path).readlines())
            if stuffGarbageCollection:
                result.append("collectgarbage()")
        else:
            raise RecipeError('unknown operand %s' % (line[0],))
    return result
