import os
import time
import json
import shutil
import platform
import sysconfig
import subprocess
from .utils.utils import utils


class psiphon(object):
    def __init__(self, inject_host, inject_port):
        super(psiphon, self).__init__()

        self.inject_host = inject_host
        self.inject_port = inject_port

        self.loop = True
        self.libutils = utils(__file__)
        self.kuota_data = {'all': 0}

        self.system_machine = sysconfig.get_platform()
        self.system_platform = platform.system()

        self.file_psiphon_tunnel_core = {
            'win32': '/../storage/psiphon/.tunnel-core/win-i386',
            'win-i386': '/../storage/psiphon/.tunnel-core/win-i386',
            'win-amd64': '/../storage/psiphon/.tunnel-core/win-i386',
            'linux-x86_64': '/../storage/psiphon/.tunnel-core/linux-x86_64',
            'linux-armv7l': '/../storage/psiphon/.tunnel-core/linux-armv7l',
            'linux-armv8l': '/../storage/psiphon/.tunnel-core/linux-armv8l',
            'linux-aarch64': '/../storage/psiphon/.tunnel-core/linux-aarch64',
        }

    def log(self, value, prefix='', color='[G1]', type=1):
        self.liblog.log(value, prefix=prefix, color=color, type=type)

    def log_replace(self, value, color='[G1]'):
        self.liblog.log_replace(value, color=color)

    def _get_file_size(self, value: int = 0, suffixes: list = ['B', 'KB', 'MB', 'GB'], i: int = 0) -> str:
        if not isinstance(value, int):
            return 'unknown'

        while value >= 1000 and i < len(suffixes) - 1:
            value /= 1000
            i += 1

        return f"{value:.3f} {suffixes[i]}"

    def load(self):
        if self.system_machine not in self.file_psiphon_tunnel_core:
            raise OSError(f"This machine ({self.system_machine}) is not supported")

        self.psiphon_tunnel_core = (
            self.libutils.real_path('/../storage/psiphon/psiphon-tunnel-core') +
            ('.exe' if self.system_platform == 'Windows' else ''))
        shutil.copyfile(
            self.libutils.real_path(self.file_psiphon_tunnel_core[self.system_machine]), self.psiphon_tunnel_core)
        if self.system_platform == 'Linux':
            os.system(f"chmod +x {self.psiphon_tunnel_core}")

    def stop(self):
        self.loop = False

    def generate_config(self, port, inject_port, authorization):
        config = {
            "DataStoreDirectory": f"storage/psiphon/{port}",

            "PropagationChannelId": "0000000000000000",
            "SponsorId": "0000000000000000",

            "UpstreamProxyURL": f"http://127.0.0.1:{inject_port}",
            "EmitDiagnosticNotices": True,
            "EmitBytesTransferred": True,

            "DisableLocalHTTPProxy": True,
            "LocalSocksProxyPort": port,
            "TunnelPoolSize": self.tunnels,

            "ConnectionWorkerPoolSize": self.tunnels_worker,
            "Authorizations": [authorization],

            "LimitTunnelProtocols": ["FRONTED-MEEK-HTTP-OSSH", "FRONTED-MEEK-OSSH"],
            "EgressRegion": self.region,
        }

        with self.liblog.lock:
            if not os.path.exists(self.libutils.real_path(f'/../storage/psiphon/{port}/')):
                os.makedirs(self.libutils.real_path(f'/../storage/psiphon/{port}/'))

            shutil.copyfile(
                self.libutils.real_path(f"/../storage/psiphon/.database/psiphon.boltdb"),
                self.libutils.real_path(f"/../storage/psiphon/{port}/psiphon.boltdb")
            )

            with open(self.libutils.real_path(f'/../storage/psiphon/{port}/config.json'), 'w') as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

    def client(self, port, inject_port, authorization):
        def log(value, color='[G1]', type=1):
            if self.loop:
                self.log(value, prefix=port, color=color, type=type)

        self.generate_config(port, inject_port, authorization)
        time.sleep(1.000)
        log('Connecting')
        time.sleep(1.500)
        while self.loop:
            try:
                self.kuota_data[port] = {'all': 0}
                connected = 0
                process = subprocess.Popen(
                    [
                        self.psiphon_tunnel_core, '-config', self.libutils.real_path(
                            f"/../storage/psiphon/{port}/config.json")
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                for line in process.stdout:
                    line = json.loads(line.decode().strip() + '\r')
                    info = line['noticeType']

                    if info == 'BytesTransferred':
                        if not line.get('data').get('diagnosticID'):
                            line['data']['diagnosticID'] = 'aztecrabbit'

                        id = line['data']['diagnosticID']
                        sent = line['data']['sent']
                        received = line['data']['received']

                        self.kuota_data[port]['all'] += sent + received
                        self.kuota_data[port][id] += sent + received
                        self.kuota_data['all'] += sent + received
                        self.log_replace(
                            f"{port} ({id}) ({self._get_file_size(self.kuota_data[port]['all'])}) "
                            f"({self._get_file_size(self.kuota_data['all'])})"
                        )

                    elif info == 'ActiveTunnel':
                        diagnostic_id = line.get('data', {}).get('diagnosticID', 'aztecrabbit')
                        connected += 1
                        self.kuota_data[port][diagnostic_id] = 0
                        log(f"Connected ({diagnostic_id})", color='[Y1]')
                        if ['127.0.0.1', port] not in self.proxyrotator.proxies:
                            self.proxyrotator.proxies.append(['127.0.0.1', port])
                        if connected == self.tunnels:
                            log('Connected', color='[Y1]')

                    elif info == 'Alert':
                        message = line['data']['message']

                        if 'SOCKS proxy accept error' in message:
                            log('SOCKS proxy accept error ({})'.format(
                                'connected' if connected else 'disconnected'), color='[R1]')

                        elif 'meek round trip failed' in message:
                            if connected == self.tunnels:
                                if (message == 'meek round trip failed: remote error: tls: bad record MAC' or
                                        message == 'meek round trip failed: context deadline exceeded' or
                                        message == 'meek round trip failed: EOF' or
                                        'psiphon.CustomTLSDial' in message):
                                    self.reconnecting_color = '[R1]'
                                    break

                                """
                                else:
                                    self.log(f'001: \n\n{line}\n', color='[P1]')
                                """

                        elif (
                                ('A connection attempt failed because the connected party did not properly '
                                    'respond after a period of time') in message or
                                ('No connection could be made because the target machine '
                                    'actively refused it.') in message or
                                'tunnel.dialTunnel: dialConn is not a Closer' in message or
                                'psiphon.(*ServerContext).DoConnectedRequest' in message or
                                'making proxy request: unexpected EOF' in message or
                                'response status: 403 Forbidden' in message or
                                'meek connection has closed' in message or
                                'meek connection is closed' in message or
                                'psiphon.(*MeekConn).relay' in message or
                                'unexpected status code:' in message or
                                'RemoteAddr returns nil' in message or
                                'network is unreachable' in message or
                                'close tunnel ssh error' in message or
                                'tactics request failed' in message or
                                'API request rejected' in message or
                                'context canceled' in message or
                                'no such host' in message):
                            continue

                        elif ('controller shutdown due to component failure' in message or
                                'psiphon.(*ServerContext).DoStatusRequest' in message or
                                'psiphon.(*Tunnel).sendSshKeepAlive' in message or
                                'psiphon.(*MeekConn).readPayload' in message or
                                'psiphon.(*Tunnel).Activate' in message or
                                'underlying conn is closed' in message or
                                'duplicate tunnel:' in message or
                                'tunnel failed:' in message):
                            self.reconnecting_color = '[R1]'
                            break

                        elif ('controller shutdown due to component failure' in message or
                                'No address associated with hostname' in message):
                            log(f"007:\n\n{line}\n", color='[R1]')
                            # self.reconnecting_color = '[R1]'
                            # break
                        elif ('bind: address already in use' in message):
                            log(f"Port {port} already in use", color='[R1]')
                            self.stop()

                        else:
                            log(line, color='[R1]', type=2)

                    else:
                        log(line, color='[CC]', type=3)

            except json.decoder.JSONDecodeError:
                log(line.decode().strip(), color='[R1]')

            finally:
                process.kill()
                if ['127.0.0.1', port] in self.proxyrotator.proxies:
                    self.proxyrotator.proxies.remove(['127.0.0.1', port])
                if self.system_platform == 'Windows':
                    time.sleep(0.750)
                log(f"Reconnecting ({self._get_file_size(self.kuota_data[port]['all'])})")
