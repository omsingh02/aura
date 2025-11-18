def log(message, level='INFO'):
    if level != 'ERROR':
        return
    print(f'\\033[91m{message}\\033[0m')
