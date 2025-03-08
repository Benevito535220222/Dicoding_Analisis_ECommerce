## Setup Environment - Anaconda

conda create --name py_dicoding python=3.11.11 <br>
conda activate py_dicoding <br>
pip install -r requirements.txt

## Run steamlit app
streamlit run dashboard/dashboard.py

## Run .ipynb
Klik run all (vscode) <br>
Ctrl + F9 (windows-googlecolab)<br>
Cmd + F9 (macOS-googlecolab) 

***Warning:** untuk re-run code-nya di anjurkan untuk tetap run all. Ada banyak variable yang membutuhkan proses sebelumnya*

## Output loading terus/lama?
Data peta Brazil yang diambil dari library geobr harus di load terlebih dahulu untuk run yang pertama kali agar di cache terlebih dulu. Untuk run setelahnya akan lebih cepat. Harap ditunggu.
