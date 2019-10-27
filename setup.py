import os
import sys
import subprocess

def real_path(file_name):
    return os.path.dirname(os.path.abspath(__file__)) + file_name

def log_tab(value='', enter=False):
    print('{}|   {}'.format('\n' if enter else '', value))

def command(command, silent=False):
    if not silent:
        print(f'Executing: {command}\n')
    
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

class xgit(object):
    def __init__(self):
        super(xgit, self).__init__()

        self.enabled = False

    def load(self):
        response = command('git --version', silent=True)
        for line in response.stdout:
            if line.decode().strip().startswith('git version'):
                self.enabled = True
            break

        if not self.enabled:
            log_tab('git not installed. please install git first!', enter=True)
            log_tab('\n')

        return self

    def clone(self, path, repo, folder_name):
        if not self.enabled:
            return

        response = command(f'cd {real_path(path)} && git clone {repo} {folder_name}')
        for line in response.stdout:
            line = line.decode().strip()

            if 'already exists and is not an empty directory.' in line:
                log_tab('Already installed.')
                break

            log_tab(line)

        log_tab('\n')

    def pull(self, path='', force=False):
        if not self.enabled:
            return

        response = command(f'cd {real_path(path)} && git pull')
        for line in response.stdout:
            line = line.decode().strip()
            log_tab(line)

        log_tab('\n')

def main():
    git = xgit().load()

    if len(sys.argv) <= 1:
        log_tab('Usage: python3 setup.py [install] [update]', enter=True)
        log_tab('\n')

    elif sys.argv[1] == 'install':
        git.clone('/src', 'https://github.com/AztecRabbit/log', 'log')
        git.clone('/src', 'https://github.com/AztecRabbit/utils', 'utils')
        git.clone('/src', 'https://github.com/AztecRabbit/inject', 'inject')
        git.clone('/src', 'https://github.com/AztecRabbit/redsocks', 'redsocks')
        git.clone('/src', 'https://github.com/AztecRabbit/proxyrotator', 'proxyrotator')

    elif sys.argv[1] == 'update':
        git.pull('/src/log')
        git.pull('/src/utils')
        git.pull('/src/inject')
        git.pull('/src/redsocks')
        git.pull('/src/proxyrotator')
        git.pull()

if __name__ == '__main__':
    main()
