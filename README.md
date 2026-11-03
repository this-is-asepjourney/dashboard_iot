# IoT Dashboard — Heat Press Monitoring System

Platform monitoring IoT berbasis Docker untuk memantau mesin heat press secara real-time. Data dari perangkat ESP32/MC dikirim melalui MQTT, diproses oleh Telegraf, disimpan di Prometheus, divisualisasikan di Grafana, dan dikelola melalui Web Dashboard buatan sendiri.

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PERANGKAT IoT                                │
│   [ESP32 / MC Heat Press]  ──── MQTT ──────────────────────────►   │
│         (MAC Address sebagai ID unik)        Broker: 10.109.25.97  │
└──────────────────────────────────────────────────────┬──────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE STACK                            │
│                                                                     │
│   [Telegraf] ──subscribe──► [MQTT Broker]                           │
│       │  Parse JSON, buat tag MAC/MCID                              │
│       │  Expose metrics di :9273                                    │
│       ▼                                                             │
│   [Prometheus] ──scrape──► telegraf:9273                            │
│       │  Simpan time-series metrics                                 │
│       │  Expose di :9090                                            │
│       ▼                                                             │
│   [Grafana] ──query──► Prometheus                                   │
│       │  Dashboard real-time per device (filter by $mac)            │
│       │  Accessible: localhost:3000 & localhost/grafana/            │
│       │                                                             │
│   [FastAPI] ──SQLite──► Device Registry                             │
│       │  CRUD: MAC → Name, Model, Location                          │
│       │  Status: query Prometheus cek device aktif                  │
│       │  Accessible via Nginx: localhost/api/                       │
│       ▼                                                             │
│   [Nginx] ──serve──► Web Dashboard (HTML/CSS/JS)                    │
│       │  / → Web UI                                                 │
│       │  /api/ → FastAPI                                            │
│       └─ /grafana/ → Grafana                                        │
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼ Browser
         ┌──────────────────────┐
         │  Web Dashboard       │
         │  localhost:80        │
         │  - Device Table      │
         │  - Status Online/    │
         │    Offline           │
         │  - Grafana iframe    │
         └──────────────────────┘
```

---

## Hirarki Armada Mesin Heatpress

Sistem kini mendukung struktur hirarki berbasis kategori mesin dan sub-model:

```
🔥 Heatpress (Fleet Root)
  ├── 📟 HPM 55        — Double Station Pneumatic Heat Press (Tekanan 4-8 Bar, Suhu s/d 250°C)
  ├── 📟 AF-450        — Automatic Flatbed Heat Press 450 (Auto-Open Elektromagnetik, Suhu s/d 220°C)
  ├── 📟 APM-LOGO      — Auto Positioning Logo Heat Press (Sensor Laser Guide & Micro-Cylinder)
  └── ⏳ Coming Soon   — Next-Gen Intelligent Heat Press (Multi-Zone PID & Load-Cell Digital)
```

---

## Fitur

### 1. Hirarki Armada (Fleet Hierarchy View)
- **Tampilan Kartu Armada** — Kartu interaktif untuk HPM 55, AF-450, APM-LOGO, dan Coming Soon
- **Spesifikasi Model** — Menampilkan ringkasan teknologi (Pneumatic, Flatbed, Auto-Positioning)
- **Status per Model** — Jumlah unit terdaftar dan indikator online/offline per model
- **Aksi Cepat** — Filter tabel langsung ke model tertentu, monitor live di Grafana, atau tambah unit

### 2. Device Registry & Model Filter Pills
- **Model Pills Bar** — Filter cepat 1-klik di tabel (`Semua Heatpress`, `HPM 55`, `AF-450`, `APM-LOGO`, `Coming Soon`)
- **Preset Model di Modal** — Chip pilihan cepat untuk HPM 55, AF-450, APM-LOGO, dan Coming Soon dengan auto-fill
- **Tambah/Edit/Hapus Device** — Manajemen lengkap MAC Address, MCID, model, lokasi, dan deskripsi
- **Cari Device** — Filter real-time berdasarkan nama, MAC, MCID, lokasi, atau model

### 3. Status Online / Offline
- Setiap device ditampilkan dengan badge **🟢 Online** atau **⚫ Offline**
- Status ditentukan dari data Prometheus: jika device mengirim metric dalam **5 menit terakhir** → Online
- Stat cards di bagian atas menampilkan:
  - **Total Devices** — jumlah device yang terdaftar
  - **Online** — jumlah device aktif (hijau, dengan animasi pulse)
  - **Offline** — jumlah device tidak aktif
  - **Ter-mapping (MCID)** — jumlah device yang sudah dipasangkan dengan MCID
  - **Last Updated** — waktu terakhir polling status
- Status diperbarui otomatis setiap **30 detik**

### 4. Multi-Model Dedicated Dashboards & Universal Monitoring (Grafana)
- **Dashboard Universal (Seluruh Armada)** (`/grafana/d/iot-universal/`):
  - Memonitor seluruh armada lintas model mesin Heatpress (HPM 55, AF-450, APM-LOGO) dalam satu layar komparasi terpadu.
  - Dilengkapi filter cascading: **Filter Model** (`Semua Model`, `HPM 55`, `AF-450`, `APM-LOGO`) dan **Filter Device (MAC)**.
- **Dashboard Dedicated per Model Mesin (Terpisah & Tidak Tercampur)**:
  - 🔥 **Dashboard HPM 55** (`/grafana/d/hpm55-monitoring/`): Khusus model HPM 55 (Double Station Pneumatik, 4-8 Bar, suhu s/d 250°C, platen shuttle dual station). Filter device otomatis hanya menampilkan unit-unit HPM 55.
  - ⚡ **Dashboard AF-450** (`/grafana/d/af450-dashboard/`): Khusus model AF-450 (Automatic Flatbed 450, auto-open elektromagnetik, suhu s/d 220°C, flatbed 40x50cm). Filter device otomatis hanya menampilkan unit-unit AF-450.
  - 🏷️ **Dashboard APM-LOGO** (`/grafana/d/apmlogo-dashboard/`): Khusus model APM-LOGO (Auto Positioning Motion Logo, micro-cylinder pneumatik, laser guide, suhu s/d 230°C, compact platen 15x15cm). Filter device otomatis hanya menampilkan unit-unit APM-LOGO.
- **Dashboard Switcher Tabs**: Pindah antar dashboard dalam 1 klik langsung di Web UI tanpa reload halaman.
- **Device Filter Dinamis**: Pilihan pantau seluruh unit model tersebut (`All Units`) atau fokus ke satu perangkat spesifik.
- **Direct Monitoring Routing**: Dari kartu armada atau tabel Device Manager, klik tombol icon monitor langsung membuka dashboard khusus model device tersebut dengan device otomatis terpilih.

### 5. Statistik & Notifikasi
- Statistik jumlah device dan per model diperbarui otomatis
- Toast notification untuk setiap aksi dan perubahan status device (Online/Offline)
- Animasi pulse pada dot status device yang sedang Online


---

## MQTT Topics & Metric

Telegraf subscribe ke broker MQTT `10.109.25.97:1883` pada topic berikut:

| Topic                | Metric Name     | Keterangan                        |
|----------------------|-----------------|-----------------------------------|
| `+/SysCtrl`          | `sysctrl`       | Status mesin (ON/OFF), versi, IP  |
| `+/Event/Cnt`        | `event_cnt`     | Hitungan event proses             |
| `+/Event/Handling`   | `event_handling`| Event handling proses             |
| `+/Event/Mchn_time`  | `machine_time`  | Waktu operasional mesin           |
| `+/Heatpress`        | `heatpress`     | Data tekanan/suhu heat press      |

**Tag penting:** `MAC`, `IOT_MAC`, `MCID` — digunakan sebagai identifier unik device di Prometheus dan Grafana.

> Metric `sysctrl` adalah acuan utama untuk penentuan status Online/Offline. Device yang mengirim `sysctrl` dalam 5 menit terakhir dianggap **Online**.

---

## Cara Menambahkan Device Baru

1. Buka Web Dashboard: [http://localhost](http://localhost)
2. Klik tombol **+ Add Device**
3. Isi form:
   - **MAC Address** *(wajib)* — format `XX:XX:XX:XX:XX:XX`, contoh: `AA:BB:CC:DD:EE:FF`
   - **Device Name** *(wajib)* — nama deskriptif, contoh: `Heat Press Line 1`
   - **Model** *(opsional)* — tipe hardware, contoh: `ESP32-WROOM`
   - **Location** *(opsional)* — lokasi fisik, contoh: `Factory Floor A`
4. Klik **Save Device**

> MAC Address yang dimasukkan harus sesuai dengan MAC yang dikirim device melalui MQTT (field `MAC` atau `IOT_MAC` dalam JSON payload). Ini adalah kunci penghubung antara data metrik di Prometheus dengan informasi device di dashboard.

---

## Services & Port

| Service    | Container              | Internal Port | Host Port | URL                         |
|------------|------------------------|---------------|-----------|-----------------------------|
| Nginx      | `iot_dashboard_web`    | 80            | **80**    | http://localhost             |
| FastAPI    | `device_mapping_api`   | 8000          | **8000**  | http://localhost/api/        |
| Grafana    | `grafana`              | 3000          | **3000**  | http://localhost:3000        |
| Prometheus | `prometheus`           | 9090          | **9090**  | http://localhost:9090        |
| Telegraf   | `telegraf`             | 9273          | **9273**  | http://localhost:9273/metrics|

---

## Konfigurasi Environment (`.env`)

```env
# Grafana login
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=adminpassword
```

---

## API Endpoints (FastAPI)

Base URL: `http://localhost/api` (via Nginx) atau `http://localhost:8000`

| Method   | Endpoint                           | Deskripsi                                  |
|----------|------------------------------------|--------------------------------------------|
| `GET`    | `/api/devices/hierarchy`           | **Struktur hirarki model Heatpress & unit**|
| `GET`    | `/api/devices/`                    | Ambil semua device (filter: category, model) |
| `POST`   | `/api/devices/`                    | Tambah device baru                         |
| `GET`    | `/api/devices/{mac}`               | Ambil info satu device                     |
| `PUT`    | `/api/devices/{mac}`               | Update info device (nama, model, lokasi)   |
| `DELETE` | `/api/devices/{mac}`               | Hapus device                               |
| `GET`    | `/api/devices/statuses`            | **Status Online/Offline semua device**     |
| `GET`    | `/api/devices/{mac}/status`        | Status Online/Offline satu device          |
| `GET`    | `/api/devices/{mac}/last-seen`     | Waktu terakhir device mengirim data        |

Dokumentasi interaktif: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Struktur Direktori

```
dashboard_iot/
├── docker-compose.yml          # Definisi semua services
├── .env                        # Konfigurasi credentials
│
├── web/                        # Web Dashboard (Nginx + Static)
│   ├── index.html              # UI utama
│   ├── app.js                  # Logic JS (fetch, render, polling)
│   ├── style.css               # Styling (glassmorphism, dark mode)
│   └── nginx.conf              # Konfigurasi reverse proxy Nginx
│
├── api/                        # Device Mapping API (FastAPI + SQLite)
│   ├── main.py                 # Endpoints + status via Prometheus
│   ├── models.py               # SQLAlchemy model (Device table)
│   ├── schemas.py              # Pydantic schemas
│   ├── crud.py                 # Database operations
│   ├── database.py             # SQLite connection
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Build image FastAPI
│   └── data/                   # SQLite database file (persisted)
│       └── devices.db
│
├── telegraf/
│   └── telegraf.conf           # MQTT subscribe + Prometheus export config
│
├── prometheus/                 # Prometheus scrape config
│
└── grafana/                    # Grafana provisioning
    ├── provisioning/           # Datasource & dashboard config otomatis
    └── dashboards/             # JSON dashboard definitions
```

---

## Cara Menjalankan

```bash
# Clone repo & masuk direktori
cd dashboard_iot

# Start semua service (pertama kali, atau setelah ubah Dockerfile)
docker compose up -d --build

# Start tanpa build ulang
docker compose up -d

# Lihat log semua service
docker compose logs -f

# Lihat log service tertentu
docker compose logs -f api

# Stop semua service
docker compose down
```

### Rebuild setelah perubahan kode:

| Komponen diubah          | Perintah rebuild                          |
|--------------------------|-------------------------------------------|
| `api/` (Python/Backend)  | `docker compose up -d --build api`        |
| `web/` (HTML/JS/CSS)     | Langsung refresh browser (file di-mount)  |
| `docker-compose.yml`     | `docker compose up -d`                    |
| `telegraf/telegraf.conf` | `docker compose restart telegraf`         |

---

## Flow Data Lengkap

```
1. [ESP32/MC]
   └─ Kirim JSON via MQTT ke topic: {DeviceID}/SysCtrl
      Contoh payload:
      {
        "MAC": "AA:BB:CC:DD:EE:FF",
        "IOT_MAC": "AA:BB:CC:DD:EE:FF",
        "MCID": "MC001",
        "STS": "ON",
        "VER": "1.2.3",
        "MCIP": "192.168.1.100"
      }

2. [Telegraf]
   └─ Subscribe topic +/SysCtrl
   └─ Parse JSON, simpan MAC sebagai tag Prometheus
   └─ Expose metric: sysctrl{MAC="AA:BB:CC:DD:EE:FF"} di port 9273

3. [Prometheus]
   └─ Scrape telegraf:9273 setiap 5 detik
   └─ Simpan time-series data

4. [Web Dashboard - JS]
   └─ Setiap 30 detik: GET /api/devices/statuses
   └─ FastAPI query Prometheus:
      count by (MAC) (count_over_time(sysctrl[5m]))
   └─ Jika MAC ada di result → Online ✅
   └─ Jika tidak ada → Offline ❌
   └─ Render badge di tabel

5. [Grafana Multi-Model & Universal Dashboard]
   └─ Dashboard Universal: /d/iot-universal/?var-model=...&var-mac=...
   └─ Dashboard HPM 55 Dedicated: /d/hpm55-monitoring/?var-mac=...
   └─ Dashboard AF-450 Dedicated: /d/af450-dashboard/?var-mac=...
   └─ Dashboard APM-LOGO Dedicated: /d/apmlogo-dashboard/?var-mac=...
   └─ Dashboard query Prometheus terfilter sesuai model & device tanpa tercampur
```

---

## Tech Stack

| Layer       | Teknologi                      |
|-------------|--------------------------------|
| Hardware    | ESP32 / Microcontroller        |
| Messaging   | MQTT (Mosquitto broker)        |
| Ingestion   | Telegraf 1.29                  |
| Storage     | Prometheus (time-series)       |
| Visualization | Grafana 10.4.0               |
| Backend API | FastAPI + SQLite (SQLAlchemy)  |
| Web UI      | HTML5 + Vanilla JS + CSS3      |
| Proxy       | Nginx (Alpine)                 |
| Container   | Docker + Docker Compose        |
