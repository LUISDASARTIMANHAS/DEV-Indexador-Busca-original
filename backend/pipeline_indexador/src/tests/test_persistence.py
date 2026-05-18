import unittest
import os
import json
import shutil
from pipeline_indexador.src.storage.index_repository import IndexRepository

class TestIndexPersistence(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        self.storage_path = os.path.join(self.test_dir, "test_index.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_persistence(self):
        # 1. Cria repositório e adiciona dados
        repo = IndexRepository(storage_path=self.storage_path)
        repo.add_tokens("doc1", ["python", "busca"])
        
        # 2. Verifica se o arquivo foi criado
        self.assertTrue(os.path.exists(self.storage_path))
        
        # 3. Cria NOVO repositório e verifica se carregou os dados
        new_repo = IndexRepository(storage_path=self.storage_path)
        self.assertEqual(new_repo.search("python"), ["doc1"])
        self.assertEqual(new_repo.search("busca"), ["doc1"])

    def test_incremental_update(self):
        repo = IndexRepository(storage_path=self.storage_path)
        
        # 1. Indexa documento com certos tokens
        repo.add_tokens("doc1", ["python", "ciencia"])
        self.assertEqual(repo.search("python"), ["doc1"])
        self.assertEqual(repo.search("ciencia"), ["doc1"])
        
        # 2. Atualiza o MESMO documento com novos tokens (remove os antigos)
        repo.add_tokens("doc1", ["java", "web"])
        
        # 3. Verifica se os tokens antigos foram removidos
        self.assertEqual(repo.search("python"), [])
        self.assertEqual(repo.search("ciencia"), [])
        
        # 4. Verifica se os novos tokens foram adicionados
        self.assertEqual(repo.search("java"), ["doc1"])
        self.assertEqual(repo.search("web"), ["doc1"])
        
        # 5. Verifica se persistiu a atualização
        new_repo = IndexRepository(storage_path=self.storage_path)
        self.assertEqual(new_repo.search("python"), [])
        self.assertEqual(new_repo.search("java"), ["doc1"])

if __name__ == '__main__':
    unittest.main()
