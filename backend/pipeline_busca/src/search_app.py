from pipeline_busca.src.search.search_service import SearchService


def main():
    """
    Executa o serviço de busca.
    """

    # cria o serviço de busca
    search_service = SearchService()

    # consulta que será realizada
    query = "python dados"

    # executa a busca
    results = search_service.search(query)

    # imprime os resultados
    print("Resultados da busca:")
    print(results)


if __name__ == "__main__":
    main()
