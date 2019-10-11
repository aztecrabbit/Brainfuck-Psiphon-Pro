import sys
import src
import threading

def main():
    ''' variables '''
    proxyrotator_host = str('0.0.0.0')
    proxyrotator_port = int('3080')
    inject_host = str('0.0.0.0')
    inject_port = int('8989')

    ''' utils '''
    utils = src.utils(__file__)

    ''' log '''
    log = src.log()
    log.type = 1
    log.prefix = 'INFO'
    log.value_prefix = "datetime.datetime.now().strftime('[%H:%M:%S]{clear} [P1]::{clear} {color}{prefix}{clear} [P1]::{clear}')"

    ''' proxyrotator '''
    proxyrotator = src.proxyrotator((proxyrotator_host, proxyrotator_port), src.proxyrotator_handler)
    proxyrotator.liblog = log
    proxyrotator.proxies = []
    proxyrotator.username = 'aztecrabbit'
    proxyrotator.password = 'aztecrabbit'
    proxyrotator.buffer_size = 65535
    proxyrotator.socks_version = 5
    proxyrotator_thread = threading.Thread(target=proxyrotator.serve_forever, args=())
    proxyrotator_thread.daemon = True
    proxyrotator_thread.start()

    ''' redsocks '''
    redsocks = src.redsocks()
    redsocks.liblog = log
    redsocks.ip = '127.0.0.1'
    redsocks.port = proxyrotator_port
    redsocks.type = 'socks5'
    redsocks.login = 'aztecrabbit'
    redsocks.password = 'aztecrabbit'
    redsocks.log_output = utils.real_path('/storage/redsocks/redsocks.log')
    redsocks.redsocks_config = utils.real_path('/storage/redsocks/redsocks.conf')
    redsocks.start()

    ''' psiphon '''
    psiphon = src.psiphon(inject_host, inject_port)
    psiphon.liblog = log
    psiphon.tunnels = 8
    psiphon.proxyrotator = proxyrotator
    for i in range(1):
        psiphon_client_port = proxyrotator_port + 1 + i
        threading.Thread(target=psiphon.client, args=(psiphon_client_port, )).start()

    try:
        ''' inject '''
        log.log(f'Domain Fronting running on port {inject_port}', color='[G1]')
        log.log(f'Proxy Rotator running on port {proxyrotator_port}', color='[G1]')
        inject = src.inject((inject_host, inject_port), src.inject_handler)
        inject.rules = [
            {
                'target-list': ['akamai.net:80'],
                'tunnel-type': '3',
                'remote-proxies': ['video.iflix.com', 'videocdn-2.iflix.com'],
            },
        ]
        inject.liblog = log
        inject.libredsocks = redsocks
        inject.socket_server_timeout = 1
        inject.serve_forever()
    except KeyboardInterrupt:
        inject.stop = True
        with utils.lock:
            psiphon.stop()
            redsocks.stop()
            log.keyboard_interrupt()
            proxyrotator.stop()
    finally:
        pass

if __name__ == '__main__':
    main()
