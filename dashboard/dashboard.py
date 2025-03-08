import streamlit as st
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
from geobr import read_state
from geobr import read_municipality
from shapely.geometry import Point
from matplotlib.lines import Line2D

st.title("Visualisasi Dashboard E-Commerce")
st.subheader("Benevito Kevin Sebastian Hariandja (MC325D5Y0757)")

# Buat tab dan berikan nama
tab1, tab2, tab3 = st.tabs(["Sebaran Customer dan Seller", "Sebaran Price dan Freight Value", "Keakuratan Estimasi Pengiriman"])

# Tab pertanyaan 1
with tab1:

    df1 = pd.read_csv("dashboard/geoloc_customer.csv")
    df2 = pd.read_csv("dashboard/geoloc_seller.csv")

    # Ubah df1 dan df2 ke geodataframe
    geometry1 = [Point(xy) for xy in zip(df1["geolocation_lng"], df1["geolocation_lat"])]
    gdf1 = gpd.GeoDataFrame(df1, geometry=geometry1, crs="EPSG:4674")
    geometry2 = [Point(xy) for xy in zip(df2["geolocation_lng"], df2["geolocation_lat"])]
    gdf2 = gpd.GeoDataFrame(df2, geometry=geometry2, crs="EPSG:4674")

    # Load peta negara brazil
    brazil_states = read_state(year=2018).to_crs("EPSG:4674")
    gdf = gdf1.clip(brazil_states)

    # Gabungkan customer dan seller count
    customer_count = df1["geolocation_state"].value_counts().reset_index()
    customer_count.columns = ["abbrev_state", "customer_count"]

    seller_count = df2["seller_state"].value_counts().reset_index()
    seller_count.columns = ["abbrev_state", "seller_count"]

    # Merge customer dan seller dengan kode kota
    brazil_states = brazil_states.merge(customer_count, on="abbrev_state", how="left")
    brazil_states = brazil_states.merge(seller_count, on="abbrev_state", how="left")
    brazil_states["total_count"] = brazil_states["customer_count"] + brazil_states["seller_count"].fillna(0)

    # Fungsi untuk membuat peta choropleth
    def plot_choropleth(ax, gdf, column, title, cmap):
        brazil_states.plot(ax=ax, color="lightgrey", edgecolor="grey")
        gdf.plot(column=column, 
                 cmap=cmap, 
                 linewidth=0.8, 
                 edgecolor="black", 
                 legend_kwds={"shrink": 0.3},
                 legend=True, 
                 ax=ax)
        ax.set_title(title, fontsize=12)
        ax.set_axis_off()

    # Gambar 1
    st.subheader("Peta Sebaran Customer dan Seller")
    fig, axes = plt.subplots(1, 3, figsize=(12, 10))
    plot_choropleth(axes[0], brazil_states, "total_count", "Sebaran Customers dan Sellers", "Purples")
    plot_choropleth(axes[1], brazil_states, "customer_count", "Sebaran Customers", "Reds")
    plot_choropleth(axes[2], brazil_states, "seller_count", "Sebaran Sellers", "Greens")
    plt.tight_layout()
    st.pyplot(fig)

    # Bagian wilayah kecil
    # Kode kota yang ingin ditampilkan
    code = ["SP", "RJ", "MG", "PR"]

    # Kode kota akan di iterasikan dan peta akan di load untuk semua variable code
    municipalities = {state: read_municipality(code_muni=state, year=2018) for state in code}

    # Data dari geopandas akan di spatial join kan agar visualisasi dapat fokus ke wilayah tersebut saja
    # Hal ini dilakukan untuk geopandas dataframe customer dan seller
    gdfs_c = {state: gpd.sjoin(gdf1, municipalities[state], predicate="intersects") for state in code}
    gdfs_s = {state: gpd.sjoin(gdf2, municipalities[state], predicate="intersects") for state in code}

    st.subheader("Peta Sebaran di Wilayah yang Lebih Kecil")
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    legend = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=8, label='Customers'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Sellers')
    ]

    # Iterasi untuk membuat plot setiap wilayah kecil
    for i, (state, ax) in enumerate(zip(code, axes.flatten())):
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        municipalities[state].plot(ax=ax, color="lightgrey", edgecolor="grey")
        gdfs_c[state].plot(ax=ax, markersize=2, color="red", alpha=0.5)
        gdfs_s[state].plot(ax=ax, markersize=2, color="green", alpha=0.5)
        ax.legend(handles=legend, loc="upper left" if i in [1, 2] else "upper right")
        ax.set_title(f"Peta Sebaran di {state}")

    plt.tight_layout()
    st.pyplot(fig)

    # Bagian pie chart
    def percent(pct, total):
        value = round(pct / 100 * total)
        return f"{pct:.1f}%\n({value})" if pct >= 4 else ""

    # Gabungkan value yang terlalu kecil
    def group(value_counts):
        total = value_counts.sum()
        percentages = value_counts / total * 100
        large_cat = value_counts[percentages >= 4]
        small_cat = value_counts[percentages < 4]
        if not small_cat.empty:
            large_cat["Lainnya"] = small_cat.sum()
        return large_cat

    # Hitung berapa banyak customer dan seller
    count_customers_state = df1["geolocation_state"].value_counts()
    count_sellers_state = df2["seller_state"].value_counts()

    # Panggil fungsi group
    grouped_customers = group(count_customers_state)
    grouped_sellers = group(count_sellers_state)

    st.subheader("Pie Chart Customer dan Seller")
    fig, axes = plt.subplots(1, 2, figsize=(9, 7))
    colors_customers = plt.cm.Reds(range(50, 250, 25))
    colors_sellers = plt.cm.Greens(range(50, 250, 25))

    # Pie chart customer
    axes[0].pie(
        grouped_customers, labels=grouped_customers.index,
        autopct=lambda pct: percent(pct, grouped_customers.sum()),
        colors=colors_customers, startangle=140
    )
    axes[0].set_title("Jumlah Customer pada Setiap Wilayah")

    # Pie chart seller
    axes[1].pie(
        grouped_sellers, labels=grouped_sellers.index,
        autopct=lambda pct: percent(pct, grouped_sellers.sum()),
        colors=colors_sellers, startangle=140
    )
    axes[1].set_title("Jumlah Seller pada Setiap Wilayah")

    plt.tight_layout()
    st.pyplot(fig)



# Tab Pertanyaan 2
with tab2:
    df2 = pd.read_csv("dashboard/price.csv")

    # Scatter Plot
    st.subheader("Scatter Plot: Freight Value dengan Price")
    fig, ax = plt.subplots()
    sns.scatterplot(data=df2, x="freight_value", y="price", ax=ax, marker="^")
    st.pyplot(fig)

    # Heatmap korelasi
    st.subheader("Heatmap Korelasi")
    fig, ax = plt.subplots()
    sns.heatmap(df2.corr(), annot=True, cmap="rocket", ax=ax)
    st.pyplot(fig)

    # Sebaran freight value
    st.subheader("Sebaran Nilai Pengangkutan")
    fig, ax = plt.subplots()
    sns.histplot(df2["freight_value"], kde=True, color="blue", label="Freight Value", ax=ax)
    ax.set_xlim(0, 60)
    st.pyplot(fig)

    # Sebaran price
    st.subheader("Sebaran Harga")
    fig, ax = plt.subplots()
    sns.histplot(df2["price"], kde=True, color="red", label="Price", ax=ax)
    ax.set_xlim(0, 400)
    st.pyplot(fig)

# Tab pertanyaan 3
with tab3:
    df3 = pd.read_csv("dashboard/orders_date.csv")

    # Hitung value pada setiap kategori
    accuracy_count = df3["accuracy_cluster"].value_counts()

    # Tentukan warna bar
    colors = ["green", "orange", "red", "blue", "purple"][:len(accuracy_count)]

    # Buat bar plot
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(accuracy_count.index, accuracy_count.values, color=colors)

    # Nama label x, y, dan judul chart
    st.subheader("Keakuratan Estimasi Pengiriman")
    ax.set_xlabel("Kategori Keakuratan Pengiriman")
    ax.set_ylabel("Jumlah Pesanan")
    ax.set_title("Distribusi Keakuratan Pengiriman")

    # Tentukan sumbu x chart
    ax.set_xticks(range(len(accuracy_count)))
    ax.set_xticklabels(accuracy_count.index, rotation=45)

    # Tambahkan jumlah value di atas bar plot
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, int(height), 
                ha="center", va="bottom", fontsize=12)

    # Buat legend hanya jika jumlah kategori sesuai
    if len(accuracy_count) == 5:
        legend = [
            "Sangat awal (hari <= -3)",
            "Lebih awal (-3 < hari < 0)",
            "Sangat terlambat (hari > 3)", 
            "Sedikit terlambat (0 < hari <= 3)", 
            "Tepat waktu (hari = 0)"
        ]
        ax.legend(bars, legend, title="Kategori")

    st.pyplot(fig)

    # Analisis distribusi pengiriman lebih awal dari 3 hari
    early_delivery_count = df3[df3["delivery_accuracy"] < -3]["delivery_accuracy"].value_counts()

    # Pisahkan data yang >= 500 dengan yang < 500
    main_values = early_delivery_count[early_delivery_count >= 500]
    other_values_sum = early_delivery_count[early_delivery_count < 500].sum()

    # Tambahkan "Lainnya" jika ada kategori kecil
    if other_values_sum > 0:
        main_values = pd.concat([main_values, pd.Series({"Lainnya": other_values_sum})])

    # Buat chart
    fig, ax = plt.subplots(figsize=(13, 5))
    bars = ax.bar(main_values.index.astype(str), main_values.values, color="green")

    # Keterangan
    ax.set_xlabel("Jumlah Hari Lebih Awal (Delivery Accuracy < -3)")
    ax.set_ylabel("Jumlah Pesanan")
    ax.set_title("Distribusi Pengiriman yang Lebih Awal dari 3 Hari")

    # Tambahkan count di atas setiap bar
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height, int(height), 
                ha="center", va="bottom", fontsize=8)

    st.pyplot(fig)


