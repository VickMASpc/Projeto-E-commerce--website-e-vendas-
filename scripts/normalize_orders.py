import argparse
import json
from pathlib import Path

import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SALES_DIR = REPO_ROOT / "Sistema de vendas"
if str(SALES_DIR) not in sys.path:
    sys.path.insert(0, str(SALES_DIR))

from domain.order import normalize_order  # noqa: E402


def normalize_orders_file(source: Path, destination: Path) -> int:
    with source.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        orders = data.get("pedidos")
        if not isinstance(orders, list):
            raise ValueError("O JSON deve conter a chave 'pedidos' com uma lista.")
        normalized = {**data, "pedidos": [normalize_order(order) for order in orders]}
    elif isinstance(data, list):
        normalized = [normalize_order(order) for order in data]
    else:
        raise ValueError("Formato não suportado. Use lista de pedidos ou objeto com 'pedidos'.")

    with destination.open("w", encoding="utf-8") as file:
        json.dump(normalized, file, ensure_ascii=False, indent=2)

    return len(normalized if isinstance(normalized, list) else normalized["pedidos"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Normaliza pedidos para o contrato canônico Grand Parfum.")
    parser.add_argument("source", help="Arquivo JSON de origem.")
    parser.add_argument(
        "--output",
        help="Arquivo de saída. Se omitido, cria um arquivo '<origem>.normalized.json'.",
    )
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {source}")

    destination = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source.with_name(f"{source.stem}.normalized{source.suffix}")
    )

    count = normalize_orders_file(source, destination)
    print(f"Pedidos normalizados: {count}")
    print(f"Saída: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
