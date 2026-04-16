"""Command-line interface for the Rappi intelligence agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from rappi_intelligence.agent import RappiOperationsAgent
from rappi_intelligence.config import DEFAULT_PROVIDER_MODELS
from rappi_intelligence.credentials import CredentialStore
from rappi_intelligence.llm_providers import SUPPORTED_PROVIDERS
from rappi_intelligence.reporting import write_reports


def main() -> None:
    """Run the CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Rappi operations intelligence CLI")
    parser.add_argument("--data", help="Path to workbook or CSV folder", default=None)
    parser.add_argument(
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        help="LLM provider to use",
        default=None,
    )
    parser.add_argument("--model", help="Provider model name", default=None)
    parser.add_argument("--api-key", help="API key to encrypt and save", default=None)
    parser.add_argument(
        "--save-key",
        action="store_true",
        help="Save --api-key in encrypted SQLite storage and exit",
    )
    parser.add_argument(
        "--require-llm",
        action="store_true",
        help="Fail if the selected LLM provider is not configured",
    )
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

    if args.save_key:
        _save_key(args.provider, args.model, args.api_key)
        return

    agent = RappiOperationsAgent(
        data_source=args.data,
        provider=args.provider,
        model=args.model,
        require_llm=args.require_llm,
    )

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


def _save_key(provider: str | None, model: str | None, api_key: str | None) -> None:
    if not provider:
        raise SystemExit("--provider is required with --save-key")
    if provider != "ollama" and not api_key:
        raise SystemExit("--api-key is required for hosted providers")

    selected_model = model or DEFAULT_PROVIDER_MODELS[provider]
    CredentialStore().save_provider(provider, selected_model, api_key)
    if provider == "ollama":
        print(f"Saved local Ollama model configuration: {selected_model}")
    else:
        print(f"Encrypted API key saved for {provider} with model {selected_model}")


if __name__ == "__main__":
    main()
