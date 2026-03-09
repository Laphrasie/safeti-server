#!/usr/bin/env python3
"""
Outil de provisionnement d'utilisateurs gas-monitor.

Crée un nouvel utilisateur via l'API en s'authentifiant d'abord
avec les credentials d'un superviseur.

Usage:
    python tools/provision_user.py \\
        --supervisor-email supervisor@example.com \\
        --supervisor-password supervisor123 \\
        --email paul@example.com \\
        --full-name "Paul Lefebvre" \\
        --role wearer \\
        --password secret123 \\
        --user-uid aez321e35az1

Options:
    --url               URL de base de l'API (défaut: http://localhost:8000)
    --supervisor-email  Email du superviseur (pour l'auth)
    --supervisor-password Mot de passe du superviseur
    --email             Email du nouvel utilisateur
    --full-name         Nom complet du nouvel utilisateur
    --role              Rôle : wearer | doctor | supervisor
    --password          Mot de passe du nouvel utilisateur
    --user-uid          UID externe (utilisé par la gateway, ex: "aez321e35az1")
    --supervisor-id     ID entier du superviseur à assigner au wearer (optionnel)
"""
import argparse
import sys
import requests


def authenticate(base_url: str, email: str, password: str) -> str:
    """Returns a Bearer token."""
    resp = requests.post(
        f"{base_url}/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    if not resp.ok:
        print(
            f"Erreur d'authentification ({resp.status_code}) : {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    return resp.json()["access_token"]


def create_user(base_url: str, token: str, payload: dict) -> dict:
    resp = requests.post(
        f"{base_url}/users/",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=10,
    )
    if not resp.ok:
        print(
            f"Erreur lors de la création ({resp.status_code}) : {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    return resp.json()


def main():
    parser = argparse.ArgumentParser(
        description="Provisionne un nouvel utilisateur dans gas-monitor."
    )
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--supervisor-email", required=True)
    parser.add_argument("--supervisor-password", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--role", required=True, choices=["wearer", "doctor", "supervisor"])
    parser.add_argument("--password", required=True)
    parser.add_argument("--user-uid", default=None, help="UID externe gateway")
    parser.add_argument("--supervisor-id", type=int, default=None)
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print(f"Authentification en tant que {args.supervisor_email} ...")
    token = authenticate(base_url, args.supervisor_email, args.supervisor_password)

    payload = {
        "email": args.email,
        "full_name": args.full_name,
        "role": args.role,
        "password": args.password,
    }
    if args.user_uid:
        payload["user_uid"] = args.user_uid
    if args.supervisor_id is not None:
        payload["supervisor_id"] = args.supervisor_id

    print(f"Création de l'utilisateur {args.email} (rôle: {args.role}) ...")
    user = create_user(base_url, token, payload)

    print(f"Utilisateur créé avec succès :")
    print(f"  ID       : {user['id']}")
    print(f"  Email    : {user['email']}")
    print(f"  Nom      : {user['full_name']}")
    print(f"  Rôle     : {user['role']}")
    print(f"  user_uid : {user.get('user_uid') or '(non défini)'}")


if __name__ == "__main__":
    main()
