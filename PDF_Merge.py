# Código para Unificar PDF  e editar


import sys
import os
import tempfile
import fitz  # PyMuPDF para manipulação de PDF
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QMessageBox, \
    QInputDialog, QDialog, QLabel, QScrollArea, QSplitter
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter

class PDFMerger(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.edited_pdfs = {}
        self.init_ui()
        self.setWindowIcon(QIcon('rede7.ico'))

    def init_ui(self):
        # Tamanho da tela ajustado
        screen_size = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen_size.width() * 1.00), int(screen_size.height() * 1.00))
        self.setStyleSheet("background-color: #C0C0C0;")

        # Usar QSplitter para dividir a área de pré-visualização e os botões
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        # Área de pré-visualização (50% à esquerda)
        self.preview_area = QScrollArea(self)
        self.preview_area.setWidgetResizable(True)
        self.preview_content = QVBoxLayout()
        self.preview_widget = QWidget()
        self.preview_widget.setLayout(self.preview_content)
        self.preview_area.setWidget(self.preview_widget)
        splitter.addWidget(self.preview_area)

        # Layout para os botões e o logo (50% à direita)
        right_widget = QWidget()
        buttons_layout = QVBoxLayout(right_widget)
        # Criação do layout vertical para os botões
        buttons_vbox = QVBoxLayout()

        # Botão para selecionar arquivos PDF
        self.select_files_button = QPushButton('Selecionar PDFs')
        self.select_files_button.clicked.connect(self.select_pdfs)
        buttons_layout.addWidget(self.select_files_button)

        # Lista para mostrar arquivos PDF selecionados
        self.file_list = QListWidget(self)
        buttons_layout.addWidget(self.file_list)

        # Botões para manipulação dos PDFs
        self.remove_pdf_button = QPushButton('Remover PDF Selecionado')
        self.remove_pdf_button.clicked.connect(self.remove_pdf)
        buttons_layout.addWidget(self.remove_pdf_button)

        self.order_pdfs_button = QPushButton('Organizar PDFs')
        self.order_pdfs_button.clicked.connect(self.order_pdfs)
        self.merge_button = QPushButton('Unir PDFs')
        buttons_layout.addWidget(self.order_pdfs_button)

        self.remove_pages_button = QPushButton('Excluir páginas de um PDF')
        splitter.setStretchFactor(0, 1)  # Pré-visualização (50%)
        self.remove_pages_button.clicked.connect(self.remove_pages)
        buttons_layout.addWidget(self.remove_pages_button)

        self.merge_button.clicked.connect(self.merge_pdfs)
        buttons_layout.addWidget(self.merge_button)

        # Dentro do método init_ui, após adicionar o botão 'Unir PDFs'
        self.clear_button = QPushButton('Limpar', self)
        self.clear_button.clicked.connect(self.clear_all_files)
        buttons_layout.addWidget(self.clear_button)

        # Adicionar logo no final dos botões
        logo_label = QLabel(self)
        # pixmap = QPixmap(r"C:\Users\vinicius.alonso\Projetos em Python\pythonProject1\rede7.png")
        # logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        buttons_layout.addWidget(logo_label)

        # Adicionar layout direito ao splitter e configurar proporções
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 1)  # Botões (50%)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        self.setWindowTitle('Unificar PDFs')
        self.show()

        # Conectar seleção de item à função de pré-visualização
        self.file_list.currentItemChanged.connect(self.show_preview)
        self.set_button_styles()

    # Função que limpa todos os arquivos da lista
    def clear_all_files(self):
        self.pdf_files.clear()  # Limpa a lista de arquivos
        self.edited_pdfs.clear()  # Limpa os PDFs editados armazenados
        self.update_file_list()  # Atualiza a exibição da lista
        self.clear_preview()  # Limpa a pré-visualização caso haja alguma exibida

    def set_button_styles(self):
        button_style = """
            QPushButton {
                background-color: #4682B4;
                color: black;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #00BFFF;
            }
        """
        self.select_files_button.setStyleSheet(button_style)
        self.remove_pdf_button.setStyleSheet(button_style)
        self.order_pdfs_button.setStyleSheet(button_style)
        self.remove_pages_button.setStyleSheet(button_style)
        self.merge_button.setStyleSheet(button_style)
        self.clear_button.setStyleSheet(button_style)

    def select_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecione arquivos PDF", "", "PDF Files (*.pdf)")
        if files:
            self.pdf_files.extend(files)
            self.update_file_list()

    def remove_pdf(self):
        current_item = self.file_list.currentItem()
        if current_item:
            pdf_to_remove = current_item.text().split(' (')[0]
            self.pdf_files = [pdf for pdf in self.pdf_files if pdf != pdf_to_remove]
            self.update_file_list()
            self.clear_preview()

    def update_file_list(self):
        self.file_list.clear()
        for file in self.pdf_files:
            doc = fitz.open(file)
            num_pages = len(doc)
            self.file_list.addItem(f"{file} ({num_pages} páginas)")
            doc.close()

    def show_preview(self):
        selected_pdf = self.file_list.currentItem()
        if selected_pdf:
            pdf_path = selected_pdf.text().split(' (')[0]
            self.preview_pdf(pdf_path)

    def preview_pdf(self, pdf_path):
        self.clear_preview()
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                qimage = self.convert_to_qimage(pix)

                page_label = QLabel(self)
                page_label.setPixmap(
                    QPixmap.fromImage(qimage).scaled(800, 900, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.preview_content.addWidget(page_label)

            doc.close()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível pré-visualizar o PDF: {e}")
            self.clear_preview()

    def clear_preview(self):
        for i in reversed(range(self.preview_content.count())):
            widget = self.preview_content.itemAt(i).widget()
            widget.deleteLater()

    def convert_to_qimage(self, pix):
        mode = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, mode)
        return qimage

    def order_pdfs(self):
        if not self.pdf_files:
            QMessageBox.warning(self, "Erro", "Nenhum arquivo PDF selecionado.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Organizar PDFs")

        # Define o tamanho da janela do diálogo
        dialog.resize(1200, 800)

        layout = QVBoxLayout(dialog)

        list_widget = QListWidget(dialog)
        list_widget.addItems([f"{pdf} (ordem atual)" for pdf in self.pdf_files])
        layout.addWidget(list_widget)

        move_up_button = QPushButton("Mover para cima", dialog)
        move_down_button = QPushButton("Mover para baixo", dialog)
        layout.addWidget(move_up_button)
        layout.addWidget(move_down_button)

        move_up_button.clicked.connect(lambda: self.move_item(list_widget, direction="up"))
        move_down_button.clicked.connect(lambda: self.move_item(list_widget, direction="down"))

        save_button = QPushButton("Salvar ordem", dialog)
        save_button.clicked.connect(lambda: self.save_order(list_widget, dialog))
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def move_item(self, list_widget, direction):
        current_row = list_widget.currentRow()
        if current_row < 0:
            return

        item = list_widget.takeItem(current_row)

        if direction == "up" and current_row > 0:
            list_widget.insertItem(current_row - 1, item)
            list_widget.setCurrentRow(current_row - 1)
        elif direction == "down" and current_row < list_widget.count() - 1:
            list_widget.insertItem(current_row + 1, item)
            list_widget.setCurrentRow(current_row + 1)

    def save_order(self, list_widget, dialog):
        new_order = []
        for i in range(list_widget.count()):
            pdf_name = list_widget.item(i).text().split(" (ordem atual)")[0]
            new_order.append(pdf_name)
        self.pdf_files = new_order
        dialog.accept()
        self.update_file_list()

    def remove_pages(self):
        selected_pdf = self.file_list.currentItem()
        if selected_pdf:
            pdf_path = selected_pdf.text().split(' (')[0]
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)

            pages_to_remove, ok = QInputDialog.getText(self, "Páginas a remover",
                                                       f"O PDF tem {num_pages} páginas. Digite as páginas a serem removidas (ex: 1, 2, 3):")

            if ok and pages_to_remove:
                try:
                    pages_to_remove = [int(page.strip()) - 1 for page in pages_to_remove.split(',')]
                    if any(page < 0 or page >= num_pages for page in pages_to_remove):
                        raise ValueError("Número de página inválido.")
                    writer = PdfWriter()
                    for i in range(num_pages):
                        if i not in pages_to_remove:
                            writer.add_page(reader.pages[i])

                    output_path = os.path.join(tempfile.gettempdir(), f"editado_{os.path.basename(pdf_path)}")
                    with open(output_path, "wb") as output_pdf:
                        writer.write(output_pdf)

                    self.pdf_files[self.pdf_files.index(pdf_path)] = output_path
                    self.update_file_list()
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Não foi possível remover páginas: {e}")

    def merge_pdfs(self):
        if not self.pdf_files:
            QMessageBox.warning(self, "Erro", "Nenhum arquivo PDF selecionado.")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Unificado", "", "PDF Files (*.pdf)")
        if output_file:
            try:
                writer = PdfWriter()
                for pdf_path in self.pdf_files:
                    reader = PdfReader(pdf_path)
                    for page in reader.pages:
                        writer.add_page(page)

                with open(output_file, "wb") as output_pdf:
                    writer.write(output_pdf)
                QMessageBox.information(self, "Sucesso", "PDFs unificados com sucesso.")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível unir os PDFs: {e}")


app = QApplication(sys.argv)
window = PDFMerger()
window.show()
sys.exit(app.exec_())