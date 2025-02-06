from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QLabel, QPushButton, \
    QStatusBar, QWidget, QHBoxLayout, QGridLayout, QMessageBox
from PyQt6.QtGui import QPixmap, QAction, QImage, QFont
from PyQt6.QtCore import QTimer, Qt, QSize, QPoint
from functools import partial
import random
import json
import os


class PuzzlePiece(QLabel):
    def __init__(self, pixmap, id, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.id = id

    def mousePressEvent(self, event):
        self.parent().parent().piece_clicked(self)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.isNewRecord = False
        self.game_active = False
        self.pieces = []
        self.image = None
        self.setWindowTitle("Puzzle")
        self.setFixedSize(1280, 520)

        self.image_name = "Beach"
        self.difficulty = "Easy"
        self.rows = 4
        self.columns = 4

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

        # Plik z najlepszymi czasami
        self.records_file = "records.txt"
        if not os.path.exists(self.records_file):
            with open(self.records_file, 'w') as f:
                json.dump({}, f)

        # Menu
        menubar = self.menuBar()
        images_menu = menubar.addMenu('Images')
        for image_name in ['Beach', 'Tiger', 'Road', 'Car', 'Hogwart', 'Mountains']:
            action = QAction(image_name, self)
            action.triggered.connect(partial(self.image_clicked, image_name))
            images_menu.addAction(action)

        difficulty_menu = menubar.addMenu('Difficulty')
        for difficulty_level in ['Easy', 'Medium', 'Hard']:
            action = QAction(difficulty_level, self)
            action.triggered.connect(partial(self.difficulty_clicked, difficulty_level))
            difficulty_menu.addAction(action)

        records_menu = menubar.addMenu('Records')
        show_records_action = QAction('Show Actual Records', self)
        show_records_action.triggered.connect(self.show_records_clicked)
        records_menu.addAction(show_records_action)

        delete_records_action = QAction('Delete Record Data', self)
        delete_records_action.triggered.connect(self.delete_records_clicked)
        records_menu.addAction(delete_records_action)

        about_menu = menubar.addMenu('About')
        author_info_action = QAction('Author Info', self)
        author_info_action.triggered.connect(self.author_info_clicked)
        about_menu.addAction(author_info_action)

        # Canvas do wyświetlania fragmentów
        self.first_column_canvas = QWidget(self)
        self.first_column_canvas.setGeometry(20, 30, 800, 452)

        # Oryginalny obraz pomocniczny
        self.image_label = QLabel(self)
        self.image_label.setGeometry(840, 10, 544, 306)
        self.image_label.setPixmap(QPixmap('Images/Beach.jpg').scaled(round(self.width() / 3), self.height(),
                                                                      Qt.AspectRatioMode.KeepAspectRatio))

        # Liczba ruchów
        self.moves_label = QLabel('Moves: 0', self)
        self.moves_label.setGeometry(900, 320, 544, 50)
        font = QFont()
        font.setPointSize(20)
        self.moves_label.setFont(font)
        self.moves = 0

        # Timer
        self.timer_label = QLabel('00:00:00', self)
        self.timer_label.setGeometry(1100, 320, 544, 50)
        self.timer_label.setFont(font)

        # Przycisk nowej gry
        self.new_game_button = QPushButton('New Game', self)
        self.new_game_button.setGeometry(875, 400, 350, 50)
        self.new_game_button.setStyleSheet("background-color: lightgray; color: dark;")
        self.new_game_button.clicked.connect(self.new_game_clicked)

        # Zmodyfikowany pasek stanu
        self.status_label = QLabel(self)
        self.status_label.setGeometry(20, 475, 544, 50)
        self.status_message = self.image_name + ' - ' + self.difficulty
        self.status_label.setText(self.status_message)

        self.selected_piece = None

    # Naciśnięcie przycisku New Game
    def new_game_clicked(self):
        self.clean_canvas()
        self.game_active = True
        self.image = QImage(f'Images/{self.image_name}.jpg')
        rows, cols = self.rows, self.columns
        piece_width = self.image.width() // cols
        piece_height = self.image.height() // rows
        for row in range(rows):
            for col in range(cols):
                piece_image = self.image.copy(col * piece_width, row * piece_height, piece_width, piece_height)
                piece_pixmap = QPixmap.fromImage(piece_image).scaled(self.first_column_canvas.width() // cols,
                                                                     self.first_column_canvas.height() // rows,
                                                                     Qt.AspectRatioMode.KeepAspectRatio)
                piece = PuzzlePiece(piece_pixmap, id=row * cols + col, parent=self.first_column_canvas)
                self.pieces.append(piece)
                piece.show()

        random.shuffle(self.pieces)
        for i, piece in enumerate(self.pieces):
            piece.move((i % cols) * (self.first_column_canvas.width() // cols),
                       (i // rows) * (self.first_column_canvas.height() // rows))
        self.first_column_canvas.update()

        # Rozpoczęcie timera, aktualizacja co 10ms
        self.timer.start(10)
        self.elapsed_time = 0

    # Naciśnięcie fragmentu obrazu
    def piece_clicked(self, piece):
        if not self.game_active:
            # Jeżeli puzzle zostały ułożone nie można kliknąć na fragment
            return
        if self.selected_piece is None:
            self.selected_piece = piece
            self.selected_piece.setStyleSheet("border: 3px solid blue;")
        else:
            if self.selected_piece != piece:
                piece1 = self.selected_piece
                piece2 = piece
                piece1_pos = piece1.pos()
                piece2_pos = piece2.pos()
                piece1.move(piece2_pos)
                piece2.move(piece1_pos)
                id1 = self.pieces.index(piece1)
                id2 = self.pieces.index(piece2)
                self.pieces[id1], self.pieces[id2] = self.pieces[id2], self.pieces[id1]

                self.moves += 1
                self.moves_label.setText(f"Moves: {self.moves}")

            self.selected_piece.setStyleSheet("border: none;")
            self.selected_piece = None

            if self.check_solution():
                self.timer.stop()
                self.solved_message_box()

    # Menu Image
    def image_clicked(self, image_name):
        self.image_label.setPixmap(QPixmap(f'Images/{image_name}.jpg').scaled(round(self.width() / 3), self.height(),
                                                                              Qt.AspectRatioMode.KeepAspectRatio))
        self.image_name = image_name
        self.status_label.setText(self.image_name + ' - ' + self.difficulty)
        self.clean_canvas()

    # Menu Difficulty
    def difficulty_clicked(self, difficulty_level):
        difficulties = {
            "Easy": (4, 4),
            "Medium": (6, 6),
            "Hard": (8, 8)
        }

        if difficulty_level in difficulties:
            self.rows, self.columns = difficulties[difficulty_level]
            self.difficulty = difficulty_level
            self.status_label.setText(self.image_name + ' - ' + self.difficulty)
        else:
            print(f"Nieznany poziom trudności: {difficulty_level}")

        self.clean_canvas()

    # Menu Show Records
    def show_records_clicked(self):
        images = ['Beach', 'Tiger', 'Road', 'Car', 'Hogwart', 'Mountains']
        difficulties = ['Easy', 'Medium', 'Hard']

        records_string = ""
        with open(self.records_file, 'r') as f:
            records = json.load(f)
        for image in images:
            for difficulty in difficulties:
                key = f"{image}-{difficulty}"
                if key in records:
                    time, moves = records[key]
                    minutes = time // 60000
                    seconds = (time % 60000) // 1000
                    milliseconds = (time % 1000) // 10
                    records_string += f"{image} - {difficulty}: Best Time: {minutes:02d}:{seconds:02d}:{milliseconds:02d}, Moves: {moves}\n"
                else:
                    records_string += f"{image} - {difficulty}: No record yet\n"
        QMessageBox.information(self, "Records", records_string)

    # Menu Delete Records
    def delete_records_clicked(self):
        with open(self.records_file, 'w') as f:
            f.write("{}")
        QMessageBox.information(self, "Records", "Record data has been cleared.")

    # Menu Author
    def author_info_clicked(self):
        message = f"Created by Kamil Pieczyk"
        QMessageBox.information(self, "Author", message)

    # Czyszczenie Canvasu i reset liczby ruchów i timera
    def clean_canvas(self):
        for piece in self.pieces:
            piece.deleteLater()

        self.pieces.clear()
        self.moves = 0
        self.moves_label.setText("Moves: 0")
        self.timer.stop()
        self.timer_label.setText("00:00:00")
        self.selected_piece = None

    # Update timera
    def update_timer(self):
        self.elapsed_time += 10
        minutes = self.elapsed_time // 60000
        seconds = (self.elapsed_time % 60000) // 1000
        milliseconds = (self.elapsed_time % 1000) // 10
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}:{milliseconds:02d}")

    # Sprawdzenie poprawności ułożenia i nowego rekordu
    def check_solution(self):
        for i, piece in enumerate(self.pieces):
            if piece.id != i:
                return False

        self.game_active = False

        with open(self.records_file, 'r') as f:
            records = json.load(f)
        key = f"{self.image_name}-{self.difficulty}"
        if key not in records or records[key][0] > self.elapsed_time:
            records[key] = (self.elapsed_time, self.moves)
            with open(self.records_file, 'w') as f:
                json.dump(records, f)
            self.isNewRecord = True
        else:
            self.isNewRecord = False
        return True

    # Okno końca gry
    def solved_message_box(self):
        minutes = self.elapsed_time // 60000
        seconds = (self.elapsed_time % 60000) // 1000
        milliseconds = (self.elapsed_time % 1000) // 10
        message = f"Congratulations! You solved the puzzle in {minutes:02d}:{seconds:02d}:{milliseconds:02d} with {self.moves} moves."

        if self.isNewRecord:
            message += "\nNew Best Time!"
        QMessageBox.information(self, "Puzzle Completed", message)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()