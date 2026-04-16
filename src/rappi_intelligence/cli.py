"""Command-line interface for the Rappi intelligence agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from rappi_intelligence.agent import RappiOperationsAgent
from rappi_intelligence.reporting import write_reports


def main() -> None:
    """Run the CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Rappi operations intelligence CLI")
    parser.add_argument("--data", help="Path to workbook or CSV folder", default=None)
    parser.add_argument("--ask", help="Ask one question and exit", default=None)
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate executive Markdown and HTML reports",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated reports",
    )
    args = parser.parse_args()

    agent = RappiOperationsAgent(args.data)

    if args.report:
        markdown_path, html_path = write_reports(agent.dataset, args.output_dir)
        print(f"Reports generated: {markdown_path} and {html_path}")

    if args.ask:
        _print_response(agent.ask(args.ask))
        return

    if not args.report:
        _interactive_loop(agent)


def _interactive_loop(agent: RappiOperationsAgent) -> None:
    print("Rappi Operations Intelligence Agent")
    print("Type 'exit' to quit.\n")
    print("Starter questions:")
    for question in agent.starter_questions():
        print(f"- {question}")
    print()

    while True:
        question = input("Question> ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        _print_response(agent.ask(question))


def _print_response(response) -> None:
    print(f"\n{response.answer}\n")
    if response.table is not None and not response.table.empty:
        print(response.table.head(20).to_string(index=False))
        print()
    if response.suggestions:
        print("Suggested next questions:")
        for suggestion in response.suggestions:
            print(f"- {suggestion}")
    print()


if __name__ == "__main__":
    main()
