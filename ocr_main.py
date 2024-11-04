import cv2
import pytesseract
from PIL import ImageGrab, Image
import numpy as np
import tkinter as tk
from tkinter import filedialog
import re
import pandas as pd
import time
import firebase_admin
from firebase_admin import credentials, db

# Configurar la ruta de Tesseract en tu sistema
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Inicializar Firebase
cred = credentials.Certificate("credential.json")  # Reemplaza con la ruta de tu archivo JSON de credenciales
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://hydrometra-3269a-default-rtdb.firebaseio.com/'
})

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pantalla OCR")

        # Configurar el tamaño y la posición inicial de la ventana
        self.root.geometry("400x159+962+7")  # Ancho x Alto + Posición X + Posición Y

        # Mantener la ventana siempre al frente
        self.root.attributes("-topmost", True)

        # Botón para iniciar el escaneo completo de la pantalla
        self.scan_btn = tk.Button(root, text="Escanear Pantalla Completa", command=self.scan_full_screen)
        self.scan_btn.pack(pady=10)

        # Botón para empezar a escanear automáticamente cada 1 segundo
        self.auto_scan_btn = tk.Button(root, text="Empezar a Escanear", command=self.start_auto_scan)
        self.auto_scan_btn.pack(pady=10)

        # Área de texto para mostrar los resultados
        self.text_area = tk.Text(root, wrap='word', height=5, width=40)
        self.text_area.pack(pady=10)

        # Inicializar DataFrame para almacenar los datos
        self.data = pd.DataFrame(columns=["Tiempo", "Voltaje (V)", "Amperios (A)", "Potencia (W)"])
        self.running = False

    def scan_full_screen(self):
        # Captura de toda la pantalla
        img = ImageGrab.grab()
        text = self.extract_text(img)
        voltaje, amperios = self.extract_voltage_current(text)
        potencia = self.calculate_power(voltaje, amperios)
        self.display_text(voltaje, amperios, potencia)
        self.save_data(voltaje, amperios, potencia)
        self.send_to_firebase(voltaje, amperios, potencia)

    def start_auto_scan(self):
        # Iniciar el escaneo automático cada 1 segundo
        self.running = True
        self.auto_scan()

    def auto_scan(self):
        if self.running:
            self.scan_full_screen()
            # Llamar a la función de nuevo después de 1 segundo
            self.root.after(500, self.auto_scan)

    def extract_text(self, img):
        # Convertir la imagen a escala de grises
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        # Utilizar pytesseract para extraer texto
        texto = pytesseract.image_to_string(gray, config='--psm 6')
        return texto

    def extract_voltage_current(self, text):
        # Buscar los valores de voltaje y corriente con expresiones regulares
        pattern = re.search(r'Vv A\s*([\d\.]+)\s+([\d\.]+)', text)
        if pattern:
            voltaje = float(pattern.group(1))  # Valor del voltaje
            amperios = float(pattern.group(2))  # Valor del amperaje que está justo después del voltaje
        else:
            voltaje = 0.0
            amperios = 0.0

        return voltaje, amperios

    def calculate_power(self, voltaje, amperios):
        # Calcular la potencia como voltaje * amperaje
        return voltaje * amperios

    def display_text(self, voltaje, amperios, potencia):
        # Limpiar el área de texto y mostrar los resultados
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, f"Voltaje: {voltaje} V\nAmperios: {amperios} A\nPotencia: {potencia} W\n")

    def save_data(self, voltaje, amperios, potencia):
        # Guardar los datos en el DataFrame
        tiempo = time.strftime("%Y-%m-%d %H:%M:%S")
        new_data = {"Tiempo": tiempo, "Voltaje (V)": voltaje, "Amperios (A)": amperios, "Potencia (W)": potencia}
        self.data = pd.concat([self.data, pd.DataFrame([new_data])], ignore_index=True)

        # Guardar los datos en un archivo Excel
        self.data.to_excel("datos.xlsx", index=False)

    def send_to_firebase(self, voltaje, amperios, potencia):
        # Enviar datos a Firebase Realtime Database
        ref = db.reference('ahora')
        tiempo = time.strftime("%Y-%m-%d %H:%M:%S")
        ref.set({
            "actualvoltage": str(voltaje),
            "actualampere": str(amperios),
            "actualpower": str(potencia),
            "actualtime": tiempo
        })

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
