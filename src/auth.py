"""Login a Garmin Connect."""

import os

from garminconnect import Garmin, GarminConnectAuthenticationError

DEFAULT_TOKENSTORE = "~/.garminconnect"


def _prompt_mfa() -> str:
    return input("Codigo MFA de Garmin: ").strip()


def login() -> Garmin:
    """Devuelve un cliente de Garmin ya autenticado.

    Reusa los tokens OAuth cacheados en GARMINTOKENS si existen, asi el MFA
    solo se pide la primera vez. Si el cache esta vencido o no existe, hace
    login completo con email/password y vuelve a guardar los tokens.
    """
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS") or DEFAULT_TOKENSTORE)

    if not email or not password:
        raise SystemExit(
            "Faltan GARMIN_EMAIL / GARMIN_PASSWORD. Copia .env.example a .env "
            "y llena las credenciales."
        )

    client = Garmin(email=email, password=password, prompt_mfa=_prompt_mfa)

    try:
        client.login(tokenstore)
    except (GarminConnectAuthenticationError, FileNotFoundError, OSError) as exc:
        # Cache invalido o inexistente: login limpio y re-guardar tokens.
        print(f"  Login desde cache fallo ({type(exc).__name__}), reintentando...")
        client.login()
        try:
            client.garth.dump(tokenstore)
        except Exception as dump_exc:  # noqa: BLE001 - cachear es best-effort
            print(f"  Aviso: no se pudieron guardar los tokens: {dump_exc}")

    print(f"Autenticado como {email}")
    return client
