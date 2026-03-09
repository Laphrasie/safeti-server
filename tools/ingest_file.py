#!/usr/bin/env python3
"""
Outil d'ingestion de fichiers JSON gateway vers l'API gas-monitor.

Usage:
    python tools/ingest_file.py data/20260217_17_29_00
    python tools/ingest_file.py data/20260217_17_29_00 --url http://localhost:8000 --api-key mykey
"""
import argparse
import json
import sys
import requests


def main():
    parser = argparse.ArgumentParser(
        description="Envoie un fichier JSON gateway vers l'endpoint /gateway/ingest-file."
    )
    parser.add_argument("file", help="Chemin vers le fichier JSON à envoyer")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL de base de l'API (défaut: http://localhost:8000)",
    )
    parser.add_argument(
        "--api-key",
        default="gateway-api-key-change-in-production",
        help="Clé API gateway (header X-Api-Key)",
    )
    args = parser.parse_args()

    # Load JSON file
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        print(f"Erreur : fichier introuvable : {args.file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Erreur : JSON invalide dans {args.file} : {e}", file=sys.stderr)
        sys.exit(1)

    endpoint = f"{args.url.rstrip('/')}/gateway/ingest-file"
    print(f"Envoi de {args.file} vers {endpoint} ...")

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"X-Api-Key": args.api_key, "Content-Type": "application/json"},
            timeout=30,
        )
    except requests.ConnectionError:
        print(f"Erreur : impossible de se connecter à {args.url}", file=sys.stderr)
        sys.exit(1)

    if response.ok:
        result = response.json()
        print(f"Succès ({response.status_code})")
        print(f"  Mesures créées  : {result.get('measurements_created', '?')}")
        print(f"  Logs créés      : {result.get('logs_created', '?')}")
        skipped = result.get("skipped_devices", [])
        if skipped:
            print(f"  Devices ignorés (user_uid inconnu) : {skipped}")
    else:
        print(f"Erreur HTTP {response.status_code} : {response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
