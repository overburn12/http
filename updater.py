import subprocess

commands = [
    'git pull',
    'sudo systemctl restart flask.service'
]

with open('update.log', 'a') as logfile:
    for command in commands:
        logfile.write(f'Command: {command}\n')
        result = subprocess.run(
            command,
            shell=True,
            stdout=logfile,
            stderr=logfile,
            text=True
        )
        logfile.write(f'Return Code: {result.returncode}\n\n')