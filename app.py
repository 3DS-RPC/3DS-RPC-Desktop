# Created by Deltaion Lee (MCMi460) on Github

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from layout import Ui_MainWindow
from client import *
from client import _REGION

import webbrowser
import time

from enum import IntEnum

class Page(IntEnum):
    WELCOME = 0
    ENDPOINT = 1
    LINK = 2
    LOADING = 3
    MAIN = 4
    SETTINGS = 5

class UIBridge(QObject):
    updated = pyqtSignal(object)
    errored = pyqtSignal(object, object)
    reauthRequested = pyqtSignal()
    statusChanged = pyqtSignal(str)

def fmtTime(ts):
    if not ts:
        return '\u2014'
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(ts)))
    except (ValueError, TypeError, OverflowError):
        return str(ts)

# 3DS Variables
apiKey = ''
config = {}
if not os.path.isdir(path):
    os.mkdir(path)
if os.path.isfile(privateFile):
    with open(privateFile, 'r') as file:
        js = json.loads(file.read())
        apiKey = js.get('apiKey', '')
        config = js
client = None

# PyQt5 Variables
with open(getPath('./layout/style.qss'), 'r') as file:
    style = file.read()
offlineStyle = style.replace('#FFC693', '#B7B7B7').replace('#E39240', '#AAA6A3')

def loadPix(url):
    _pixmap = QPixmap()
    try:
        _pixmap.loadFromData(requests.get(url, verify = False, timeout = 10).content)
    except Exception:
        pass
    return _pixmap

def up(_label,image):
    _label.clear()
    if isinstance(image,str):
        image = loadPix(image)
    _label.setPixmap(image)

class GUI(Ui_MainWindow):
    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.MainWindow.setFixedSize(600,600)
        if os.name == 'nt':
            self.MainWindow.setWindowIcon(QIcon(getPath('layout/resources/logo.ico')))

        self.underLyingButton2 = QPushButton()
        self.underLyingButton2.clicked.connect(lambda a : self.errorMes())
        self.err = None
        self.traceback = None
        self._customEndpoint = ''
        self.reauthing = False
        self.styled = False
        self.bridge = UIBridge()
        self.bridge.updated.connect(self.update)
        self.bridge.errored.connect(self.error)
        self.bridge.reauthRequested.connect(self.reauthorize)
        self.bridge.statusChanged.connect(self.setStatus)

    def selfService(self, app):
        self.app = app
        self.MainWindow.setStyleSheet(style)
        self.assignVariables()
        self.versionLabel.setText('3DS-RPC v%s' % version)
        self.page = Page.WELCOME
        self.updatePage()

        self.MainWindow.closeEvent = self.closeEvent
        self.underLyingButton = QPushButton()
        self.underLyingButton.clicked.connect(lambda a : self.updateColor())

        if self.state and client.userData.get('consoles'):
            self.stylize()
        self.closeButton.clicked.connect(sys.exit)
        self.settingsButton.clicked.connect(lambda a : self.updatePage(Page.SETTINGS))
        self.okButton.clicked.connect(lambda a : self.updatePage(Page.MAIN))
        self.refreshButton.clicked.connect(self.refresh)

        self.state = False

    def assignVariables(self):
        self.continueButton.clicked.connect(lambda a : self.updatePage(Page.ENDPOINT))

        self.loginButton.clicked.connect(self.changeState)

        self.welcomeLogo.setPixmap(QPixmap(getPath('layout/resources/logo.png')))

        self.endpointButton.clicked.connect(lambda a : self.showEndpointPage())
        self.backEndpointButton.clicked.connect(lambda a : self.updatePage(Page.WELCOME if not client else Page.SETTINGS))
        self.saveEndpointButton.clicked.connect(self.saveEndpoint)
        self.endpointInput.currentIndexChanged.connect(lambda a : self.updateEndpointField())
        self.customEndpointInput.textChanged.connect(self.captureCustomEndpoint)
        self.endpointHint.setStyleSheet('color: #D32F2F;')
        self.updateEndpointField()

    def captureCustomEndpoint(self, text):
        if self.customEndpointInput.isEnabled():
            self._customEndpoint = text
        self.updateSaveState()

    def updateEndpointField(self):
        endpoint = self.endpointInput.currentText().strip()
        if endpoint == 'custom':
            self.customEndpointInput.setEnabled(True)
            self.customEndpointInput.setText(self._customEndpoint or (client.customEndpoint if client else config.get('customEndpoint', '')))
        else:
            self.customEndpointInput.setEnabled(False)
            self.customEndpointInput.setText(getHost(endpoint))
        self.updateSaveState()

    def updateSaveState(self):
        endpoint = self.endpointInput.currentText().strip()
        if endpoint == 'custom':
            try:
                validateEndpoint(self.customEndpointInput.text())
                valid, message = True, ''
            except ValueError as e:
                valid, message = False, str(e)
        else:
            valid, message = True, ''
        self.saveEndpointButton.setEnabled(valid)
        self.endpointHint.setText(message)
        self.endpointHint.setVisible(endpoint == 'custom' and bool(message))

    def showEndpointPage(self):
        if not client:
            return
        index = self.endpointInput.findText(client.endpoint)
        if index != -1:
            self.endpointInput.setCurrentIndex(index)
        self.updateEndpointField()
        self.updatePage(Page.ENDPOINT)

    def saveEndpoint(self):
        global config
        config['endpoint'] = self.endpointInput.currentText().strip() or 'official'
        config['customEndpoint'] = ''
        if config['endpoint'] == 'custom':
            try:
                config['customEndpoint'] = validateEndpoint(self.customEndpointInput.text())
            except ValueError as e:
                dlg = QMessageBox()
                dlg.setWindowTitle('3DS-RPC')
                dlg.setText(str(e))
                dlg.exec_()
                return
        if client:
            client.setEndpoint(config['endpoint'], config['customEndpoint'])
            self.updatePage(Page.SETTINGS)
        else:
            self.updatePage(Page.LINK)

    def stylize(self):
        self.styled = True
        self.underLyingButton.click()

        self.updateProfile()
        self.updateDetails()

        # Update others
        self.okButtonLogout.clicked.connect(self.logout)
        for button in ((self.showElapsedOff, self.showElapsedOn, 'showElapsed'), (self.showProfileButtonOff, self.showProfileButtonOn, 'showProfileButton'), (self.showSmallImageOff, self.showSmallImageOn, 'showSmallImage')):
            self.setFontText(button[0], 'No')
            self.setFontText(button[1], 'Yes')
            button[0].clicked.connect(lambda e, button = button : self.updateSettings(button, False))
            button[1].clicked.connect(lambda e, button = button : self.updateSettings(button, True))
            self.updateSettings(button, client.__dict__[button[2]])
        for label in (self.showElapsedText, self.showProfileButtonText, self.showSmallImageText):
            self.setFontText(label, label.text())

    def updateProfile(self):
        console = client.userData['consoles'][0] if client.userData.get('consoles') else None
        if not console:
            return
        self.miiLabel.setScaledContents(True)
        self.gameIcon.setScaledContents(True)
        self.setFontText(self.username, console.get('username', ''))
        if console.get('mii'):
            up(self.miiLabel, console['mii']['face'])
        self.friendCard.mouseReleaseEvent = lambda event : self.openLink(client.host + '/user/%s' % console['friendCode'])

    def refresh(self):
        if not client:
            return
        try:
            client.loop()
        except Exception as e:
            dlg = QMessageBox()
            dlg.setWindowTitle('3DS-RPC')
            dlg.setText('Refresh failed: %s' % str(e))
            dlg.exec_()
            return
        self.updateProfile()

    def updateSettings(self, button, activate):
        client.__dict__[button[2]] = activate
        client.reflectConfig()
        button[0].setStyleSheet('QPushButton{background-color: #%s;} %s' % (('E1E1E1' if activate else '8BFDB3'), ('QPushButton:hover {background-color: #818181;color: #FFF;}' if activate else '')))
        button[1].setStyleSheet('QPushButton{background-color: #%s;} %s' % (('E1E1E1' if not activate else '8BFDB3'), ('QPushButton:hover {background-color: #818181;color: #FFF;}' if not activate else '')))

    def updateColor(self):
        self.MainWindow.setStyleSheet('')
        console = client.userData['consoles'][0] if client.userData.get('consoles') else None
        online = bool(console and console.get('online'))
        if not online:
            self.MainWindow.setStyleSheet(offlineStyle)
        else:
            self.MainWindow.setStyleSheet(style)

        self.status.setText('Online' if online else 'Offline')

    def setFontText(self, label, text):
        label.setText(text)
        i = 21
        width = 30000
        while label.width() < width and i > 1:
            i -= 1
            font = QFont('Arial', i)
            label.setFont(font)
            metric = QFontMetricsF(label.font())
            width = metric.width(label.text())

    def openLink(self, url:str):
        webbrowser.open(url)

    def closeEvent(self, event):
        if apiKey and client:
            event.ignore()
            self.MainWindow.hide()
            tray.show()
        elif apiKey:
            event.accept()
            self.app.quit()
        else:
            sys.exit()

    def changeState(self):
        global apiKey
        newKey = self.keyInput.text().strip()
        if not newKey:
            dlg = QMessageBox()
            dlg.setWindowTitle('3DS-RPC')
            dlg.setText('Please enter your API key.')
            dlg.exec_()
            return
        apiKey = newKey
        if client:
            client.updateKey(newKey)
            self.reauthing = False
            self.refresh()
            self.updatePage(Page.MAIN)
        else:
            self.MainWindow.close()

    def updatePage(self, page = None):
        self.page = page if page != None else self.page
        self.stackedWidget.setCurrentIndex(page if page != None else self.page)

    def updateDetails(self):
        if not client:
            return
        self.endpointDetail.setText('Endpoint: %s' % client.host)
        console = client.userData['consoles'][0] if client.userData.get('consoles') else None
        if not console:
            self.networkDetail.setText('Network: \u2014')
            self.lastActiveDetail.setText('Last Active: \u2014')
            self.lastOnlineDetail.setText('Last Online: \u2014')
            return
        self.networkDetail.setText('Network: %s' % console.get('network', '\u2014').title())
        self.lastActiveDetail.setText('Last Active: %s' % fmtTime(console.get('lastAccessed')))
        self.lastOnlineDetail.setText('Last Online: %s' % fmtTime(console.get('lastOnline')))

    def update(self, data):
        try:
            if self.page == Page.LOADING:
                self.updatePage(Page.MAIN)
            if client.userData.get('consoles') and not self.styled:
                self.stylize()
            self.updateProfile()
            self.updateDetails()
            if data:
                self.gamePlate.show()
                game = client.userData['consoles'][0]['Presence']['game']
                publisher = (game.get('publisher') or {}).get('name', '')
                self.gamePlate.mouseReleaseEvent = lambda a : self.openLink('https://www.google.com/search?q=%s' % '+'.join((game['name'] + ' ' + publisher).split(' ')))
                if data.get('large_image') and not client.local:
                    up(self.gameIcon, data['large_image'])
                self.setFontText(self.gameName, data['details'])
            else:
                self.gamePlate.hide()
            self.underLyingButton.click()
        except Exception as e:
            print('Update error: %s' % e)

    def error(self, error, traceback):
        self.err = error
        self.traceback = traceback
        print(self.err)
        self.underLyingButton2.click()

    def errorMes(self):
        dlg = QMessageBox()
        dlg.setWindowTitle('3DS-RPC')
        dlg.setText('An error has occurred:\n%s' % str(self.err))
        dlg.exec_()
        print(self.traceback)
        self.app.quit()
        os._exit(0)

    def logout(self):
        os.remove(privateFile)
        sys.exit()

    def reauthorize(self):
        self.reauthing = True
        self.keyInput.setText('')
        self.updatePage(Page.LINK)
        self.MainWindow.show()

    def setStatus(self, message):
        if self.page == Page.LOADING:
            self.loadingText.setText(message)

class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, icon, parent):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)
        self.parent = parent

        reopen = menu.addAction('Show')
        reopen.triggered.connect(self.reopen)

        quit = menu.addAction('Quit')
        quit.triggered.connect(sys.exit)

        self.setContextMenu(menu)

    def reopen(self):
        self.parent.show()
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    lock = acquireLock()
    if not lock:
        QMessageBox.warning(None, '3DS-RPC', '3DS-RPC is already running.')
        sys.exit(0)

    MainWindow = QMainWindow()
    window = GUI(MainWindow)

    tray = SystemTrayApp(QIcon(getPath('layout/resources/tray.png')), MainWindow)
    window.state = False
    window.setupUi(MainWindow)
    window.selfService(app)

    if not apiKey:
        MainWindow.show()
        app.exec_()

    config['apiKey'] = apiKey

    client = Client(apiKey, config, GUI = window)
    window.state = True
    window.setupUi(MainWindow)
    window.selfService(app)
    window.updatePage(Page.LOADING)
    MainWindow.show()

    client.connect()
    threading.Thread(target = client.background, daemon = True).start()

    sys.exit(app.exec_())
