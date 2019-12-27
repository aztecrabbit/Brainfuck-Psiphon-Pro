import os
import sys
import shutil
import subprocess


class _setup(object):
    def __init__(self):
        super(_setup, self).__init__()

        self.enabled = False
        self.libraries = []

    def real_path(self, file_name=''):
        return os.path.dirname(os.path.abspath(__file__)) + file_name

    def log(self, value='', tab='|   '):
        print(tab + value)

    def load(self):
        if shutil.which('git'):
            self.enabled = True

        self.libraries = open(self.real_path('/libraries.txt')).readlines()
        self.libraries = [x.strip() for x in self.libraries if x]

        if not self.enabled:
            self.log(tab='')
            self.log('git not installed. please install git first!')
            self.log('\n', tab='|')

        return self

    def execute(self, command):
        self.log(f'Executing: {command}' + '\n', tab='')

        return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def usage(self):
        self.log(tab='')
        self.log(f'Usage: python3 {sys.argv[0]} [install] [update]')
        self.log('\n', tab='|')

    def install(self):
        if not self.enabled:
            return

        for name in self.libraries:
            response = self.execute(f"cd {self.real_path('/src')} && git clone https://github.com/aztecrabbit/{name}")
            for line in response.stdout:
                line = line.decode().strip()

                if 'already exists and is not an empty directory.' in line:
                    self.log('Already installed.')
                    break

                self.log(line)

            self.log('\n', tab='|')

    def update(self, force=False):
        if not self.enabled:
            return

        path_list = []
        path_list.append(self.real_path())
        for path in self.libraries:
            path_list.append(self.real_path('/src/' + path))

        for path in path_list:
            response = self.execute(f'cd {path} && git pull')
            for line in response.stdout:
                line = line.decode().strip()

                self.log(line)

            self.log('\n', tab='|')


def main():
    setup = _setup().load()

    if len(sys.argv) <= 1:
        setup.usage()

    elif sys.argv[1] == 'install':
        setup.install()

    elif sys.argv[1] == 'update':
        setup.update()


if __name__ == '__main__':
    main()
