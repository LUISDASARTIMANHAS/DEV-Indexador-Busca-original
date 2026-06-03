import re


class MessageFormatter:
    MAX_RESULTS = 5

    def format_search_results(self, *, query: str, results: list[dict], total: int) -> str:
        if not results:
            return (
                "Não encontrei documentos para essa consulta.\n"
                "Tente usar termos mais gerais, por exemplo: estágio, TCC ou relatório."
            )

        lines = [f'Encontrei {total} documento(s) para "{query}":', ""]
        for index, item in enumerate(results[: self.MAX_RESULTS], start=1):
            snippet = self._clean_snippet(item.get("snippet", ""))
            lines.extend(
                [
                    f"{index}. {item.get('title', 'Documento sem título')}",
                    f"Relevância: {item.get('relevance', 0)}%",
                ]
            )
            if snippet:
                lines.append(f'Trecho: "{snippet}"')
            lines.append("")

        lines.append('Responda com "detalhes 1" para ver mais informações do primeiro resultado.')
        return "\n".join(lines).strip()

    def format_document_details(self, document: dict | None) -> str:
        if document is None:
            return "Não encontrei detalhes para esse documento."

        content = self._truncate(self._clean_snippet(document.get("content", "")), 500)
        lines = [
            document.get("title", "Documento sem título"),
            f"ID: {document.get('id')}",
            f"Categoria: {document.get('category', '-')}",
            f"Tipo: {document.get('document_type') or document.get('type') or '-'}",
            f"Arquivo: {document.get('file_name', '-')}",
            f"Autor: {document.get('author_name', '-')}",
        ]
        if content:
            lines.extend(["", f"Prévia: {content}"])
        return "\n".join(lines)

    def format_help(self) -> str:
        return (
            "Olá! Eu sou o bot do IFESDOC.\n\n"
            "Você pode me pedir coisas como:\n"
            "- buscar documentos sobre estágio\n"
            "- mostrar PDFs de 2025 sobre TCC\n"
            "- detalhes do documento 15\n"
            "- detalhes 1\n"
            "- gerar relatório das buscas sem resultado\n"
            "- ver meu histórico de consultas"
        )

    def format_unknown(self) -> str:
        return (
            "Não consegui entender sua solicitação.\n"
            'Tente escrever algo como: "buscar documentos sobre estágio".'
        )

    def format_report(self, report: dict) -> str:
        summary = report.get("summary", {})
        return (
            "Relatório de buscas do IFESDOC:\n"
            f"Total de consultas: {summary.get('totalQueries', 0)}\n"
            f"Consultas sem resultado: {summary.get('queriesWithoutResults', 0)}\n"
            f"Tempo médio: {summary.get('averageResponseTimeMs', 0)} ms\n"
            f"Média de resultados: {summary.get('averageResults', '0')}"
        )

    def format_history(self, interactions: list) -> str:
        if not interactions:
            return "Ainda não há interações registradas para este usuário no bot."
        lines = ["Últimas interações no bot:"]
        for item in interactions:
            lines.append(f"- {item.mensagem_usuario} ({item.intencao_detectada or 'unknown'})")
        return "\n".join(lines)

    def format_rate_limited(self) -> str:
        return "Muitas mensagens em pouco tempo. Aguarde alguns instantes e tente novamente."

    def _clean_snippet(self, value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        text = re.sub(r"\s+", " ", text).strip()
        return self._truncate(text, 240)

    def _truncate(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return value[: limit - 3].rstrip() + "..."
