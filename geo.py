import pandas as pd
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Definir o caminho para o shapefile e o arquivo Excel
shapefile_path = r"C:\Users\Dárlen\Downloads\municipios-da-paraiba\Municípios da Paraíba\PARAIBA_MUNICIPIOS.shp"
excel_path = r"C:\Users\Dárlen\Downloads\catatreco_1-2024-10-28_15602.xlsx"

# Carregar o shapefile
map_df = gpd.read_file(shapefile_path)

# Verificar o CRS do shapefile e convertê-lo para EPSG:4326 (WGS84), se necessário
if map_df.crs != 'epsg:4326':
    map_df = map_df.to_crs(epsg=4326)

# Ler o arquivo Excel com as coordenadas no novo formato {"x":longitude,"y":latitude}
df = pd.read_excel(excel_path, names=["Coordinates"], header=None)
df['Coordinates'] = df['Coordinates'].str.replace('}', '').str.replace('{', '')
df[['x', 'y']] = df['Coordinates'].str.split(",", expand=True)
df['Longitude'] = df['x'].str.split(":").str[1].astype(float)
df['Latitude'] = df['y'].str.split(":").str[1].astype(float)
df.drop(['Coordinates', 'x', 'y'], axis=1, inplace=True)

# Converter o DataFrame para GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")

# Realizar a junção espacial para identificar a quais bairros os pontos pertencem
joined_df = gpd.sjoin(gdf, map_df, predicate="within", how="left")

# Contar o número de pontos em cada bairro e identificar pontos fora dos bairros
bairro_counts = joined_df['index_right'].value_counts(dropna=False).reset_index()
bairro_counts.columns = ['bairro_numero', 'num_pontos']

# Preparar os labels para a legenda
legend_labels = []
for idx, row in bairro_counts.iterrows():
    if pd.notna(row['bairro_numero']):
        legend_labels.append(f"Setor {int(row['bairro_numero'])} - {int(row['num_pontos'])} comunicações")
    else:
        legend_labels.append(f"Fora da cidade - {int(row['num_pontos'])} comunicações")

# Gerar gráfico e limitar a legenda aos 10 primeiros itens
fig, ax = plt.subplots(figsize=(14, 14))

# Mapa base
map_df.plot(ax=ax, color="#f2f2f2", edgecolor="black", zorder=1)

# Adicionar os pontos de bairro
for _, row in bairro_counts.iterrows():
    if pd.notna(row['bairro_numero']):
        ax.scatter(row['bairro_numero'], row['num_pontos'], label=f"Setor {int(row['bairro_numero'])}", s=100)

# Exibir apenas os 10 primeiros setores na legenda
top_10_rows = list(bairro_counts.iterrows())[:10]  # Converte para lista e pega os 10 primeiros
top_10_labels = [f"{row[1]['bairro_numero']} - {row[1]['num_pontos']} pontos" for row in top_10_rows]
handles = [plt.Line2D([0], [0], marker='o', color='w', label=label, markerfacecolor='blue', markersize=10) for label in top_10_labels]
ax.legend(handles=handles, loc='upper right', fontsize='small', bbox_to_anchor=(1.15, 1))

# Definir o centro do mapa usando a média das coordenadas
map_center = [gdf['Latitude'].mean(), gdf['Longitude'].mean()]

# Criar um mapa interativo com folium
m = folium.Map(location=map_center, zoom_start=12)

# Adicionar bairros ao mapa como camadas de polígonos
for _, row in map_df.iterrows():
    folium.GeoJson(
        row['geometry'],
        name=f"Setor {row.name + 1}"
    ).add_to(m)

# Adicionar pontos ao mapa com base nas coordenadas
for _, row in gdf.iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.6
    ).add_to(m)

# Adicionar a legenda na parte superior direita com informações sobre cada setor
legend_html = '''
<div style="position: fixed;
            top: 10px; right: 10px; width: 150px; height: auto;
            border:2px solid grey; z-index:9999; font-size:12px;
            background-color:white; padding: 10px;">
<h4>Legenda</h4>
''' + "<br>".join(legend_labels) + "</div>"

m.get_root().html.add_child(folium.Element(legend_html))

# Salvar o mapa como um arquivo HTML interativo
m.save("mapa_interativoJP.html")

# # Mostrar o gráfico gerado
# plt.show()
