import subprocess

with open('update.log', 'a') as logfile:
    logfile.write(f'Command: git pull\n')
    result = subprocess.run(
        'git pull',
        shell=True,
        capture_output=True,  # Capture the command output
        text=True
    )
    # Write the command output to the log file
    logfile.write(result.stdout)
    logfile.write(result.stderr)
    logfile.write(f'Return Code: {result.returncode}\n\n')

subprocess.run('sudo systemctl restart flask.service', shell=True,text=True)