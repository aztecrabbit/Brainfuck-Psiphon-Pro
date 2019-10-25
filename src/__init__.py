import os
from .psiphon import psiphon
from .log.log import log
from .utils.utils import utils
from .inject.inject import inject
from .inject.inject import inject_handler
from .redsocks.redsocks import redsocks
from .proxyrotator.proxyrotator import proxyrotator
from .proxyrotator.proxyrotator import proxyrotator_handler

utils(__file__).banner([
    'Brainfuck Tunnel [Psiphon Pro Version. 1.3.191025]',
    '(c) 2019 Aztec Rabbit.',
])
