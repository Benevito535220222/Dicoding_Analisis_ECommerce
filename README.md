Setup Environment - Anaconda

conda create --name py_dicoding python=3.11.11
conda activate py_dicoding
pip install -r requirements.txt

Run steamlit app
streamlit run dashboard/dashboard.py

Cara run .ipynb
Klik run all (vscode) 
Ctrl + F9 (windows-googlecolab)
Cmd + F9 (macOS-googlecolab) 

untuk re-run code-nya di anjurkan untuk tetap run all
ada banyak variable yang membutuhkan proses sebelumnya

Output loading terus/lama?
Data peta Brazil yang diambil dari library geobr harus di load terlebih dahulu untuk run yang pertama kali agar di cache. Untuk run setelahnya akan lebih cepat. Harap ditunggu.