import sys
from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QToolBar, QAction, QLineEdit, QTabWidget,
    QFileDialog, QMenu, QComboBox, QMessageBox
)
from urllib.parse import urlparse
import shutil

class DownloadManager(QWebEnginePage):
    def acceptNavigationRequest(self, qurl, _type, isMainFrame):
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            self.browser.download_requested.emit(qurl)
            return False
        return super().acceptNavigationRequest(qurl, _type, isMainFrame)

class Browser(QWebEngineView):
    download_requested = pyqtSignal(QUrl, str)  # Menambahkan sinyal untuk menyimpan path file

    def __init__(self, *args, **kwargs):
        super(Browser, self).__init__(*args, **kwargs)

        profile = QWebEngineProfile.defaultProfile()
        download_manager = profile.downloadRequested.connect(self.on_download_requested)

    def on_download_requested(self, download):
        # Prompt the user to choose the download location
        file_dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = file_dialog.getSaveFileName(self, "Save File", "", "All Files (*);;Text Files (*.txt)", options=options)

        if file_path:
            download.setPath(file_path)
            self.download_requested.emit(download.url())
            download.accept()
            self.show_download_notification(download.url().toString())

    def show_download_notification(self, url):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Download Complete")
        msg_box.setText(f"Downloaded: {url}")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def navigate_to_url(self, url):
        qurl = QUrl(url)
        if qurl.scheme() == "":
            qurl.setScheme("https://")
        self.setUrl(qurl)

class Window(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.navigation_bar = QToolBar('Navigation Toolbar')
        self.addToolBar(self.navigation_bar)

        back_button = QAction("<", self)
        back_button.setStatusTip('Go to the previous page you visited')
        back_button.triggered.connect(self.navigate_back)
        self.navigation_bar.addAction(back_button)

        refresh_button = QAction("↻", self)
        refresh_button.setStatusTip('Refresh this page')
        refresh_button.triggered.connect(self.reload_page)
        self.navigation_bar.addAction(refresh_button)

        next_button = QAction(">", self)
        next_button.setStatusTip('Go to the next page')
        next_button.triggered.connect(self.navigate_forward)
        self.navigation_bar.addAction(next_button)

        home_button = QAction("Home", self)
        home_button.setStatusTip('Go to the home page (Google page)')
        home_button.triggered.connect(self.go_to_home)
        self.navigation_bar.addAction(home_button)

        self.navigation_bar.addSeparator()

        self.new_tab_button = QAction("+", self)
        self.new_tab_button.setStatusTip('Open a new tab')
        self.new_tab_button.triggered.connect(self.create_new_tab)
        self.navigation_bar.addAction(self.new_tab_button)

        self.URLBar = QLineEdit()
        self.URLBar.returnPressed.connect(self.navigate_to_current_tab)
        self.navigation_bar.addWidget(self.URLBar)

        search_button = QAction("Search", self)
        search_button.setStatusTip('Search the web')
        search_button.triggered.connect(self.search_button_clicked)
        self.navigation_bar.addAction(search_button)

        self.search_engine_combo = QComboBox(self)
        self.search_engine_combo.addItems(['Google', 'Bing', 'DuckDuckGo', 'Yahoo'])
        self.navigation_bar.addWidget(self.search_engine_combo)

        go_button = QAction("Go", self)
        go_button.setStatusTip('Go to the selected search engine')
        go_button.triggered.connect(self.go_to_selected_engine)
        self.navigation_bar.addAction(go_button)

        self.addToolBarBreak()

        bookmarks_toolbar = QToolBar('Bookmarks', self)
        self.addToolBar(bookmarks_toolbar)

        bookmarks = [
            ("Facebook", 'Go to Facebook', "https://www.facebook.com"),
            ("Youtube", 'Go to YouTube', "https://www.youtube.com"),
            ("Instagram", 'Go to Instagram', "https://www.instagram.com"),
            ("Twitter", 'Go to Twitter', "https://www.twitter.com")
        ]

        for name, status_tip, url in bookmarks:
            action = QAction(name, self)
            action.setStatusTip(status_tip)
            action.triggered.connect(lambda _, u=url: self.create_tab(u))
            bookmarks_toolbar.addAction(action)

        self.show()

        self.current_browser = QWebEngineView()
        self.current_browser.urlChanged.connect(lambda qurl, browser=self.current_browser:
                                                 self.update_address_bar(qurl, browser))

        self.create_tab('https://www.google.com')

    def download_file(self, url, file_path):
        file_name = QUrl(url).fileName()
        destination_file = file_path + "/" + file_name  # Menggabungkan path dan nama file

        # Pindahkan file yang diunduh ke folder yang diinginkan
        shutil.move(url.toString(), destination_file)
        
    def go_to_home(self):
        self.current_browser.setUrl(QUrl('https://www.google.com/'))

    def navigate_back(self):
        self.current_browser.back()

    def reload_page(self):
        self.current_browser.reload()

    def navigate_forward(self):
        self.current_browser.forward()

    def navigate_to_url(self):
        q = QUrl(self.URLBar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.current_browser.setUrl(q)

    def create_tab(self, url):
        browser = Browser()
        browser.navigate_to_url(url)
        i = self.tabs.addTab(browser, url)
        self.tabs.setCurrentIndex(i)
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))

    def create_new_tab(self):
        self.create_tab('https://www.google.com')

    def close_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def current_tab_changed(self, i):
        self.current_browser = self.tabs.widget(i)
        self.current_browser.urlChanged.connect(lambda qurl, browser=self.current_browser:
                                                self.update_address_bar(qurl, browser))
        qurl = self.current_browser.url()
        self.update_address_bar(qurl, self.current_browser)

    def update_address_bar(self, qurl, browser=None):
        if browser != self.current_browser:
            return
        self.URLBar.setText(qurl.toString())
        self.URLBar.setCursorPosition(0)

    def search_button_clicked(self):
        search_query = self.URLBar.text()
        selected_search_engine = self.search_engine_combo.currentText()

        if not search_query:
            self.go_to_home()
        else:
            search_url = self.get_search_url(search_query, selected_search_engine)
            self.current_browser.setUrl(QUrl(search_url))

    def go_to_selected_engine(self):
        selected_search_engine = self.search_engine_combo.currentText()

        if selected_search_engine == 'Google':
            self.current_browser.setUrl(QUrl('https://www.google.com'))
        elif selected_search_engine == 'Bing':
            self.current_browser.setUrl(QUrl('https://www.bing.com'))
        elif selected_search_engine == 'DuckDuckGo':
            self.current_browser.setUrl(QUrl('https://duckduckgo.com'))
        elif selected_search_engine == 'Yahoo':
            self.current_browser.setUrl(QUrl('https://www.yahoo.com'))

    def navigate_to_current_tab(self):
        current_browser = self.current_browser
        input_text = self.URLBar.text()

        parsed_url = urlparse(input_text)
        if parsed_url.scheme and parsed_url.netloc:
            current_browser.navigate_to_url(input_text)
        else:
            search_url = self.get_search_url(input_text)
            current_browser.navigate_to_url(search_url)

    def get_search_url(self, query, engine=None):
        search_engines = {
            'Google': 'https://www.google.com/search?q={}',
            'Bing': 'https://www.bing.com/search?q={}',
            'DuckDuckGo': 'https://duckduckgo.com/?q={}',
            'Yahoo': 'https://search.yahoo.com/search?p={}',
        }
        selected_engine = engine if engine else self.search_engine_combo.currentText()
        return search_engines.get(selected_engine, 'https://www.google.com').format(query.replace(" ", "+"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName('Web Browser')

    window = Window()
    app.exec_()