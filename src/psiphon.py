import time
import json
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

    def log(self, value, prefix='', color='[G1]', type=1):
        self.liblog.log(value, prefix=prefix, color=color, type=type)

    def log_replace(self, value, color='[G1]'):
        self.liblog.log_replace(value, color=color)

    def size(self, bytes, suffixes=['B', 'KB', 'MB', 'GB'], i=0):
        while bytes >= 1000 and i < len(suffixes) - 1:
            bytes /= 1000; i += 1

        return '{:.3f} {}'.format(bytes, suffixes[i])

    def stop(self):
        self.loop = False

    def client(self, port):
        def log(value, color='[G1]', type=1):
            self.log(value, prefix=port, color=color, type=type)

        psiphon_tunnel_core = self.libutils.real_path('/../storage/psiphon/psiphon-tunnel-core')
        psiphon_config = self.libutils.real_path(f'/../storage/psiphon/{port}/config.json')

        time.sleep(1.000)
        log('Connecting')
        time.sleep(1.500)
        while self.loop:
            try:
                ''' variables '''
                self.kuota_data[port] = {'all': 0}
                connected = 0

                process = subprocess.Popen(f'{psiphon_tunnel_core} -config {psiphon_config}'.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for line in process.stdout:                    
                    line = json.loads(line.decode().strip() + '\r')
                    info = line['noticeType']

                    if info == 'BytesTransferred':
                        id, sent, received = line['data']['diagnosticID'], line['data']['sent'], line['data']['received']
                        self.kuota_data[port]['all'] += sent + received
                        self.kuota_data[port][id] += sent + received
                        self.kuota_data['all'] += sent + received
                        self.log_replace(f"{port} ({id}) ({self.size(self.kuota_data[port][id])}) ({self.size(self.kuota_data['all'])})")

                    elif info == 'ActiveTunnel':
                        connected += 1
                        self.kuota_data[port][line['data']['diagnosticID']] = 0
                        log(f"Connected ({line['data']['diagnosticID']})", color='[Y1]')
                        if connected == self.tunnels:
                            self.proxyrotator.proxies.append(['127.0.0.1', port])
                            log('Connected', color='[Y1]')

                    elif info == 'Alert':
                        message = line['data']['message']

                        if 'SOCKS proxy accept error' in message:
                            log('SOCKS proxy accept error ({})'.format('connected' if connected else 'disconnected'), color='[R1]')

                        elif 'meek round trip failed' in message:
                            if connected == self.tunnels:
                                if message == 'meek round trip failed: remote error: tls: bad record MAC' or \
                                   message == 'meek round trip failed: context deadline exceeded' or \
                                   message == 'meek round trip failed: EOF' or \
                                   'psiphon.CustomTLSDial' in message:
                                    # ~
                                    self.reconnecting_color = '[R1]'
                                    break

                                '''else:
                                    self.log(f'001: \n\n{line}\n', color='[P1]')

                                ?
                                '''

                        elif 'A connection attempt failed because the connected party did not properly respond after a period of time' in message or \
                         'context canceled' in message or \
                         'API request rejected' in message or \
                         'RemoteAddr returns nil' in message or \
                         'network is unreachable' in message or \
                         'close tunnel ssh error' in message or \
                         'tactics request failed' in message or \
                         'unexpected status code:' in message or \
                         'meek connection is closed' in message or \
                         'psiphon.(*MeekConn).relay' in message or \
                         'meek connection has closed' in message or \
                         'response status: 403 Forbidden' in message or \
                         'making proxy request: unexpected EOF' in message or \
                         'tunnel.dialTunnel: dialConn is not a Closer' in message or \
                         'psiphon.(*ServerContext).DoConnectedRequest' in message or \
                         'No connection could be made because the target machine actively refused it.' in message or \
                         'no such host' in message:
                            continue

                        elif 'controller shutdown due to component failure' in message or \
                          'psiphon.(*ServerContext).DoStatusRequest' in message or \
                          'psiphon.(*Tunnel).sendSshKeepAlive' in message or \
                          'psiphon.(*MeekConn).readPayload' in message or \
                          'psiphon.(*Tunnel).Activate' in message or \
                          'underlying conn is closed' in message or \
                          'duplicate tunnel:' in message or \
                          'tunnel failed:' in message:
                            # ~
                            self.reconnecting_color = '[R1]'
                            break

                        elif 'controller shutdown due to component failure' in message or \
                          'No address associated with hostname' in message:
                            log(f"007:\n\n{line}\n", color='[R1]')
                            # self.reconnecting_color = '[R1]'
                            # break

                        else:
                            log(line, color='[R1]', type=3)

                    else:
                        log(line, color='[CC]', type=3)

            except json.decoder.JSONDecodeError:
                log(line.decode().strip(), color='[R1]')
            finally:
                process.kill()

                if ['127.0.0.1', port] in self.proxyrotator.proxies:
                    self.proxyrotator.proxies.remove(['127.0.0.1', port])

                if self.loop:
                    log(f"Reconnecting ({self.size(self.kuota_data[port]['all'])})")
