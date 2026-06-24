from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from pde_pipeline import build_pde_report, export_pde_excel


def _default_data_file(data_dir: Path, pattern: str) -> Path | None:
    matches = sorted(data_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def parse_args() -> argparse.Namespace:
    project_dir = Path(__file__).resolve().parent
    data_dir = project_dir / "data"

    default_historico = _default_data_file(data_dir, "base_mestre_provis*.xlsx")
    default_base = _default_data_file(data_dir, "base_mestre_tratada*.xlsx")
    default_atual = _default_data_file(data_dir, "Equipamentos Gerenciarme*.csv")
    default_output_dir = project_dir / "outputs" / "pde"

    parser = argparse.ArgumentParser(
        description="Gera base mestre e relatorio de pendencias PDE do GerenciarMe."
    )
    parser.add_argument(
        "--historico",
        nargs="+",
        default=[str(default_historico)] if default_historico else None,
        help="Um ou mais relatorios historicos do GerenciarMe (.xlsx/.csv).",
    )
    parser.add_argument(
        "--atual",
        default=str(default_atual) if default_atual else None,
        help="Relatorio atual do GerenciarMe (.csv/.xlsx).",
    )
    parser.add_argument(
        "--base-mestre",
        default=str(default_base) if default_base else None,
        help="Base mestre tratada. Se omitida, uma base provisoria sera gerada do historico.",
    )
    parser.add_argument(
        "--saida",
        default=None,
        help="Caminho completo do arquivo Excel final. Por padrao usa outputs/pde.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_output_dir),
        help="Diretorio para arquivos gerados quando --saida nao for informado.",
    )
    parser.add_argument(
        "--data-referencia",
        default=None,
        help="Data de referencia no formato DD/MM/AAAA. Se omitida, usa Data(para) do relatorio atual.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.historico or not args.historico[0] or args.historico[0] == "None":
        raise SystemExit("Informe --historico ou coloque base_mestre_provisoria.xlsx na pasta data.")
    if not args.atual or args.atual == "None":
        raise SystemExit("Informe --atual ou coloque Equipamentos GerenciarMe*.csv na pasta data.")

    reference_date = None
    if args.data_referencia:
        reference_date = datetime.strptime(args.data_referencia, "%d/%m/%Y")

    result = build_pde_report(
        historico_paths=args.historico,
        atual_path=args.atual,
        base_mestre_path=None if args.base_mestre in {None, "None", ""} else args.base_mestre,
        reference_date=reference_date,
    )

    if args.saida:
        output_path = Path(args.saida)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(args.output_dir) / f"relatorio_pendencias_pde_{stamp}.xlsx"

    output_path = export_pde_excel(result, output_path)

    print("[PDE] Relatorio gerado com sucesso.")
    print(f"[PDE] Arquivo: {output_path}")
    print(f"[PDE] Ativos para cobranca: {result.dashboard.loc[result.dashboard['Indicador'] == 'Equipamentos ativos para cobranca', 'Valor'].iloc[0]}")
    print(f"[PDE] Pendencias: {len(result.pendencias)}")
    print(f"[PDE] Obras com pendencia: {len(result.pendencias_por_obra)}")
    print(f"[PDE] Validacoes antes de cobrar: {len(result.validar_antes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
