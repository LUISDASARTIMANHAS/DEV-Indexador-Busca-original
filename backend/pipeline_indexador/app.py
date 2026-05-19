from pipeline_indexador.src.indexer.indexer_service import IndexerService


def main():
    """
    Executa o indexador.
    """

    indexer = IndexerService()

    indexer.index_document(
        "doc1",
        "Python é muito usado para ciência de dados e busca"
    )

    print("Documento indexado")


if __name__ == "__main__":
    main()
