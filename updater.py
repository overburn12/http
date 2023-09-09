import subprocess

commands = [
    'git pull',
    'sudo systemctl restart flask.service'
]

with open('update.log', 'a') as logfile:
    for command in commands:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        logfile.write(f'Command: {command}\n')
        logfile.write(f'Stdout: {stdout}\n')
        logfile.write(f'Stderr: {stderr}\n')
        logfile.write('\n')