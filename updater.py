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
            capture_output=True,  # Capture the command output
            text=True
        )
        # Write the command output to the log file
        logfile.write(result.stdout)
        logfile.write(result.stderr)
        logfile.write(f'Return Code: {result.returncode}\n\n')