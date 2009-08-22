import os

invokables = {}
def invokable(func):
    invokables[func.__name__] = func
    return func

@invokable
def prompt(argv):
    interact()

def interact(locals=None):
    try:
        from IPython.Shell import IPShellEmbed
        interact_func = lambda locals: IPShellEmbed(argv=())(local_ns=locals)
    except ImportError:
        interact_func = lambda locals: code.interact(local=locals)
    interact_func(locals)

@invokable
def telnet(argv):
    os.system('telnet localhost 2323')
    os.system('reset -w 2>/dev/null')
