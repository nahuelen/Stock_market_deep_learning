# -*- coding: utf-8 -*-
"""TP2_LENARDON.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jcFzOkQymVNOkNmdcKiLpsCa9GHyNjXS

##Instalacion de paquetes
"""

pip install ta

pip install mplfinance

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from tensorflow import keras
from pandas_datareader import data as pdr
import yfinance as yf
import plotly.graph_objects as go
from ta.volatility import BollingerBands
from sklearn.metrics import confusion_matrix

"""## GENERO DATASET"""

### obtengo datos
lenovo=yf.download('LNVGY').reset_index()

"""Genero marcadores"""

def signal_compra (precios,min):
    señales_compra = [np.nan] * len(precios)
    for i in range(len(precios) - 5):
        precio_actual = precios[i]
        precio_futuro = precios[i + 5]
        variacion = (precio_futuro - precio_actual) / precio_actual

        if variacion >= 0.05:
            señales_compra[i] = min[i]         # marco low

    return señales_compra

lenovo['Compra']=signal_compra(lenovo['Close'],lenovo['Low'])

def signal_venta (precios,max):
    señales_venta = [np.nan] * len(precios)
    for i in range(len(precios) - 5):
        precio_actual = precios[i]
        precio_futuro = precios[i + 5]
        variacion = (precio_futuro - precio_actual) / precio_actual

        if variacion <= -0.05:
            señales_venta[i] = max[i]      ## marco high

    return señales_venta

lenovo['Venta']=signal_venta(lenovo['Close'],lenovo['High'])

def signal_mantener(Precio,Compra,Venta):
  señales_mantener=[np.nan]* len(Compra)
  for i in range(len(Compra)):
    if pd.isnull(Compra[i])and pd.isnull(Venta[i]):
      señales_mantener[i] = Precio[i]
  return señales_mantener

lenovo['Mantener']=signal_mantener(lenovo['Close'],lenovo['Compra'],lenovo['Venta'])

lenovo.head(-1000)

"""Creo indicadores"""

###normalizo volumen
lenovo['Volume']=(lenovo['Volume']-lenovo['Volume'].min())/(lenovo['Volume'].max()-lenovo['Volume'].min())

###bandas de bollinger
bandas=BollingerBands(close=lenovo['Close'], window=20, window_dev=2)
### las agrego al dataframe
lenovo['bb_upper'] = bandas.bollinger_hband()
lenovo['bb_lower'] = bandas.bollinger_lband()

## genero EMA de 20
from ta.trend import EMAIndicator
ema_indicator = EMAIndicator(close=lenovo['Close'], window=20)
# calculo la EMA20 y agrego al dataframe
lenovo['EMA20'] = ema_indicator.ema_indicator()

## MACD 20
from ta.trend import MACD
macd=MACD(close=lenovo['Close'], window_slow=12,window_fast=26,window_sign=9)
lenovo['macd']=macd.macd()

## RSI estocastico
from ta.momentum import RSIIndicator
rsi=RSIIndicator(close=lenovo['Close'], window= 14)
lenovo['rsi']=rsi.rsi()

## Ickimoku
from ta.trend import IchimokuIndicator
ichimoku=IchimokuIndicator(high=lenovo['High'],low=lenovo['Low'])

lenovo_filtro=lenovo[(lenovo['Date']>'2018-01-01')&(lenovo['Date']<'2020-12-31')]

lenovo_filtro.head(12)

"""###Dataset entrenamiento"""

lenovo_filtro=lenovo_filtro.set_index('Date')

"""Grafico

Genero carpetas de imagenes de Mantener
"""

import zipfile
import os

# Genero la ventana de 30 días
window_size = 30

# Directorio donde se guardarán las imágenes
output_directory = "/content/output_images_mantener"
os.makedirs(output_directory, exist_ok=True)

# Inicializar una lista para almacenar las rutas de las imágenes generadas
image_paths = []

# Inicializar una lista para almacenar las fechas de los gráficos generados
generated_chart_dates = []

# Genero grafico de velas japonesas guardando solamente las que tienen en el ultimo dato valores en mantener
for i in range(len(lenovo_filtro) - window_size + 1):
    start_date = lenovo_filtro.index[i].strftime('%Y-%m-%d')
    end_date = lenovo_filtro.index[i + window_size - 1].strftime('%Y-%m-%d')

    data = lenovo_filtro.iloc[i:i+window_size]  # Datos para el próximo gráfico

    # Verificar si el último valor en la columna "Mantener" no es NaN
    if not np.isnan(data['Mantener'].iloc[-1]):
        indicators = []

        # Agregar marcadores e indicadores que incorpore para analisis
        #if not np.isnan(data['Compra']).all():
        #    indicators.append(mpf.make_addplot(data['Compra'], color='g', type='scatter', markersize=100, marker='^', panel=0))

        #if not np.isnan(data['Venta']).all():
        #    indicators.append(mpf.make_addplot(data['Venta'], type='scatter', markersize=100, color='r', marker='v', panel=0))

        #if not np.isnan(data['Mantener']).all():
        #    indicators.append(mpf.make_addplot(data['Mantener'], type='scatter', markersize=100, color='b', marker='x', panel=0))

        indicators.append(mpf.make_addplot(data['EMA20'], color='y', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_upper'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_lower'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['macd'], color='b', width=1.5, panel=1))
        indicators.append(mpf.make_addplot(data['rsi'], color='y', width=1.5, panel=1))

        # Genero el grafico
        image_path = os.path.join(output_directory, f'{end_date}.png')# El nombre del archivo incluye la fecha de último dato
        mpf.plot(data,
                 type='candle',
                 style='default',
                 addplot=indicators,
                 savefig=image_path)
        generated_chart_dates.append(end_date)
        image_paths.append(image_path)

# Crear un archivo zip y agregar las imágenes
with zipfile.ZipFile('/content/output_images_mantener.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for image_path in image_paths:
        zipf.write(image_path, os.path.basename(image_path))

# Imprimir las fechas de los gráficos generados y ruta de zip
print("Fechas de los gráficos generados:", generated_chart_dates)
print("Archivo ZIP creado con las imágenes: /content/output_images.zip")

"""Genero carpetas de imagenes de Vender



"""

# Genero la ventana de 30 días
window_size = 30

# Directorio donde se guardarán las imágenes
output_directory = "/content/output_images_vender"
os.makedirs(output_directory, exist_ok=True)

# Inicializar una lista para almacenar las rutas de las imágenes generadas
image_paths = []

# Inicializar una lista para almacenar las fechas de los gráficos generados
generated_chart_dates = []
# Genero grafico de velas japonesas guardando solamente las que tienen en el ultimo dato valores en mantener
for i in range(len(lenovo_filtro) - window_size + 1):
    start_date = lenovo_filtro.index[i].strftime('%Y-%m-%d')
    end_date = lenovo_filtro.index[i + window_size - 1].strftime('%Y-%m-%d')

    data = lenovo_filtro.iloc[i:i+window_size]  # Datos para el próximo gráfico

    # Verificar si el último valor en la columna "Vender" no es NaN
    if not np.isnan(data['Venta'].iloc[-1]):
        indicators = []

        # Agregar marcadores e indicadores que incorpore para analisis
        #if not np.isnan(data['Compra']).all():
        #    indicators.append(mpf.make_addplot(data['Compra'], color='g', type='scatter', markersize=100, marker='^', panel=0))

        #if not np.isnan(data['Venta']).all():
        #    indicators.append(mpf.make_addplot(data['Venta'], type='scatter', markersize=100, color='r', marker='v', panel=0))

        #if not np.isnan(data['Mantener']).all():
        #    indicators.append(mpf.make_addplot(data['Mantener'], type='scatter', markersize=100, color='b', marker='x', panel=0))

        indicators.append(mpf.make_addplot(data['EMA20'], color='y', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_upper'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_lower'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['macd'], color='b', width=1.5, panel=1))
        indicators.append(mpf.make_addplot(data['rsi'], color='y', width=1.5, panel=1))

        # Genero el grafico
        image_path = os.path.join(output_directory, f'{end_date}.png')# El nombre del archivo incluye la fecha de último dato
        mpf.plot(data,
                 type='candle',
                 style='default',
                 addplot=indicators,
                 savefig=image_path)
        generated_chart_dates.append(end_date)
        image_paths.append(image_path)

# Crear un archivo zip y agregar las imágenes
with zipfile.ZipFile('/content/output_images_vender.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for image_path in image_paths:
        zipf.write(image_path, os.path.basename(image_path))

# Imprimir las fechas de los gráficos generados y ruta de zip
print("Fechas de los gráficos generados:", generated_chart_dates)
print("Archivo ZIP creado con las imágenes: /content/output_images.zip")

"""Genero carpetas de imagenes de Compra"""

# Genero la ventana de 30 días
window_size = 30

# Directorio donde se guardarán las imágenes
output_directory = "/content/output_images_comprar"
os.makedirs(output_directory, exist_ok=True)

# Inicializar una lista para almacenar las rutas de las imágenes generadas
image_paths = []

# Inicializar una lista para almacenar las fechas de los gráficos generados
generated_chart_dates = []
# Genero grafico de velas japonesas guardando solamente las que tienen en el ultimo dato valores en mantener
for i in range(len(lenovo_filtro) - window_size + 1):
    start_date = lenovo_filtro.index[i].strftime('%Y-%m-%d')
    end_date = lenovo_filtro.index[i + window_size - 1].strftime('%Y-%m-%d')

    data = lenovo_filtro.iloc[i:i+window_size]  # Datos para el próximo gráfico

    # Verificar si el último valor en la columna "Compra" no es NaN
    if not np.isnan(data['Compra'].iloc[-1]):
        indicators = []

        # Agregar marcadores e indicadores que incorpore para analisis
        #if not np.isnan(data['Compra']).all():
        #    indicators.append(mpf.make_addplot(data['Compra'], color='g', type='scatter', markersize=100, marker='^', panel=0))

        #if not np.isnan(data['Venta']).all():
        #    indicators.append(mpf.make_addplot(data['Venta'], type='scatter', markersize=100, color='r', marker='v', panel=0))

        #if not np.isnan(data['Mantener']).all():
        #    indicators.append(mpf.make_addplot(data['Mantener'], type='scatter', markersize=100, color='b', marker='x', panel=0))

        indicators.append(mpf.make_addplot(data['EMA20'], color='y', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_upper'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_lower'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['macd'], color='b', width=1.5, panel=1))
        indicators.append(mpf.make_addplot(data['rsi'], color='y', width=1.5, panel=1))

        # Genero el grafico
        image_path = os.path.join(output_directory, f'{end_date}.png')# El nombre del archivo incluye la fecha de último dato
        mpf.plot(data,
                 type='candle',
                 style='default',
                 addplot=indicators,
                 savefig=image_path)
        generated_chart_dates.append(end_date)
        image_paths.append(image_path)

# Crear un archivo zip y agregar las imágenes
with zipfile.ZipFile('/content/output_images_comprar.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for image_path in image_paths:
        zipf.write(image_path, os.path.basename(image_path))

# Imprimir las fechas de los gráficos generados y ruta de zip
print("Fechas de los gráficos generados:", generated_chart_dates)
print("Archivo ZIP creado con las imágenes: /content/output_images.zip")

pip install rarfile

import rarfile

# Especifica la ruta al archivo RAR
ruta_archivo_rar = "/content/drive/MyDrive/Uba/Maestria datos financieros/Metodos avanzados predictivo/Trabajos practicos/2/acciones.rar"

# Crea un objeto RarFile para abrir el archivo RAR
with rarfile.RarFile(ruta_archivo_rar, 'r') as rar:
    # Lista los archivos dentro del archivo RAR
    archivos_en_rar = rar.namelist()
    print("Archivos en el archivo RAR:", archivos_en_rar)

    # Extrae todos los archivos del RAR a un directorio específico
    ruta_destino = "/content/drive/MyDrive/Uba/Maestria datos financieros/Metodos avanzados predictivo/Trabajos practicos/2"  # Directorio donde deseas guardar los archivos extraídos
    rar.extractall(path=ruta_destino)
    print(f"Archivos extraídos a '{ruta_destino}'")

"""Preprocesamiento"""

import tensorflow as tf

train_datagen=tf.keras.preprocessing.image.ImageDataGenerator()
train_generator= train_datagen.flow_from_directory(
    '/content/drive/MyDrive/Uba/Maestria datos financieros/Metodos avanzados predictivo/Trabajos practicos/2/acciones',
    target_size=(100,100),
    batch_size=128,
    classes=['mantener','vender','comprar'],
)

"""###Dataset validacion"""

lenovo_val=lenovo[(lenovo['Date']>'2021-01-01')&(lenovo['Date']<'2021-06-30')]

lenovo_val=lenovo_val.set_index('Date')

"""Grafico

Genero carpetas de imagenes de Mantener
"""

import zipfile
import os

# Genero la ventana de 30 días
window_size = 30

# Directorio donde se guardarán las imágenes
output_directory = "/content/output_images_mantener_val"
os.makedirs(output_directory, exist_ok=True)

# Inicializar una lista para almacenar las rutas de las imágenes generadas
image_paths = []

# Inicializar una lista para almacenar las fechas de los gráficos generados
generated_chart_dates = []

# Genero grafico de velas japonesas guardando solamente las que tienen en el ultimo dato valores en mantener
for i in range(len(lenovo_val) - window_size + 1):
    start_date = lenovo_val.index[i].strftime('%Y-%m-%d')
    end_date = lenovo_val.index[i + window_size - 1].strftime('%Y-%m-%d')

    data = lenovo_val.iloc[i:i+window_size]  # Datos para el próximo gráfico

    # Verificar si el último valor en la columna "Mantener" no es NaN
    if not np.isnan(data['Mantener'].iloc[-1]):
        indicators = []

        # Agregar marcadores e indicadores que incorpore para analisis
        #if not np.isnan(data['Compra']).all():
        #    indicators.append(mpf.make_addplot(data['Compra'], color='g', type='scatter', markersize=100, marker='^', panel=0))

        #if not np.isnan(data['Venta']).all():
        #    indicators.append(mpf.make_addplot(data['Venta'], type='scatter', markersize=100, color='r', marker='v', panel=0))

        #if not np.isnan(data['Mantener']).all():
        #    indicators.append(mpf.make_addplot(data['Mantener'], type='scatter', markersize=100, color='b', marker='x', panel=0))

        indicators.append(mpf.make_addplot(data['EMA20'], color='y', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_upper'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_lower'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['macd'], color='b', width=1.5, panel=1))
        indicators.append(mpf.make_addplot(data['rsi'], color='y', width=1.5, panel=1))

        # Genero el grafico
        image_path = os.path.join(output_directory, f'{end_date}.png')# El nombre del archivo incluye la fecha de último dato
        mpf.plot(data,
                 type='candle',
                 style='default',
                 addplot=indicators,
                 savefig=image_path)
        generated_chart_dates.append(end_date)
        image_paths.append(image_path)

# Crear un archivo zip y agregar las imágenes
with zipfile.ZipFile('/content/output_images_mantener_val.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for image_path in image_paths:
        zipf.write(image_path, os.path.basename(image_path))

# Imprimir las fechas de los gráficos generados y ruta de zip
print("Fechas de los gráficos generados:", generated_chart_dates)
print("Archivo ZIP creado con las imágenes: /content/output_images_val.zip")

"""Genero carpetas de imagenes de Vender



"""

# Genero la ventana de 30 días
window_size = 30

# Directorio donde se guardarán las imágenes
output_directory = "/content/output_images_vender_val"
os.makedirs(output_directory, exist_ok=True)

# Inicializar una lista para almacenar las rutas de las imágenes generadas
image_paths = []

# Inicializar una lista para almacenar las fechas de los gráficos generados
generated_chart_dates = []
# Genero grafico de velas japonesas guardando solamente las que tienen en el ultimo dato valores en mantener
for i in range(len(lenovo_val) - window_size + 1):
    start_date = lenovo_val.index[i].strftime('%Y-%m-%d')
    end_date = lenovo_val.index[i + window_size - 1].strftime('%Y-%m-%d')

    data = lenovo_val.iloc[i:i+window_size]  # Datos para el próximo gráfico

    # Verificar si el último valor en la columna "Vender" no es NaN
    if not np.isnan(data['Venta'].iloc[-1]):
        indicators = []

        # Agregar marcadores e indicadores que incorpore para analisis
        #if not np.isnan(data['Compra']).all():
        #    indicators.append(mpf.make_addplot(data['Compra'], color='g', type='scatter', markersize=100, marker='^', panel=0))

        #if not np.isnan(data['Venta']).all():
        #    indicators.append(mpf.make_addplot(data['Venta'], type='scatter', markersize=100, color='r', marker='v', panel=0))

        #if not np.isnan(data['Mantener']).all():
        #    indicators.append(mpf.make_addplot(data['Mantener'], type='scatter', markersize=100, color='b', marker='x', panel=0))

        indicators.append(mpf.make_addplot(data['EMA20'], color='y', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_upper'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_lower'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['macd'], color='b', width=1.5, panel=1))
        indicators.append(mpf.make_addplot(data['rsi'], color='y', width=1.5, panel=1))

        # Genero el grafico
        image_path = os.path.join(output_directory, f'{end_date}.png')# El nombre del archivo incluye la fecha de último dato
        mpf.plot(data,
                 type='candle',
                 style='default',
                 addplot=indicators,
                 savefig=image_path)
        generated_chart_dates.append(end_date)
        image_paths.append(image_path)

# Crear un archivo zip y agregar las imágenes
with zipfile.ZipFile('/content/output_images_vender_val.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for image_path in image_paths:
        zipf.write(image_path, os.path.basename(image_path))

# Imprimir las fechas de los gráficos generados y ruta de zip
print("Fechas de los gráficos generados:", generated_chart_dates)
print("Archivo ZIP creado con las imágenes: /content/output_images_val.zip")

"""Genero carpetas de imagenes de Compra"""

# Genero la ventana de 30 días
window_size = 30

# Directorio donde se guardarán las imágenes
output_directory = "/content/output_images_comprar_val"
os.makedirs(output_directory, exist_ok=True)

# Inicializar una lista para almacenar las rutas de las imágenes generadas
image_paths = []

# Inicializar una lista para almacenar las fechas de los gráficos generados
generated_chart_dates = []
# Genero grafico de velas japonesas guardando solamente las que tienen en el ultimo dato valores en mantener
for i in range(len(lenovo_val) - window_size + 1):
    start_date = lenovo_val.index[i].strftime('%Y-%m-%d')
    end_date = lenovo_val.index[i + window_size - 1].strftime('%Y-%m-%d')

    data = lenovo_val.iloc[i:i+window_size]  # Datos para el próximo gráfico

    # Verificar si el último valor en la columna "Compra" no es NaN
    if not np.isnan(data['Compra'].iloc[-1]):
        indicators = []

        # Agregar marcadores e indicadores que incorpore para analisis
        #if not np.isnan(data['Compra']).all():
        #    indicators.append(mpf.make_addplot(data['Compra'], color='g', type='scatter', markersize=100, marker='^', panel=0))

        #if not np.isnan(data['Venta']).all():
        #    indicators.append(mpf.make_addplot(data['Venta'], type='scatter', markersize=100, color='r', marker='v', panel=0))

        #if not np.isnan(data['Mantener']).all():
        #    indicators.append(mpf.make_addplot(data['Mantener'], type='scatter', markersize=100, color='b', marker='x', panel=0))

        indicators.append(mpf.make_addplot(data['EMA20'], color='y', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_upper'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['bb_lower'], color='m', width=1.5))
        indicators.append(mpf.make_addplot(data['macd'], color='b', width=1.5, panel=1))
        indicators.append(mpf.make_addplot(data['rsi'], color='y', width=1.5, panel=1))

        # Genero el grafico
        image_path = os.path.join(output_directory, f'{end_date}.png')# El nombre del archivo incluye la fecha de último dato
        mpf.plot(data,
                 type='candle',
                 style='default',
                 addplot=indicators,
                 savefig=image_path)
        generated_chart_dates.append(end_date)
        image_paths.append(image_path)

# Crear un archivo zip y agregar las imágenes
with zipfile.ZipFile('/content/output_images_comprar_val.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for image_path in image_paths:
        zipf.write(image_path, os.path.basename(image_path))

# Imprimir las fechas de los gráficos generados y ruta de zip
print("Fechas de los gráficos generados:", generated_chart_dates)
print("Archivo ZIP creado con las imágenes: /content/output_images_val.zip")

import rarfile

# Especifica la ruta al archivo RAR
ruta_archivo_rar = "/content/drive/MyDrive/Uba/Maestria datos financieros/Metodos avanzados predictivo/Trabajos practicos/2/acciones_val.rar"

# Crea un objeto RarFile para abrir el archivo RAR
with rarfile.RarFile(ruta_archivo_rar, 'r') as rar:
    # Lista los archivos dentro del archivo RAR
    archivos_en_rar = rar.namelist()
    print("Archivos en el archivo RAR:", archivos_en_rar)

    # Extrae todos los archivos del RAR a un directorio específico
    ruta_destino = "/content/drive/MyDrive/Uba/Maestria datos financieros/Metodos avanzados predictivo/Trabajos practicos/2"  # Directorio donde deseas guardar los archivos extraídos
    rar.extractall(path=ruta_destino)
    print(f"Archivos extraídos a '{ruta_destino}'")

"""Preprocesamiento"""

import tensorflow as tf

train_datagen_val=tf.keras.preprocessing.image.ImageDataGenerator()
train_generator_val= train_datagen_val.flow_from_directory(
    '/content/drive/MyDrive/Uba/Maestria datos financieros/Metodos avanzados predictivo/Trabajos practicos/2/acciones_val',
    target_size=(100,100),
    batch_size=128,
    classes=['mantener','vender','comprar'],
)

"""##MODELADO"""

from tensorflow import keras
model=tf.keras.models.Sequential([
    ###Entrada
    tf.keras.layers.Input(shape=(100,100,3)),
    ###Convoluciones1
    tf.keras.layers.Conv2D(16,(3,3),activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    ###Convoluciones2
    tf.keras.layers.Conv2D(32,(3,3),activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    ###Convoluciones3
    tf.keras.layers.Conv2D(64,(3,3),activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    ###Convoluciones4
    tf.keras.layers.Conv2D(64,(3,3),activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    ###achatamiento
    tf.keras.layers.Flatten(),
    ###capas densas
    tf.keras.layers.Dense(100, activation='relu'),
    ###salida
    tf.keras.layers.Dense(3, activation='softmax')
])

metrics= [
    keras.metrics.AUC(name="AUC"),
    keras.metrics.Precision(name="precision"),
    keras.metrics.Recall(name="recall"),
    keras.metrics.Accuracy(name='accuracy')
    ]
model.compile(loss='categorical_crossentropy', optimizer='adam',metrics=metrics)

history=model.fit(train_generator,batch_size=256, epochs=20,verbose=2)

history=pd.DataFrame(history.history)
history.plot(xlabel="epoch", figsize=(10,6));

"""Validacion"""

pred=model.predict(train_generator_val)

from sklearn.metrics import accuracy_score

# Obtén las etiquetas verdaderas del conjunto de validación
etiquetas_verdaderas = train_generator_val.classes

# Convierte las predicciones en etiquetas predichas
etiquetas_predichas = pred.argmax(axis=1)

# Calcula la precisión
precision = accuracy_score(etiquetas_verdaderas, etiquetas_predichas)
print(f'Precisión: {precision}')

matriz_confusion = confusion_matrix(etiquetas_verdaderas, etiquetas_predichas)
print('Matriz de Confusión:')
print(matriz_confusion)

"""PROFE NO SE COMO ENCUADRAR EL BATCH DE IMAGENES PARA QUE PUEDA VERLO, IGUAL COPIO CODIGO COMO ME CORRIGIO PARA QUE TENGA ACCESO"""

from google.colab import drive
drive.mount('/content/drive')

# Conexión con Drive
!pip install --upgrade --no-cache-dir gdown

# Subir el archivo a drive y elegir compartir como lector. acciones_val.zip
https://drive.google.com/file/d/1I99QP8hYjBGOzA39dOKZx0NeUz_OawIv/view?usp=sharing
# Subir el archivo a drive y elegir compartir como lector. acciones.zip
https://drive.google.com/file/d/1IAKJCY-6Cx19v3mNoSyQcyyapEIyYayY/view?usp=sharing
# Copiar una parte del enlace que está entre // abajo:
!gdown --id 1I99QP8hYjBGOzA39dOKZx0NeUz_OawIv
!gdown --id 1IAKJCY-6Cx19v3mNoSyQcyyapEIyYayY