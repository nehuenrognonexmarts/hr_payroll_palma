from odoo import models, fields
from datetime import datetime


class HrPaylip(models.Model):
    _inherit = 'hr.payslip'

    valor_tarea = fields.Float("Valor Tarea", compute="_compute_valor_tarea")
    alimentacion = fields.Float("Alimentacion", compute="_compute_alimentacion")
    # dominical = fields.Float("Dominical", compute="_compute_dominical")
    septimo = fields.Float("Septimo", compute="_compute_septimo")
    asuetos = fields.Float("Asuetos", compute="_compute_asuetos")

    def _obtain_tasks(self):
        xma_task= self.env['xma.task.activity'] 
        return xma_task.search([('date', '>=', self.date_from), ('date', '<=', self.date_to), ('employee_id','=', self.employee_id.id)])

    def _compute_valor_tarea(self):
        xma_task_ids = self._obtain_tasks()
        self.valor_tarea = sum(xma_task_ids.mapped('total'))

    def _compute_alimentacion(self): 
        xma_task_ids = self._obtain_tasks()
        days = [task.date.date() for task in xma_task_ids]
        self.alimentacion = len(set(days))*30

    # def _compute_dominical(self):
    #     xma_task_ids = self._obtain_tasks()
    #     self.dominical =  sum(xma_task_ids.mapped('total'))

    def _compute_septimo(self):
        xma_task_ids = self._obtain_tasks()
        days = [task.date.date() for task in xma_task_ids]
        if len(set(days)) < 6:
            self.septimo = 0
        else:
            self.septimo = sum(xma_task_ids.mapped('total'))/len(set(days))

    def _compute_asuetos(self):
        self.asuetos = 0