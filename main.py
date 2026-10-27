import json, os, sys
from pathlib import Path
from urllib.parse import quote_plus
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLineEdit, QPushButton, QToolButton, QMenu, QDialog, QFormLayout,
    QComboBox, QCheckBox, QSpinBox, QDialogButtonBox, QLabel, QMessageBox, QListWidget,
    QInputDialog)
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

APP_NAME = 'Configurable Browser'
DATA_DIR = Path.home() / '.configurable-browser'
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / 'settings.json'
DEFAULTS = {
    'home_page': 'https://www.google.com', 'search_engine': 'DuckDuckGo', 'theme': 'Midnight',
    'zoom': 100, 'javascript': True, 'images': True, 'cookies': True,
    'restore_tabs': True, 'show_bookmarks_bar': True, 'custom_css': '', 'user_agent': '',
    'new_tab_page': 'home'
}
THEMES = {
    'Midnight': {'bg':'#11131a','panel':'#1b1e29','field':'#252a38','text':'#eef1fa','muted':'#9ca6bd','accent':'#7c9cff','border':'#343a4d'},
    'Light': {'bg':'#f3f5f9','panel':'#ffffff','field':'#edf0f6','text':'#202432','muted':'#687086','accent':'#4169e1','border':'#d9deea'},
    'OLED Black': {'bg':'#000000','panel':'#090909','field':'#171717','text':'#f5f5f5','muted':'#aaaaaa','accent':'#64e6bd','border':'#292929'},
    'Forest': {'bg':'#101a17','panel':'#182822','field':'#21372e','text':'#e6f4ec','muted':'#a2c0b0','accent':'#66d19e','border':'#2d4b3d'},
    'Sunset': {'bg':'#21151d','panel':'#30202b','field':'#432c38','text':'#fff0e8','muted':'#d2aebd','accent':'#ff9b70','border':'#563847'}
}
SEARCH = {'DuckDuckGo':'https://duckduckgo.com/?q={}', 'Google':'https://www.google.com/search?q={}', 'Bing':'https://www.bing.com/search?q={}', 'Brave':'https://search.brave.com/search?q={}', 'Wikipedia':'https://en.wikipedia.org/wiki/Special:Search?search={}', 'Startpage':'https://www.startpage.com/sp/search?q={}'}

def load_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
        return {**DEFAULTS, **data}
    except Exception: return DEFAULTS.copy()

def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding='utf-8')

class BrowserTab(QWidget):
    def __init__(self, browser, url=None):
        super().__init__(); self.browser = browser
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        self.view = QWebEngineView(self)
        self.view.urlChanged.connect(lambda u: browser.update_address(self, u))
        self.view.titleChanged.connect(lambda title: browser.update_title(self, title))
        self.view.loadProgress.connect(lambda p: browser.statusBar().showMessage(f'Loading… {p}%', 1200))
        self.view.loadFinished.connect(lambda ok: browser.after_load(self, ok))
        layout.addWidget(self.view)
        self.apply_settings()
        self.view.setUrl(QUrl(url or browser.settings['home_page']))
    def apply_settings(self):
        s = self.view.settings(); cfg = self.browser.settings
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, cfg['javascript'])
        s.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, cfg['images'])
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.view.setZoomFactor(max(25, min(300, int(cfg['zoom']))) / 100)
        if cfg.get('user_agent'):
            self.view.page().profile().setHttpUserAgent(cfg['user_agent'])

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent); self.setWindowTitle('Browser settings'); self.setMinimumWidth(460)
        self.cfg = parent.settings.copy(); form = QFormLayout(self)
        self.home = QLineEdit(self.cfg['home_page']); form.addRow('Home page URL', self.home)
        self.search = QComboBox(); self.search.addItems(SEARCH); self.search.setCurrentText(self.cfg['search_engine']); form.addRow('Search engine', self.search)
        self.theme = QComboBox(); self.theme.addItems(THEMES); self.theme.setCurrentText(self.cfg['theme']); form.addRow('Colour theme', self.theme)
        self.zoom = QSpinBox(); self.zoom.setRange(25,300); self.zoom.setSuffix('%'); self.zoom.setValue(int(self.cfg['zoom'])); form.addRow('Default page zoom', self.zoom)
        self.js = QCheckBox('Allow JavaScript'); self.js.setChecked(self.cfg['javascript']); form.addRow('Web features', self.js)
        self.images = QCheckBox('Load images'); self.images.setChecked(self.cfg['images']); form.addRow('', self.images)
        self.cookies = QCheckBox('Allow cookies and site storage'); self.cookies.setChecked(self.cfg['cookies']); form.addRow('', self.cookies)
        self.restore = QCheckBox('Restore tabs from previous session'); self.restore.setChecked(self.cfg['restore_tabs']); form.addRow('Startup', self.restore)
        self.bookbar = QCheckBox('Show bookmarks bar'); self.bookbar.setChecked(self.cfg['show_bookmarks_bar']); form.addRow('', self.bookbar)
        self.ua = QLineEdit(self.cfg.get('user_agent','')); self.ua.setPlaceholderText('Leave blank to use QtWebEngine default'); form.addRow('Custom user agent', self.ua)
        self.css = QLineEdit(self.cfg.get('custom_css','')); self.css.setPlaceholderText('Optional CSS URL (advanced)'); form.addRow('Custom CSS URL', self.css)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)
    def values(self):
        return {'home_page':self.home.text().strip() or DEFAULTS['home_page'], 'search_engine':self.search.currentText(), 'theme':self.theme.currentText(), 'zoom':self.zoom.value(), 'javascript':self.js.isChecked(), 'images':self.images.isChecked(), 'cookies':self.cookies.isChecked(), 'restore_tabs':self.restore.isChecked(), 'show_bookmarks_bar':self.bookbar.isChecked(), 'user_agent':self.ua.text().strip(), 'custom_css':self.css.text().strip(), 'new_tab_page':self.cfg.get('new_tab_page','home')}

class Browser(QMainWindow):
    def __init__(self):
        super().__init__(); self.settings=load_settings(); self.bookmarks=[]; self.history=[]
        self.bookmark_file=DATA_DIR/'bookmarks.json'; self.history_file=DATA_DIR/'history.json'; self.session_file=DATA_DIR/'session.json'
        self.bookmarks=self.read_json(self.bookmark_file, []); self.history=self.read_json(self.history_file, [])
        self.setWindowTitle(APP_NAME); self.resize(1360,850)
        root=QWidget(); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        self.tabs=QTabWidget(); self.tabs.setDocumentMode(True); self.tabs.setMovable(True); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab); self.tabs.currentChanged.connect(self.tab_changed); outer.addWidget(self.tabs)
        nav=QWidget(); navrow=QHBoxLayout(nav); navrow.setContentsMargins(10,7,10,7); navrow.setSpacing(6); outer.insertWidget(0,nav)
        self.back_btn=self.tool('←','Back',lambda:self.current_view() and self.current_view().back(),navrow)
        self.forward_btn=self.tool('→','Forward',lambda:self.current_view() and self.current_view().forward(),navrow)
        self.reload_btn=self.tool('↻','Reload',lambda:self.current_view() and self.current_view().reload(),navrow)
        self.home_btn=self.tool('⌂','Home',self.go_home,navrow)
        self.address=QLineEdit(); self.address.setPlaceholderText('Search or enter a URL'); self.address.returnPressed.connect(self.navigate); navrow.addWidget(self.address,1)
        self.star=self.tool('☆','Bookmark this page',self.add_bookmark,navrow)
        self.new_btn=self.tool('+','New tab (Ctrl+T)',self.new_tab,navrow)
        self.menu_button=QToolButton(); self.menu_button.setText('☰'); self.menu_button.setToolTip('Browser menu'); self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup); self.menu_button.setMenu(self.make_menu()); navrow.addWidget(self.menu_button)
        self.bookbar=QWidget(); self.bookbar_layout=QHBoxLayout(self.bookbar); self.bookbar_layout.setContentsMargins(10,2,10,5); self.bookbar_layout.setSpacing(5); outer.insertWidget(1,self.bookbar)
        self.apply_cookie_policy(); self.apply_theme(); self.refresh_bookmarks_bar()
        self.add_shortcut('Ctrl+L', lambda:self.address.setFocus() or self.address.selectAll())
        self.add_shortcut('Ctrl+T',self.new_tab); self.add_shortcut('Ctrl+W',lambda:self.close_tab(self.tabs.currentIndex())); self.add_shortcut('Ctrl+R',lambda:self.current_view() and self.current_view().reload()); self.add_shortcut('Alt+Left',lambda:self.current_view() and self.current_view().back()); self.add_shortcut('Alt+Right',lambda:self.current_view() and self.current_view().forward()); self.add_shortcut('Ctrl+D',self.add_bookmark); self.add_shortcut('Ctrl+Plus',lambda:self.change_zoom(10)); self.add_shortcut('Ctrl+-',lambda:self.change_zoom(-10)); self.add_shortcut('Ctrl+0',lambda:self.set_zoom(100)); self.add_shortcut('F11',self.toggle_fullscreen)
        if self.settings['restore_tabs'] and self.read_json(self.session_file,[]):
            urls=self.read_json(self.session_file,[])
            for url in urls: self.new_tab(url)
        else: self.new_tab()
    def read_json(self,path,default):
        try:return json.loads(path.read_text(encoding='utf-8'))
        except Exception:return default
    def write_json(self,path,data):
        try:path.write_text(json.dumps(data,indent=2),encoding='utf-8')
        except Exception:pass
    def tool(self,label,tip,callback,layout):
        b=QToolButton(); b.setText(label); b.setToolTip(tip); b.clicked.connect(callback); layout.addWidget(b); return b
    def add_shortcut(self,key,callback):
        a=QAction(self); a.setShortcut(QKeySequence(key)); a.triggered.connect(callback); self.addAction(a)
    def make_menu(self):
        m=QMenu(self)
        m.addAction('New tab',self.new_tab,QKeySequence('Ctrl+T')); m.addAction('Duplicate current tab',self.duplicate_tab); m.addSeparator()
        m.addAction('Bookmarks…',self.show_bookmarks); m.addAction('History…',self.show_history); m.addAction('Downloads folder',lambda:os.startfile(str(Path.home()/'Downloads')) if sys.platform=='win32' else self.open_url('file://'+str(Path.home()/'Downloads'))); m.addSeparator()
        m.addAction('Zoom in',lambda:self.change_zoom(10),QKeySequence('Ctrl++')); m.addAction('Zoom out',lambda:self.change_zoom(-10),QKeySequence('Ctrl+-')); m.addAction('Reset zoom',lambda:self.set_zoom(100),QKeySequence('Ctrl+0')); m.addSeparator()
        m.addAction('Settings / customise',self.open_settings); m.addAction('Clear browsing history',self.clear_history); m.addAction('About',self.about); return m
    def apply_cookie_policy(self):
        profile = QWebEngineProfile.defaultProfile()
        policy = (QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
                  if self.settings.get('cookies', True) else QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        profile.setPersistentCookiesPolicy(policy)
    def apply_theme(self):
        c=THEMES.get(self.settings.get('theme'),THEMES['Midnight'])
        #apply the selected theme to the browser chrome.
        self.setStyleSheet(f"QMainWindow,QWidget{{background:{c['bg']};color:{c['text']};}} QTabWidget::pane{{border:1px solid {c['border']};}} QTabBar::tab{{background:{c['panel']};color:{c['text']};padding:9px 15px;border:1px solid {c['border']};}} QTabBar::tab:selected{{background:{c['field']};border-bottom:2px solid {c['accent']};}} QLineEdit{{background:{c['field']};color:{c['text']};border:1px solid {c['border']};border-radius:8px;padding:10px;selection-background-color:{c['accent']};}} QToolButton,QPushButton{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};border-radius:7px;padding:7px 10px;}} QToolButton:hover,QPushButton:hover{{border-color:{c['accent']};}} QMenu{{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};}} QMenu::item{{padding:7px 24px;}} QMenu::item:selected{{background:{c['accent']};}} QStatusBar{{background:{c['panel']};color:{c['muted']};}} QComboBox,QSpinBox{{background:{c['field']};padding:6px;border:1px solid {c['border']};}}")
        self.bookbar.setVisible(self.settings['show_bookmarks_bar'])
    def current_tab(self): return self.tabs.currentWidget()
    def current_view(self): return self.current_tab().view if self.current_tab() else None
    def new_tab(self,url=None):
        tab=BrowserTab(self,url); idx=self.tabs.addTab(tab,'New Tab'); self.tabs.setCurrentIndex(idx); return tab
    def close_tab(self,index):
        if index<0:return
        tab=self.tabs.widget(index); self.tabs.removeTab(index); tab.deleteLater()
        if self.tabs.count()==0:self.new_tab()
    def duplicate_tab(self):
        v=self.current_view()
        if v:self.new_tab(v.url().toString())
    def tab_changed(self,index):
        tab=self.tabs.widget(index)
        if tab and hasattr(tab,'view'): self.address.setText(tab.view.url().toString())
    def update_address(self,tab,url):
        if tab is self.current_tab():self.address.setText(url.toString())
    def update_title(self,tab,title):
        idx=self.tabs.indexOf(tab)
        if idx>=0:self.tabs.setTabText(idx,(title or 'New Tab')[:24])
        if tab is self.current_tab():self.setWindowTitle(f'{title or "New Tab"} — {APP_NAME}')
    def after_load(self,tab,ok):
        if not ok:return
        url=tab.view.url().toString()
        if url.startswith(('http://','https://')):
            self.history.insert(0,{'title':tab.view.title(),'url':url})
            self.history=self.history[:1000]; self.write_json(self.history_file,self.history)
        css=self.settings.get('custom_css','').strip()
        if css.startswith('https://') or css.startswith('http://'):
            js="fetch("+json.dumps(css)+").then(r=>r.text()).then(css=>{let s=document.createElement('style');s.textContent=css;document.head.appendChild(s)}).catch(()=>{});"
            tab.view.page().runJavaScript(js)
    def navigate(self):
        text=self.address.text().strip()
        if not text:return
        if '://' not in text and '.' in text.split('/')[0] and ' ' not in text: url='https://'+text
        elif text.startswith(('http://','https://','file://')):url=text
        else:url=SEARCH.get(self.settings['search_engine'],SEARCH['DuckDuckGo']).format(quote_plus(text))
        self.open_url(url)
    def open_url(self,url):
        if self.current_view():self.current_view().setUrl(QUrl(url))
        else:self.new_tab(url)
    def go_home(self):self.open_url(self.settings['home_page'])
    def set_zoom(self,value):
        self.settings['zoom']=max(25,min(300,value))
        if self.current_view():self.current_view().setZoomFactor(self.settings['zoom']/100)
        save_settings(self.settings); self.statusBar().showMessage(f'Zoom: {self.settings["zoom"]}%',1800)
    def change_zoom(self,delta):
        v=self.current_view(); self.set_zoom(round(v.zoomFactor()*100)+delta if v else 100+delta)
    def add_bookmark(self):
        v=self.current_view()
        if not v:return
        title,url=v.title() or v.url().host(),v.url().toString()
        if any(x.get('url')==url for x in self.bookmarks):self.statusBar().showMessage('Already bookmarked',1800);return
        self.bookmarks.append({'title':title,'url':url}); self.write_json(self.bookmark_file,self.bookmarks); self.refresh_bookmarks_bar(); self.statusBar().showMessage('Bookmark saved',1800)
    def refresh_bookmarks_bar(self):
        while self.bookbar_layout.count():
            item=self.bookbar_layout.takeAt(0); w=item.widget(); w.deleteLater() if w else None
        for item in self.bookmarks[:12]:
            b=QPushButton(item.get('title','Bookmark')[:18]); b.setToolTip(item['url']); b.clicked.connect(lambda checked=False,u=item['url']:self.open_url(u)); self.bookbar_layout.addWidget(b)
        self.bookbar_layout.addStretch(1)
    def show_bookmarks(self):
        d=QDialog(self);d.setWindowTitle('Bookmarks');d.resize(650,400);lay=QVBoxLayout(d);lst=QListWidget()
        for b in self.bookmarks:lst.addItem(f"{b.get('title','Bookmark')}  —  {b['url']}")
        lay.addWidget(lst);row=QHBoxLayout();lay.addLayout(row)
        def open_selected():
            i=lst.currentRow()
            if i>=0:self.open_url(self.bookmarks[i]['url']);d.accept()
        def remove_selected():
            i=lst.currentRow()
            if i>=0:self.bookmarks.pop(i);self.write_json(self.bookmark_file,self.bookmarks);lst.takeItem(i);self.refresh_bookmarks_bar()
        for label,fn in [('Open',open_selected),('Remove',remove_selected),('Close',d.reject)]:b=QPushButton(label);b.clicked.connect(fn);row.addWidget(b)
        d.exec()
    def show_history(self):
        d=QDialog(self);d.setWindowTitle('History');d.resize(720,450);lay=QVBoxLayout(d);lst=QListWidget()
        for h in self.history[:500]:lst.addItem(f"{h.get('title','Page')}  —  {h['url']}")
        lay.addWidget(lst);row=QHBoxLayout();lay.addLayout(row)
        def open_selected():
            i=lst.currentRow()
            if i>=0:self.open_url(self.history[i]['url']);d.accept()
        b=QPushButton('Open selected');b.clicked.connect(open_selected);row.addWidget(b);c=QPushButton('Clear history');c.clicked.connect(lambda:(self.clear_history(),lst.clear()));row.addWidget(c);x=QPushButton('Close');x.clicked.connect(d.reject);row.addWidget(x);d.exec()
    def clear_history(self):
        if QMessageBox.question(self,'Clear history','Delete saved browsing history?')==QMessageBox.StandardButton.Yes:self.history=[];self.write_json(self.history_file,[]);self.statusBar().showMessage('History cleared',1800)
    def open_settings(self):
        d=SettingsDialog(self)
        if d.exec()==QDialog.DialogCode.Accepted:
            self.settings=d.values();save_settings(self.settings);self.apply_cookie_policy();self.apply_theme();self.refresh_bookmarks_bar()
            for i in range(self.tabs.count()):self.tabs.widget(i).apply_settings()
            self.statusBar().showMessage('Settings saved. Some settings apply fully after reloading pages.',3500)
    def toggle_fullscreen(self):self.showNormal() if self.isFullScreen() else self.showFullScreen()
    def about(self):QMessageBox.about(self,APP_NAME,'A highly configurable desktop browser starter. Built with Python, PySide6 and QtWebEngine.\n\nSettings and bookmarks are stored locally in ~/.configurable-browser.\nThis is an early version, not a hardened privacy/security browser.')
    def closeEvent(self,event):
        urls=[]
        if self.settings['restore_tabs']:
            for i in range(self.tabs.count()):
                v=self.tabs.widget(i).view; u=v.url().toString()
                if u and u!='about:blank':urls.append(u)
        self.write_json(self.session_file,urls);save_settings(self.settings);event.accept()

if __name__=='__main__':
    app=QApplication(sys.argv);app.setApplicationName(APP_NAME)
    window=Browser();window.show();sys.exit(app.exec())
