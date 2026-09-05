# Created by Deltaion Lee (MCMi460) on Github

import requests, os, sys, time
import xmltodict, json
import pickle
import asyncio, threading
from urllib.parse import urlsplit
try:
    from api import *
except:
    sys.path.append('../')
    from api import *
import pypresence
from PyQt5.QtCore import QLockFile

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

version = 0.32

# Endpoint presets. The selection lives client-side in the config.
officialHost = 'https://3dsrpc.com'
host = officialHost

def getHost(endpoint:str, customEndpoint:str = '') -> str:
    endpoint = (endpoint or 'official').lower()
    if endpoint == 'custom' and customEndpoint:
        return customEndpoint.strip().rstrip('/')
    return officialHost

def validateEndpoint(url:str) -> str:
    url = (url or '').strip()
    if not url:
        raise ValueError('Please enter a custom endpoint URL.')
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.netloc:
        raise ValueError('Custom endpoint must be a full URL, e.g. https://your-server.example.com')
    if parts.path not in ('', '/'):
        raise ValueError('Custom endpoint cannot include a subpath. Use just the host, e.g. https://your-server.example.com')
    if parts.query or parts.fragment:
        raise ValueError('Custom endpoint cannot include a query string or fragment.')
    return url.rstrip('/')

_REGION = typing.Literal['ALL', 'US', 'JP', 'GB', 'KR', 'TW']
path = getAppPath()
privateFile = os.path.join(path, 'private.txt')
logFile = os.path.join(path, 'logs.txt')

# Config template
configTemplate = {
    'apiKey': '',
    'endpoint': 'official',
    'customEndpoint': '',
    'showElapsed': True,
    'showProfileButton': False,
    'showSmallImage': False,
    'fetchTime': 60,
}

lockPath = os.path.join(path, '3dsrpc.lock')

def acquireLock(timeout:int = 100):
    lock = QLockFile(lockPath)
    return lock if lock.tryLock(timeout) else None

def log(text:str):
    with open(logFile, 'a') as file:
        file.write('%s: %s\n' % (time.time(), text.replace('\n',' ')))
    print(Color.RED + text)

class RateLimitedError(Exception):
    def __init__(self, retry_after = None):
        try:
            self.wait = float(retry_after)
        except (TypeError, ValueError):
            self.wait = 30
        super().__init__('Rate limited. Waiting %ss.' % self.wait)

class BackendOfflineError(Exception):
    def __init__(self):
        super().__init__('Backend currently offline. Retrying later.')

class InvalidAPIKeyError(Exception):
    def __init__(self):
        super().__init__('Invalid console API key.')

class Client():
    def __init__(self, apiKey: str, config:dict, *, GUI = None):
        with open(privateFile, 'w') as file: # Save API key and config to file
            js = configTemplate
            js['apiKey'] = apiKey
            for key in config.keys():
                if key in configTemplate.keys():
                    js[key] = config[key]
            file.write(json.dumps(js))

        # Server-auth variables
        self.apiKey = js.get('apiKey', '')

        # Endpoint variables
        self.endpoint = js.get('endpoint', 'official')
        self.customEndpoint = js.get('customEndpoint', '')
        self.host = getHost(self.endpoint, self.customEndpoint)
        self.local = '127.0.0.1' in self.host or 'localhost' in self.host

        # Client-config
        self.connected = False
        self.userData = {}

        # Re-authentication coordination
        self.authWait = threading.Event()

        # Discord-related variables
        self.currentGame = {'@id': None}
        self.showElapsed = js['showElapsed']
        self.showProfileButton = js['showProfileButton']
        self.showSmallImage = js['showSmallImage']
        self.fetchTime = js['fetchTime']

        # Game logging
        self.gameLog = []

        # GUI-related
        self.GUI = GUI

    # Reflect to config file
    def reflectConfig(self):
        with open(privateFile, 'w') as file:
            js = configTemplate
            for key in js.keys():
                js[key] = self.__dict__[key]
            file.write(json.dumps(js))

    # Change the endpoint (official / custom)
    def setEndpoint(self, endpoint:str, customEndpoint:str = ''):
        self.endpoint = endpoint
        self.customEndpoint = customEndpoint
        self.host = getHost(endpoint, customEndpoint)
        self.local = '127.0.0.1' in self.host or 'localhost' in self.host
        self.reflectConfig()

    # Set a new API key after an invalid/expired one
    def updateKey(self, apiKey:str):
        self.apiKey = apiKey
        self.authWait.set()
        self.reflectConfig()

    # Get from API
    def APIget(self, route:str, content:dict = {}):
        return requests.get(self.host + '/api/' + route, params = content, headers = {'User-Agent':'3DS-RPC/%s' % version, 'X-API-KEY': self.apiKey,})

    # Connect to PyPresence
    def connect(self, pipe:str = '0'):
        try:
            self.rpc = pypresence.Presence('1023094010383970304', pipe = pipe)
            self.rpc.connect()
        except Exception as e:
            if self.GUI:
                self.GUI.bridge.errored.emit(str(e), traceback.format_exc())
            else:
                raise e
        self.connected = True

    # Disconnect
    def disconnect(self):
        try:self.rpc.clear()
        except:pass
        try:self.rpc.close()
        except:pass
        self.rpc = None
        self.connected = False

    def fetch(self):
        r = self.APIget('user/activeConsoles')
        if r.status_code == 429:
            raise RateLimitedError(r.headers.get('Retry-After'))
        if r.status_code == 502:
            raise BackendOfflineError()
        try:
            r = r.json()
        except:
            APIExcept(r)
        if r['Exception']:
            error = r['Exception']['Error']
            if 'offline' in error:
                raise BackendOfflineError()
            if 'invalid console API key' in error:
                raise InvalidAPIKeyError()
            raise APIException(r['Exception'])
        return r

    def loop(self):
        userData = self.fetch();self.userData = userData
        console = userData['consoles'][0] if userData.get('consoles') else None

        logger = 'Update'
        if console and console.get('online') and console.get('Presence'):

            presence = console['Presence']
            game = presence['game']
            img_url = game.get('banner_url') or game.get('icon_url')
            log('Game image URL: %r (banner=%r icon=%r)' % (img_url, game.get('banner_url'), game.get('icon_url')))

            if self.currentGame != game:
                logger += ' [%s -> %s]' % (self.currentGame['@id'], game['@id'])
                self.currentGame = game
                self.start = int(time.time())
            kwargs = {
                'details': game['name'],
                # buttons = [{'label': 'Label', 'url': 'http://DOMAIN.WHATEVER'},]
                # eShop URL could be https://api.qrserver.com/v1/create-qr-code/?data=ESHOP://{uid}
                # But... that wouldn't be very convenient. It's unfortunate how Nintendo does not have an eShop website for the 3DS
                # Include View Profile setting?
                # Certainly something when presence['joinable'] == True
            }
            if img_url:
                kwargs['large_image'] = img_url.replace('/cdn/', self.host + '/cdn/')
                kwargs['large_text'] = game['name']
            if presence.get('gameDescription'):
                kwargs['state'] = presence['gameDescription']
            if self.showProfileButton and console.get('username'):
                kwargs['buttons'] = [{'label': 'Profile', 'url': self.host + '/user/' + console['friendCode'] + '?network=' + console.get('network', '')},]
            if self.showElapsed:
                kwargs['start'] = self.start
            if self.showSmallImage and console.get('username') and img_url:
                kwargs['small_image'] = console['mii']['face']
                kwargs['small_text'] = '-'.join(console['friendCode'][i:i+4] for i in range(0, 12, 4))
            for key in list(kwargs): # Blatant rip from OpenEmuRPC (also made by me. Check it out if you want)
                if isinstance(kwargs[key], str) and not 'image' in key:
                    if len(kwargs[key]) < 2:
                        del kwargs[key]
                    elif len(kwargs[key]) > 128:
                        kwargs[key] = kwargs[key][:128]
            if self.connected:self.rpc.update(**kwargs)
            if self.GUI:self.GUI.bridge.updated.emit(kwargs)
        else:
            logger = 'Clear [%s -> %s]' % (self.currentGame['@id'], None)
            self.currentGame = {'@id': None}
            if self.connected:self.rpc.clear()
            if self.GUI:self.GUI.bridge.updated.emit(None)
        self.gameLog.append(logger)

    def background(self):
        try:
            while True:
                try:
                    self.loop()
                except InvalidAPIKeyError:
                    log('Invalid API key.')
                    if self.GUI:
                        self.GUI.bridge.reauthRequested.emit()
                    else:
                        log('Use the \'apikey\' command to set a new key.')
                    self.authWait.wait()
                    self.authWait.clear()
                except (RateLimitedError, BackendOfflineError) as e:
                    log(str(e))
                    if self.GUI:
                        self.GUI.bridge.statusChanged.emit('Rate limited. Retrying shortly...' if isinstance(e, RateLimitedError) else 'Backend offline. Retrying...')
                    time.sleep(getattr(e, 'wait', self.fetchTime))
                time.sleep(self.fetchTime) # Wait 60 seconds between calls
        except Exception as e:
            if self.GUI:
                self.GUI.bridge.errored.emit(str(e), traceback.format_exc())
            else:
                log('Failed\n' + str(e))
                print(traceback.format_exc())
                os._exit(0)

def main():
    lock = acquireLock()
    if not lock:
        print('%sAnother instance of 3DS-RPC is already running.%s' % (Color.RED, Color.DEFAULT))
        os._exit(0)

    apiKey = None
    config = {}

    # Create directory for logging and API key saving
    if not os.path.isdir(path):
        os.mkdir(path)
    try:
        if os.path.isfile(privateFile):
            with open(privateFile, 'r') as file:
                js = json.loads(file.read())
                apiKey = js.get('apiKey', '')
                config = js
                config.pop('apiKey', None)
    except:
        apiKey = None
        config = {}

    # The endpoint must be known before we can connect, so ask first if it's missing
    if not config.get('endpoint'):
        print('%sWhich endpoint would you like to use? (official or custom)%s' % (Color.YELLOW, Color.DEFAULT))
        endpoint = input('Please enter your endpoint (official or custom)\n> %s' % Color.PURPLE)
        if endpoint.lower() not in ('official', 'custom'):
            endpoint = 'official'
        config['endpoint'] = endpoint
        if endpoint.lower() == 'custom':
            while True:
                customUrl = input('Please enter your custom endpoint URL\n> %s' % Color.PURPLE)
                try:
                    config['customEndpoint'] = validateEndpoint(customUrl)
                    break
                except ValueError as e:
                    print('%s%s%s' % (Color.RED, e, Color.DEFAULT))
        print(Color.DEFAULT, end = '')

    if not apiKey:
        print('%sPlease grab your API key from the Settings page on your endpoint%s' % (Color.YELLOW, Color.DEFAULT))
        apiKey = input('Please enter your API key\n> %s' % Color.PURPLE)
        print(Color.DEFAULT, end = '')

    try:
        client = Client(apiKey, config)
    except (AssertionError) as e:
        if os.path.isfile(privateFile):
            os.remove(privateFile)
        raise e

    print('%sConnecting to %s%s' % (Color.BLUE, client.host, Color.DEFAULT))

    # Begin main thread for user configuration
    con = Console(client)
    try:
        client.connect()
    except Exception as e:
        con._log('\'%s\'\nFailed to connect to Discord! Try again with the \'discord\' command' % e, Color.RED)

    threading.Thread(target = client.background, daemon = True).start() # Start client background

    con._main() # Begin main loop for console program

if __name__ == '__main__':
    main()
