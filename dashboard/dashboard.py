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

    ### Bagian peta brazil 
    df1 = pd.read_csv("dashboard/geoloc_customer.csv")
    df2 = pd.read_csv("dashboard/geoloc_seller.csv")

    # Fungsi untuk membuat peta choropleth
    def choropleth(ax, gdf, column, title, cmap):
        brazil_state.plot(ax=ax, color="lightgrey", edgecolor="grey")
        gdf.plot(column=column, 
                 cmap=cmap, 
                 linewidth=0.8, 
                 edgecolor="black", 
                 legend_kwds={"shrink": 0.5},
                 legend=True, 
                 ax=ax)
        ax.set_title(title, fontsize=12)
        ax.set_axis_off()

    # Ubah df1 dan df2 ke geodataframe
    geometry1 = [Point(xy) for xy in zip(df1["geolocation_lng"], df1["geolocation_lat"])]
    gdf1 = gpd.GeoDataFrame(df1, geometry=geometry1, crs="EPSG:4674")
    geometry2 = [Point(xy) for xy in zip(df2["geolocation_lng"], df2["geolocation_lat"])]
    gdf2 = gpd.GeoDataFrame(df2, geometry=geometry2, crs="EPSG:4674")

    # Load peta negara brazil
    brazil_state = read_state(year=2018).to_crs("EPSG:4674")
    gdf = gdf1.clip(brazil_state)

    # Gabungkan customer dan seller count
    customer_count = df1["geolocation_state"].value_counts().reset_index()
    customer_count.columns = ["abbrev_state", "customer_count"]

    seller_count = df2["seller_state"].value_counts().reset_index()
    seller_count.columns = ["abbrev_state", "seller_count"]

    # Merge customer dan seller dengan kode kota
    brazil_state = brazil_state.merge(customer_count, on="abbrev_state", how="left")
    brazil_state = brazil_state.merge(seller_count, on="abbrev_state", how="left")
    brazil_state["total_count"] = brazil_state["customer_count"] + brazil_state["seller_count"].fillna(0)

    ### Peta sebaran Customer + Seller atau salah satu
    st.subheader("Peta Sebaran Customer dan Seller")

    # Pilihan tipe data yang ingin ditampilkan
    option = st.selectbox(
        "Pilih data yang ingin ditampilkan pada peta:",
        ("Customer + Seller", "Customer saja", "Seller saja")
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    if option == "Customer + Seller":
        choropleth(ax, brazil_state, "total_count", "Sebaran Customers dan Sellers", "Purples")
    elif option == "Customer saja":
        choropleth(ax, brazil_state, "customer_count", "Sebaran Customers", "Reds")
    else:
        choropleth(ax, brazil_state, "seller_count", "Sebaran Sellers", "Greens")

    plt.tight_layout()
    st.pyplot(fig)

    ### Bagian wilayah kecil
    st.subheader("Peta Sebaran di Wilayah Tertentu")

    # Sort semua kode kota dari A-Z
    all_states = sorted(brazil_state["abbrev_state"])

    # Pilih state, default SP
    code = st.selectbox("Pilih wilayah yang ingin ditampilkan:", all_states, index=all_states.index("SP"))

    # Ambil data municipality berdasarkan state yang dipilih
    municipalities = read_municipality(code_muni=code, year=2018).to_crs("EPSG:4674")

    # Spatial join customer dan seller
    gdfs_c = gpd.sjoin(gdf1, municipalities, predicate="intersects", how="inner")
    gdfs_s = gpd.sjoin(gdf2, municipalities, predicate="intersects", how="inner")

    # Cek jika tidak ada data customer/seller
    no_customer = gdfs_c.empty
    no_seller = gdfs_s.empty

    st.markdown(f"Peta Sebaran di Wilayah {code}")
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot municipalities
    municipalities.plot(ax=ax, color="lightgrey", edgecolor="grey")

    # Plot customers dan sellers hanya jika tidak kosong
    if not no_customer:
        gdfs_c.plot(ax=ax, markersize=2, color="red", alpha=0.5, label="Customer")

    if not no_seller:
        gdfs_s.plot(ax=ax, markersize=2, color="green", alpha=0.5, label="Seller")

    # Tambah legend jika ada data
    legend = []
    if not no_customer:
        legend.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=8, label='Customer'))
    if not no_seller:
        legend.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Seller'))

    if legend:
        ax.legend(handles=legend, loc="upper right")

    ax.set_title(f"Peta Sebaran di {code}")
    ax.set_axis_off()

    plt.tight_layout()
    st.pyplot(fig)

    # Tampilkan pesan info jika tidak ada data sama sekali
    if no_customer:
        st.info(f"Tidak ada data customer {code}")
    elif no_seller:
        st.info(f"Tidak ada data seller di {code}")

    ### Bagian pie chart
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
    grouped_customer = group(count_customers_state)
    grouped_seller = group(count_sellers_state)

    st.subheader("Pie Chart Customer dan Seller")
    fig, axes = plt.subplots(1, 2, figsize=(9, 7))
    colors_customer = plt.cm.Reds(range(50, 250, 25))
    colors_seller = plt.cm.Greens(range(50, 250, 25))

    # Pie chart customer
    axes[0].pie(
        grouped_customer, labels=grouped_customer.index,
        autopct=lambda pct: percent(pct, grouped_customer.sum()),
        colors=colors_customer, startangle=140
    )
    axes[0].set_title("Jumlah Customer pada Setiap Wilayah")

    # Pie chart seller
    axes[1].pie(
        grouped_seller, labels=grouped_seller.index,
        autopct=lambda pct: percent(pct, grouped_seller.sum()),
        colors=colors_seller, startangle=140
    )
    axes[1].set_title("Jumlah Seller pada Setiap Wilayah")

    plt.tight_layout()
    st.pyplot(fig)

# Tab Pertanyaan 2
with tab2:

    df2 = pd.read_csv("dashboard/price.csv")

    ### Scatter Plot
    st.subheader("Scatter Plot: Freight Value dengan Price")

    # Radio button untuk memilih bentuk marker pada scatter plot
    marker_option = st.radio(
        "Pilih bentuk marker pada scatter plot:",
        ("Lingkaran", "Segitiga", "Persegi", "x", "Bintang")
    )

    # Mapping pilihan marker ke simbol matplotlib
    marker_dict = {
        "Lingkaran": "o",
        "Segitiga": "^",
        "Persegi": "s",
        "x": "X",
        "Bintang": "*"
    }
    selected = marker_dict[marker_option]

    # Slider untuk menentukan range sumbu X (freight_value)
    freight_min = int(df2["freight_value"].min())
    freight_max = int(df2["freight_value"].max())
    freight_range_scatter = st.slider(
        "Pilih rentang Freight Value (sumbu X):",
        min_value=freight_min,
        max_value=freight_max,
        value=(freight_min, freight_max)
    )

    # Slider untuk menentukan range sumbu Y (price)
    price_min = int(df2["price"].min())
    price_max = int(df2["price"].max())
    price_range_scatter = st.slider(
        "Pilih rentang Price (sumbu Y):",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max)
    )

    # Hitung padding supaya titik tidak terlalu dekat dengan sumbu
    padding = 0.05
    x_min, x_max = freight_range_scatter
    y_min, y_max = price_range_scatter
    x_padding = (x_max - x_min) * padding
    y_padding = (y_max - y_min) * padding
    fix_x_min = x_min - x_padding
    fix_x_max = x_max + x_padding
    fix_y_min = y_min - y_padding
    fix_y_max = y_max + y_padding

    fig, ax = plt.subplots()
    sns.scatterplot(
        data=df2,
        x="freight_value",
        y="price",
        ax=ax,
        marker=selected
    )

    ax.set_xlim(fix_x_min, fix_x_max)
    ax.set_ylim(fix_y_min, fix_y_max)

    st.pyplot(fig)

    ### Heatmap korelasi
    st.subheader("Heatmap Korelasi")

    fig, ax = plt.subplots()
    sns.heatmap(df2.corr(), annot=True, cmap="rocket", ax=ax)
    st.pyplot(fig)

    ### Sebaran freight value
    st.subheader("Sebaran Nilai Pengangkutan")

    # Slider untuk menentukan rentang nilai freight_value yang ditampilkan pada histogram
    freight_hist = st.slider(
        "Pilih rentang Freight Value untuk histogram:",
        min_value=freight_min,
        max_value=freight_max,
        value=(freight_min, 60)
    )

    # Filter data sesuai dengan range yang dipilih
    filtered_freight = df2[
        (df2["freight_value"] >= freight_hist[0]) &
        (df2["freight_value"] <= freight_hist[1])
    ]

    fig, ax = plt.subplots()
    sns.histplot(filtered_freight["freight_value"], kde=True, color="blue", label="Freight Value", ax=ax)
    ax.set_xlim(freight_hist[0], freight_hist[1])
    st.pyplot(fig)

    ### Sebaran price
    st.subheader("Sebaran Harga")

    # Slider untuk menentukan rentang nilai price yang ditampilkan pada histogram
    price_hist = st.slider(
        "Pilih rentang Price untuk histogram:",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, 400)
    )

    # Filter data sesuai dengan range yang dipilih
    filtered_price = df2[
        (df2["price"] >= price_hist[0]) &
        (df2["price"] <= price_hist[1])
    ]

    fig, ax = plt.subplots()
    sns.histplot(filtered_price["price"], kde=True, color="red", label="Price", ax=ax)
    ax.set_xlim(price_hist[0], price_hist[1])
    st.pyplot(fig)


# Tab pertanyaan 3
with tab3:

    ### Bagian bar plot kategori
    df3 = pd.read_csv("dashboard/orders_date.csv")

    # Hitung value pada setiap kategori
    accuracy_count = df3["accuracy_cluster"].value_counts()

    # Tentukan warna bar
    color = ["mediumseagreen", "goldenrod", "indianred", "cornflowerblue", "mediumorchid"][:len(accuracy_count)]

    # Buat bar plot
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(accuracy_count.index, accuracy_count.values, color=color)

    # Nama label x, y, dan judul chart
    st.subheader("Keakuratan Estimasi Pengiriman")
    ax.set_xlabel("Kategori Keakuratan Pengiriman")
    ax.set_ylabel("Jumlah Pesanan")
    ax.set_title("Sebaran Keakuratan Pengiriman")

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

    ### Selectbox untuk memilih jenis sebaran yang ingin ditampilkan
    st.subheader("Sebaran Akurasi Pengiriman")
    pilihan = st.selectbox(
        "Pilih Jenis Sebaran Akurasi Pengiriman",
        ("Sangat Awal (Hari < -3)", 
         "Lebih Awal, Tepat Waktu, dan Terlambat Sedikit (-3 < Hari <= 3)",
         "Sangat Terlambat (Hari > 3)")
    )

    if pilihan == "Sangat Awal (Hari < -3)":

        ### Bagian bar plot sangat awal (hari < -3)
        # Filter data untuk pengiriman lebih awal dari 3 hari
        early_delivery_count = df3[df3["delivery_accuracy"] < -3]["delivery_accuracy"].value_counts().sort_index()

        # Pisahkan data yang >= 500 dan yang < 500
        main_values = early_delivery_count[early_delivery_count >= 500]
        other_values_sum = early_delivery_count[early_delivery_count < 500].sum()

        # Tambahkan kategori "Lainnya" jika ada data kecil
        if other_values_sum > 0:
            main_values = pd.concat([main_values, pd.Series({"Lainnya": other_values_sum})])

        # Warna bar gradasi hijau
        color = ["lightgreen", "limegreen", "green", "forestgreen", "darkgreen"][:len(main_values)]

        # Buat bar plot
        fig, ax = plt.subplots(figsize=(13, 5))
        bars = ax.bar(main_values.index.astype(str), main_values.values, color=color)

        # Nama label x, y, dan judul chart
        st.markdown("Pengiriman Sangat Awal (Hari < -3)")
        ax.set_xlabel("Jumlah Hari Lebih Awal")
        ax.set_ylabel("Jumlah Pesanan")
        ax.set_title("Sebaran Pengiriman Sangat Awal")

        # Tentukan sumbu x chart
        ax.set_xticks(range(len(main_values)))
        ax.set_xticklabels(main_values.index.astype(str), rotation=45)

        # Tambahkan jumlah value di atas bar plot
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height, int(height),
                    ha="center", va="bottom", fontsize=10)

        st.pyplot(fig)

    elif pilihan == "Lebih Awal, Tepat Waktu, dan Terlambat Sedikit (-3 < Hari <= 3)":

        ### Bagian bar plot lebih awal, tepat waktu, dan terlambat sedikit
        # Filter data untuk masing-masing kategori
        early_delivery = df3[(df3["delivery_accuracy"] >= -3) & (df3["delivery_accuracy"] < 0)]
        on_time_delivery = df3[df3["delivery_accuracy"] == 0]
        late_delivery = df3[(df3["delivery_accuracy"] > 0) & (df3["delivery_accuracy"] <= 3)]

        # Hitung value masing-masing kategori
        early_count = early_delivery["delivery_accuracy"].value_counts().sort_index()
        time_count = on_time_delivery["delivery_accuracy"].value_counts().sort_index()
        late_count = late_delivery["delivery_accuracy"].value_counts().sort_index()

        # Gabungkan semua data menjadi satu Series
        combined_counts = pd.concat([early_count, time_count, late_count]).sort_index()

        # Pisahkan data yang >= 500, yang lain dijadikan 'Lainnya'
        main_values = combined_counts[combined_counts >= 500]
        other_values_sum = combined_counts[combined_counts < 500].sum()

        if other_values_sum > 0:
            main_values = pd.concat([main_values, pd.Series({"Lainnya": other_values_sum})])

        # Definisikan gradien warna untuk setiap kategori
        color_early = ['peachpuff', 'moccasin', 'goldenrod', 'orange', 'darkorange']
        color_late = ['lightblue', 'deepskyblue', 'dodgerblue', 'blue', 'navy']
        color_time = 'purple'

        # Generate warna untuk tiap bar berdasarkan kategori + gradien
        color = []
        early_idx = sorted([idx for idx in main_values.index if isinstance(idx, (int, float)) and idx < 0])
        late_idx = sorted([idx for idx in main_values.index if isinstance(idx, (int, float)) and idx > 0])

        # Buat mapping warna gradien untuk 'early' dan 'late'
        for idx in main_values.index:
            if idx == "Lainnya":
                color.append("grey")
            elif idx in early_idx:
                i = early_idx.index(idx)
                color.append(color_early[i % len(color_early)])
            elif idx == 0:
                color.append(color_time)
            elif idx in late_idx:
                i = late_idx.index(idx)
                color.append(color_late[i % len(color_late)])

        # Buat bar plot
        fig, ax = plt.subplots(figsize=(13, 5))
        bars = ax.bar(main_values.index.astype(str), main_values.values, color=color)

        # Nama label x, y, dan judul chart
        st.markdown("Pengiriman Lebih Awal, Tepat Waktu, dan Terlambat Sedikit")
        ax.set_xlabel("Jumlah Hari Pengiriman")
        ax.set_ylabel("Jumlah Pesanan")
        ax.set_title("Sebaran Pengiriman (-3 < Hari <= 3)")

        # Tentukan sumbu x chart
        ax.set_xticks(range(len(main_values)))
        ax.set_xticklabels(main_values.index.astype(str), rotation=45)

        # Tambahkan jumlah value di atas bar plot
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, int(height),
                    ha="center", va="bottom", fontsize=10)

        # Buat legend custom
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=color_early[-1], label='Lebih Awal (-3 < Hari < 0)'),
            Patch(facecolor=color_time, label='Tepat Waktu (Hari = 0)'),
            Patch(facecolor=color_late[-1], label='Terlambat Sedikit (0 < Hari <= 3)'),
            Patch(facecolor='grey', label='Lainnya')
        ]
        ax.legend(handles=legend_elements, title="Kategori")

        st.pyplot(fig)

    elif pilihan == "Sangat Terlambat (Hari > 3)":

        ### Bagian bar plot sangat terlambat (hari > 3)
        # Filter data untuk keterlambatan lebih dari 3 hari
        accuracy_count = df3[df3["delivery_accuracy"] > 3]

        # Hitung value pada setiap hari keterlambatan
        very_late_count = accuracy_count["delivery_accuracy"].value_counts().sort_index()

        # Pisahkan data yang >= 10 dan yang < 10
        main_values = very_late_count[very_late_count >= 10]
        small_values_sum = very_late_count[very_late_count < 10].sum()

        # Tambahkan kategori "Lainnya" jika ada data kecil
        if small_values_sum > 0:
            main_values = pd.concat([main_values, pd.Series({"Lainnya": small_values_sum})])

        # Tentukan warna bar (pakai gradasi merah)
        colors = ["lightcoral", "indianred", "red", "firebrick", "darkred"][:len(main_values)]

        # Buat bar plot
        fig, ax = plt.subplots(figsize=(13, 5))
        bars = ax.bar(main_values.index.astype(str), main_values.values, color=colors)

        # Nama label x, y, dan judul chart
        st.markdown("Pengiriman Sangat Terlambat (Hari > 3)")
        ax.set_xlabel("Jumlah Hari Keterlambatan")
        ax.set_ylabel("Jumlah Pesanan")
        ax.set_title("Sebaran Pengiriman Sangat Terlambat")

        # Tentukan sumbu x chart
        ax.set_xticks(range(len(main_values)))
        ax.set_xticklabels(main_values.index.astype(str), rotation=45)

        # Tambahkan jumlah value di atas bar plot
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, int(height), 
                    ha="center", va="bottom", fontsize=10)

        st.pyplot(fig)
