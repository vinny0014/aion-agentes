class AionValidator:
    def validate_task_text(self, text: str):
        errors = []
        if not text or len(text.strip()) < 3:
            errors.append('Tarefa muito curta.')
        return errors

    def validate_result(self, result: str):
        errors = []
        if not result:
            errors.append('Resultado vazio.')
        if 'Relatório AION' not in result:
            errors.append('Relatório sem assinatura AION.')
        return errors
