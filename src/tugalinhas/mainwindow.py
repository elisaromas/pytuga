import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore, uic
import pytuga
from tugalinhas import TurtleWidget


VERSION = pytuga.__version__
PYTUGA_FILTER = 'Código fonte em Pytyguês (*.pytg *.py *.py3 *.py2)'


class Tugalinhas(QtWidgets.QMainWindow):
    """
    Main window for Tugalinhas
    """

    def __init__(self):
        super().__init__()
        self._filename = 'turtle-test.pytg'
        base = os.path.split(__file__)[0]
        uic.loadUi(os.path.join(base, 'main.ui'), self)
        self._turtlewidget = TurtleWidget(
                header_text='Tugalinhas %s\n'
                            'Digite `turtlehelp()` para uma lista de comandos'
                            % VERSION)
        self._turtlescene = self._turtlewidget._scene
        self._layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self._layout.addWidget(self._turtlewidget)
        self._layout.setContentsMargins(2, 0, 2, 2)
        self._documentation_view = None
        self._upgrade_task = None
        self.setMinimumSize(800, 600)
        self.updateTitle()
        self.setWindowIcon(_window_icon())


    #
    # File operations
    #
    def openFile(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Abrir arquivo', filter=PYTUGA_FILTER)[0]
        if fname:
            with open(fname) as F:
                data = F.read()
            self._turtlewidget.setText(data)
            self._filename = fname
        self.updateTitle()

    def saveFile(self):
        if self._filename is None:
            self.saveFileAs()
        else:
            with open(self._filename, 'w') as F:
                F.write(self._turtlewidget.text())

    def saveFileAs(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Salvar arquivo', filter=PYTUGA_FILTER)[0]
        if fname:
            with open(fname, 'w') as F:
                F.write(self._turtlewidget.text())
            self._filename = fname
        self.updateTitle()

    def saveImageAs(self):
        formats = QtGui.QImageWriter.supportedImageFormats()
        formats = ['.' + bytes(x).decode() for x in formats]
        fmt_string = ' '.join('*' + ext for ext in formats)

        fname = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Salvar imagem', filter="Imagens (%s)" % fmt_string)[0]

        if fname:
            if os.path.splitext(fname)[1] not in formats:
                QtWidgets.QErrorMessage.showMessage(
                        'Arquivo inválido: %s.\n'
                        'Extensão não reconhecida. Utilize um formato suportado '
                        'como por exemplo ".png".' % fname,
                        'save-image-as-error'
                )
            try:
                self._turtlewidget.saveImage(fname)
            except ValueError:
                QtWidgets.QErrorMessage.showMessage(
                        'Arquivo inválido: %s.\n'
                        'Não foi possível salvar a tela no arquivo escolhido. '
                        'Verifique se o caminho está acessível ou se as '
                        'permissões são corretas.' % fname,
                        'save-image-as-error'
                )

    def newFile(self):
        self._filename = None
        self._turtlewidget.setText('')
        self.updateTitle()

    #
    # View menu
    #
    def zoomIn(self):
        self._turtlewidget.zoomIn()

    def zoomOut(self):
        self._turtlewidget.zoomOut()

    def fontZoomIn(self):
        self._turtlewidget.fontZoomIn()

    def fontZoomOut(self):
        self._turtlewidget.fontZoomOut()

    def fontZoomReset(self):
        self._turtlewidget.fontZoomTo(1)

    def clearScene(self):
        self._turtlescene.clear()

    def toggleEditorTheme(self):
        self._turtlewidget.toggleTheme()

    #
    # help menu
    #
    def openDocumentation(self):
        try:
            from PyQt5 import QtWebKitWidgets
        except ImportError:
            QtWidgets.QMessageBox.critical(
                    self, 'qt5-webkit não está instalado',
                    'Por favor instale o pacote Qt5 Webkit para visualizar '
                    'a documentação. Caso não possa instalar o pacote, vá'
                    'para o site: http://pytuga.readthedocs.org/en/latest/'
            )

        if self._documentation_view is not None:
            self._documentation_view.show()
        else:
            dirname = os.path.dirname(__file__)
            filename = os.path.join(dirname, 'doc', 'html', 'index.html')
            view = QtWebKitWidgets.QWebView()
            view.load(QtCore.QUrl("file://%s" % filename))
            page = view.page()

            window = self._documentation_view = QtWidgets.QWidget()
            window.setWindowTitle('Documentação')
            toolbar = QtWidgets.QToolBar()
            toolbar.addAction(view.pageAction(page.Back))
            toolbar.addAction(view.pageAction(page.Forward))

            layout = QtWidgets.QVBoxLayout(window)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(toolbar)
            layout.addWidget(view)
            window.show()

    def about(self):
        QtWidgets.QMessageBox.about(
                self,
                'Pytuguês',
                'Pytuguês é uma linguagem para o ensino de programação em '
                'português. Aqui aprendemos a programar em português e dentro '
                'de um ambiente gráfico e lúdico.')

    def updateProgram(self):
        import subprocess
        import threading
        try:
            from pip import main as pip_main
            from pip.locations import virtualenv_no_global
        except ImportError:
            return QtWidgets.QErrorMessage(self).showMessage(
                    'Você não possui o comando "pip". Este comando é necessário '
                    'para realizar a atualização do Pytuguês. No Ubuntu, tente '
                    'executar o comando "sudo apt-get install python3-pip" antes '
                    'de tentar fazer a atualização.',
                    'no-pip-error'
            )

        retcode = None
        output = None

        def run_pip():
            nonlocal retcode, output

            # Run pip install pytuga --user -U or some alternative
            args = ['python3', '-m', 'pip', 'install', 'pytuga', '-U']
            if not virtualenv_no_global():
                args.append('--user')
            try:
                output = subprocess.check_output(
                        args,
                        universal_newlines=True,
                        stderr=subprocess.STDOUT,
                        timeout=5,
                )
            except subprocess.CalledProcessError:
                dialog.reject()
            except TimeoutError:
                retcode = 'timeout'
            else:
                if 'Requirement already up-to-date: pytuga' in output:
                    retcode = 'up-to-date'

            dialog.accept()

        # Create dialog and run
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Atualização de versão')
        progress = QtWidgets.QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(0)
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(QtWidgets.QLabel('Buscando atualizações...'))
        layout.addWidget(progress)

        # Run pip and dialog simultaneously
        task = threading.Thread(target=run_pip)
        task.start()
        is_ok = dialog.exec()
        task.join(0.01)
        print('out:', output)

        if not is_ok or retcode == 'timeout':
            QtWidgets.QMessageBox.critical(
                    self, 'Erro',
                    'Houve um problema na atualização. '
                    'Por favor tente novamente mais tarde.\n\n'
                    'Pip retornou a mensagem:\n' + (output or '<vazio>'),
            )
        elif retcode == 'up-to-date':
            QtWidgets.QMessageBox.about(
                    self, 'Nenhuma atualização encontrada',
                    'Seu programa já estava na última versão.')
        else:
            QtWidgets.QMessageBox.about(
                    self, 'Atualizado com sucesso',
                    'Você deve reiniciar este programa agora.')



    #
    # Other commands and utility methods
    #
    def updateTitle(self):
        if self._filename:
            self.setWindowTitle('Tugalinhas (%s)' % self._filename)
        else:
            self.setWindowTitle('Tugalinhas (not saved)')

if not hasattr(Tugalinhas, 'setUnifiedTitleAndToolBarOnMac'):
    def setUnifiedTitleAndToolBarOnMac(*arg, **kwds):
        pass

    Tugalinhas.setUnifiedTitleAndToolBarOnMac = setUnifiedTitleAndToolBarOnMac


#
# Utility function
#
def _window_icon():
    dirpath = os.path.dirname(__file__)
    icon_path = os.path.join(dirpath, 'icon.svg')
    return QtGui.QIcon(icon_path)
