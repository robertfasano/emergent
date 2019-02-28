from prompt_toolkit import prompt

def get_hub(hub, network):
    text = prompt('network.hubs["%s"].'%hub)
    exec = 'network.hubs["%s"].'%hub + text
    print(eval(exec))
