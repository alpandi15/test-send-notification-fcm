# Firebase FCM Test

Script ini dipakai untuk test kirim message ke Firebase Cloud Messaging (FCM) lewat HTTP v1 API menggunakan service account.

Catatan: FCM bukan socket/websocket. Kalau ingin simulasi event socket, kirim event itu di `data payload`, lalu handle di aplikasi client.

Script ini sudah menambahkan payload khusus Android dan iOS supaya notifikasi lebih konsisten muncul sebagai notif device:

- Android: `priority=high` dan `sound=default`
- iOS: `apns-priority=10`, `apns-push-type=alert`, dan `aps.sound=default`

## File Penting

- `fcm.py`: script pengirim FCM
- `identix-admin-sdk.json`: service account Firebase
- `requirements.txt`: dependency Python

## Persiapan

Jika virtualenv belum aktif, pakai interpreter dari folder `venv` langsung.

Install dependency:

```bash
./venv/bin/pip install -r requirements.txt
```

## Cek Bantuan Command

```bash
./venv/bin/python fcm.py --help
```

## Contoh Yang Setara Dengan Payload Legacy

Kalau kamu biasa pakai payload seperti ini:

```json
{
  "to": "FCM_DEVICE_TOKEN_KAMU",
  "notification": {
    "title": "Hello",
    "body": "Test notif"
  },
  "data": {
    "custom": "value"
  }
}
```

Di FCM HTTP v1, field `to` tidak dipakai lagi. Gantinya gunakan `token` atau `topic`.

Command yang setara di project ini:

```bash
./venv/bin/python fcm.py \
  --device-token "FCM_DEVICE_TOKEN_KAMU" \
  --title "Hello" \
  --body "Test notif" \
  --data '{"custom":"value"}'
```

Kalau aplikasi Android memakai notification channel tertentu:

```bash
./venv/bin/python fcm.py \
  --device-token "FCM_DEVICE_TOKEN_KAMU" \
  --title "Hello" \
  --body "Test notif" \
  --android-channel-id "high_importance_channel" \
  --data '{"custom":"value"}'
```

## Test Validasi Ke FCM

Mode ini hanya validasi request ke FCM, tidak mengirim ke device.

```bash
./venv/bin/python fcm.py \
  --topic test-topic \
  --title "FCM Validate" \
  --body "cek koneksi" \
  --data '{"type":"socket_test","event":"ping"}' \
  --validate-only
```

Kalau sukses, hasilnya biasanya seperti ini:

```json
{
  "name": "projects/PROJECT_ID/messages/..."
}
```

## Kirim Ke Device Token

Ganti `FCM_DEVICE_TOKEN_KAMU` dengan token dari device target.

```bash
./venv/bin/python fcm.py \
  --device-token "FCM_DEVICE_TOKEN_KAMU" \
  --title "Socket Test" \
  --body "trigger dari script" \
  --sound "default" \
  --data '{"type":"socket_test","event":"ping","room_id":"123"}'
```

## Kirim Ke Topic

Pastikan aplikasi client sudah subscribe ke topic yang sama.

```bash
./venv/bin/python fcm.py \
  --topic test-topic \
  --title "Socket Test" \
  --body "broadcast test" \
  --sound "default" \
  --data '{"type":"socket_test","event":"ping"}'
```

## Payload Yang Dikirim Oleh Script

Kalau kamu jalankan:

```bash
./venv/bin/python fcm.py \
  --device-token "FCM_DEVICE_TOKEN_KAMU" \
  --title "Hello" \
  --body "Test notif" \
  --data '{"custom":"value"}'
```

Maka bentuk payload FCM HTTP v1 yang dikirim secara konsep adalah seperti ini:

```json
{
  "message": {
    "token": "FCM_DEVICE_TOKEN_KAMU",
    "notification": {
      "title": "Hello",
      "body": "Test notif"
    },
    "data": {
      "custom": "value"
    },
    "android": {
      "priority": "high",
      "notification": {
        "sound": "default"
      }
    },
    "apns": {
      "headers": {
        "apns-priority": "10",
        "apns-push-type": "alert"
      },
      "payload": {
        "aps": {
          "sound": "default"
        }
      }
    }
  }
}
```

Dengan format ini, Android dan iOS punya hint yang lebih jelas untuk menampilkan alert notification.

## Format Payload Data

FCM `data payload` harus berbentuk object JSON.

Contoh:

```json
{
  "type": "socket_test",
  "event": "ping",
  "room_id": "123"
}
```

Di script ini semua value `data` akan dikonversi jadi string karena memang itu format yang diharapkan FCM.

## Cara Ganti Kredensial Untuk Project Lain

Ada 2 cara.

### Cara 1: Pakai Argumen CLI

Ini cara paling aman karena tidak perlu edit file Python.

1. Simpan service account project lain, misalnya `project-b-admin.json`
2. Jalankan script dengan `--service-account` dan `--project-id`

Contoh:

```bash
./venv/bin/python fcm.py \
  --service-account "project-b-admin.json" \
  --project-id "project-b-12345" \
  --topic test-topic \
  --title "Test Project B" \
  --body "kirim dari project lain" \
  --data '{"type":"socket_test","event":"ping"}' \
  --validate-only
```

### Cara 2: Ubah Default Di Script

Kalau project ini memang mau dipakai permanen untuk Firebase lain, ubah constant di file [fcm.py](/Volumes/SSD/Work/SATUPINTU/TISP/TESTING/firebase-fcm-test/fcm.py).

Bagian yang diubah:

```python
SERVICE_ACCOUNT_FILE = "identix-admin-sdk.json"
PROJECT_ID = "identix-6baf6"
```

Ganti menjadi milik project baru, misalnya:

```python
SERVICE_ACCOUNT_FILE = "project-b-admin.json"
PROJECT_ID = "project-b-12345"
```

Lalu jalankan lagi tanpa argumen tambahan:

```bash
./venv/bin/python fcm.py \
  --topic test-topic \
  --title "Test Project Baru" \
  --body "cek default credential" \
  --data '{"type":"socket_test","event":"ping"}' \
  --validate-only
```

## Cara Ambil Nilai Yang Dibutuhkan

### `project_id`

Ambil dari:

- Firebase Console
- file service account JSON, field `project_id`

### `device token`

Ambil dari aplikasi client yang sudah terpasang Firebase Messaging. Token ini biasanya didapat dari SDK FCM di Android, iOS, atau web.

### `android-channel-id`

Hanya dipakai jika aplikasi Android membuat notification channel sendiri. Kalau channel id di app berbeda, notifikasi bisa tidak muncul seperti yang diharapkan.

Contoh channel id yang sering dipakai:

- `default`
- `high_importance_channel`
- `notification_channel`

### `topic`

Nama topic bebas, misalnya:

- `test-topic`
- `chat-room-123`
- `broadcast-all`

Client harus subscribe ke topic tersebut agar menerima message.

## Error Yang Sering Muncul

### `File service account tidak ditemukan`

Penyebab:

- path file JSON salah

Solusi:

- cek nama file
- pakai `--service-account` dengan path yang benar

### `403` atau `401`

Penyebab:

- service account salah
- project id tidak cocok
- API atau permission belum sesuai

Solusi:

- pastikan `project_id` sama dengan project di service account
- gunakan service account dari project Firebase yang benar
- coba jalankan dulu dengan `--validate-only`

### `Requested entity was not found`

Biasanya:

- `device token` sudah tidak valid
- topic salah
- project salah

### Notifikasi tidak muncul di device padahal request sukses

Biasanya:

- permission notifikasi di Android 13+ belum diizinkan
- app iOS belum grant notification permission
- app Android memakai `channel_id` tertentu tapi payload tidak mengirim channel itu
- device token berasal dari project Firebase lain
- app sedang foreground dan SDK client menahan notif untuk di-handle manual

Solusi:

- cek permission notif di device
- pastikan token berasal dari project Firebase yang sama
- kalau Android pakai channel tertentu, kirim `--android-channel-id`
- test dulu saat app background atau terminated

## Contoh Alur Test Cepat

1. Jalankan validasi dulu:

```bash
./venv/bin/python fcm.py \
  --topic test-topic \
  --title "Validate" \
  --body "cek koneksi" \
  --data '{"type":"socket_test","event":"ping"}' \
  --validate-only
```

2. Kalau sukses, kirim ke token device:

```bash
./venv/bin/python fcm.py \
  --device-token "FCM_DEVICE_TOKEN_KAMU" \
  --title "Real Send" \
  --body "sudah delivery" \
  --data '{"type":"socket_test","event":"ping"}'
```

## Keamanan

- Jangan commit service account JSON ke repository publik
- Simpan file kredensial di tempat yang aman
- Untuk project production, lebih baik pakai environment terpisah
