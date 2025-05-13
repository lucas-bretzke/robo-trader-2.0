import logging

class APIHandler:
    def __init__(self, api):
        self.api = api

    def get_available_pairs(self):
        """Recupera todos os pares disponíveis na plataforma"""
        try:
            # Obter todos os pares de diferentes categorias
            binary_pairs = self.api.get_all_open_time()
            
            available_pairs = []
            
            # Verificar em todas as categorias (binary, turbo, digital)
            categories = ['binary', 'turbo', 'digital']
            
            for category in categories:
                if category in binary_pairs:
                    for pair, status in binary_pairs[category].items():
                        if status['open']:
                            available_pairs.append(pair)
            
            # Remover duplicatas
            available_pairs = list(set(available_pairs))
            logging.info(f"Pares disponíveis encontrados: {len(available_pairs)}")
            return available_pairs
        except Exception as e:
            logging.error(f"Erro ao obter pares disponíveis: {str(e)}")
            return []

    def check_pair_availability(self, pair):
        """Verifica se um par específico está disponível para negociação"""
        try:
            # Verificar disponibilidade em todas as categorias
            binary_pairs = self.api.get_all_open_time()
            
            # Normalizar o nome do par para maiúsculas
            normalized_pair = pair.upper()
            
            for category in ['binary', 'turbo', 'digital']:
                if category in binary_pairs:
                    if normalized_pair in binary_pairs[category]:
                        if binary_pairs[category][normalized_pair]['open']:
                            logging.info(f"Par {normalized_pair} disponível na categoria {category}")
                            return True
            
            logging.warning(f"Par {normalized_pair} não está disponível em nenhuma categoria")
            return False
        except Exception as e:
            logging.error(f"Erro ao verificar disponibilidade do par {pair}: {str(e)}")
            return False