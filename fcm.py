import argparse
import json
from pathlib import Path

import google.auth.transport.requests
from google.oauth2 import service_account
import requests

SERVICE_ACCOUNT_FILE = "identix-admin-sdk.json"
PROJECT_ID = "identix-6baf6"
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


def get_access_token(service_account_file: str) -> str:
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=SCOPES,
    )
    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)
    return credentials.token


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Kirim test message ke Firebase Cloud Messaging HTTP v1 API."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--device-token", help="FCM registration token dari device target.")
    target.add_argument("--topic", help="Topic FCM target, tanpa prefix /topics/.")

    parser.add_argument("--title", default="FCM Test", help="Judul notifikasi.")
    parser.add_argument("--body", default="Pesan test dari script Python.", help="Isi notifikasi.")
    parser.add_argument(
        "--sound",
        default="default",
        help="Nama sound notifikasi untuk Android dan iOS. Default: default",
    )
    parser.add_argument(
        "--android-channel-id",
        help="Android notification channel id jika app mewajibkan channel tertentu.",
    )
    parser.add_argument(
        "--data",
        default="{}",
        help='Payload data JSON string, contoh: \'{"type":"socket_test","event":"ping"}\'',
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validasi request ke FCM tanpa mengirim ke device.",
    )
    parser.add_argument(
        "--service-account",
        default=SERVICE_ACCOUNT_FILE,
        help="Path file service account JSON.",
    )
    parser.add_argument(
        "--project-id",
        default=PROJECT_ID,
        help="Firebase project id.",
    )
    return parser.parse_args()


def build_message(args: argparse.Namespace) -> dict:
    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Payload --data bukan JSON valid: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Payload --data harus object JSON, misalnya '{\"event\":\"ping\"}'.")

    # FCM data payload wajib berupa string ke string.
    data = {str(key): str(value) for key, value in data.items()}

    android_notification = {
        "sound": args.sound,
    }
    if args.android_channel_id:
        android_notification["channel_id"] = args.android_channel_id

    message = {
        "notification": {
            "title": args.title,
            "body": args.body,
        },
        "data": data,
        "android": {
            "priority": "high",
            "notification": android_notification,
        },
        "apns": {
            "headers": {
                "apns-priority": "10",
                "apns-push-type": "alert",
            },
            "payload": {
                "aps": {
                    "sound": args.sound,
                }
            },
        },
    }

    if args.device_token:
        message["token"] = args.device_token
    else:
        message["topic"] = args.topic

    return message


def send_message(access_token: str, project_id: str, message: dict, validate_only: bool) -> requests.Response:
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {
        "validate_only": validate_only,
        "message": message,
    }
    return requests.post(url, headers=headers, json=payload, timeout=30)


def main() -> None:
    args = parse_args()

    if not Path(args.service_account).exists():
        raise SystemExit(f"File service account tidak ditemukan: {args.service_account}")

    access_token = get_access_token(args.service_account)
    message = build_message(args)
    response = send_message(
        access_token=access_token,
        project_id=args.project_id,
        message=message,
        validate_only=args.validate_only,
    )

    print("HTTP Status:", response.status_code)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    print(json.dumps(body, indent=2, ensure_ascii=False) if isinstance(body, dict) else body)

    response.raise_for_status()


if __name__ == "__main__":
    main()
