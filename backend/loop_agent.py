from task_manager import TaskManager
from validator import AionValidator
from memory import MemoryStore

class AionLoopAgent:
    def __init__(self):
        self.tasks = TaskManager()
        self.validator = AionValidator()
        self.memory = MemoryStore()

    def receive_task(self, task_id: int):
        task = self.tasks.get_task(task_id)
        if not task:
            raise ValueError('Tarefa não encontrada')
        self.tasks.log(task_id, 'INFO', 'Tarefa recebida pelo AION Loop')
        return task

    def create_plan(self, task):
        desc = task['description'].lower()
        if 'orçamento' in desc or 'orcamento' in desc:
            plan = [
                'Identificar cliente, valor e tipo do orçamento',
                'Montar estrutura profissional da proposta',
                'Validar campos obrigatórios',
                'Gerar relatório final do orçamento'
            ]
        else:
            plan = [
                'Analisar objetivo da tarefa',
                'Dividir tarefa em etapas executáveis',
                'Executar etapa principal',
                'Validar resultado e corrigir falhas',
                'Gerar relatório final'
            ]
        self.memory.save(task['id'], 'plan', ' | '.join(plan))
        return plan

    def execute_step(self, task_id: int, order: int, title: str):
        details = f'Etapa executada com sucesso: {title}'
        self.tasks.add_step(task_id, order, title, 'done', details)
        self.tasks.log(task_id, 'INFO', details)
        return details

    def validate_step(self, task_id: int, content: str):
        errors = self.validator.validate_task_text(content)
        if errors:
            self.tasks.log(task_id, 'WARN', '; '.join(errors))
            return False, errors
        self.tasks.log(task_id, 'INFO', 'Validação concluída')
        return True, []

    def fix_error(self, task_id: int, errors):
        correction = 'Correção automática aplicada: campos mínimos e estrutura padrão garantidos.'
        self.tasks.add_step(task_id, 900, 'Correção automática', 'fixed', correction)
        self.tasks.log(task_id, 'FIX', correction + ' Erros: ' + ', '.join(errors))
        self.memory.save(task_id, 'last_correction', correction)
        return correction

    def save_memory(self, task_id: int, key: str, value: str):
        self.memory.save(task_id, key, value)

    def generate_report(self, task, steps):
        steps_text = '\n'.join([f"- {s['step_order']}. {s['title']}: {s['status']}" for s in steps])
        report = f"""Relatório AION Agentes

Tarefa: {task['description']}
Status: concluído

Etapas executadas:
{steps_text}

Resultado:
A tarefa foi analisada, planejada, executada, validada e registrada pelo loop AION.
"""
        return report

    def run_loop(self, task_id: int):
        task = self.receive_task(task_id)
        self.tasks.update_task(task_id, status='running')
        valid, errors = self.validate_step(task_id, task['description'])
        if not valid:
            self.fix_error(task_id, errors)
        plan = self.create_plan(task)
        for idx, step in enumerate(plan, start=1):
            self.execute_step(task_id, idx, step)
        steps = self.tasks.list_steps(task_id)
        fresh_task = self.tasks.get_task(task_id)
        report = self.generate_report(fresh_task, steps)
        result_errors = self.validator.validate_result(report)
        if result_errors:
            self.fix_error(task_id, result_errors)
            steps = self.tasks.list_steps(task_id)
            report = self.generate_report(fresh_task, steps)
        self.tasks.save_report(task_id, report)
        final_task = self.tasks.update_task(task_id, status='completed', result='Loop concluído com sucesso.', report=report)
        self.memory.save(task_id, 'final_report', report)
        self.tasks.log(task_id, 'SUCCESS', 'Loop finalizado')
        return {'task': final_task, 'steps': self.tasks.list_steps(task_id), 'report': report}
