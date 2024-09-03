from odoo import models, fields
from datetime import timedelta, datetime


class HrPaylip(models.Model):
    _inherit = 'hr.payslip'

    valor_tarea = fields.Float("Valor Tarea", compute="_compute_valor_tarea")
    alimentacion = fields.Float("Alimentacion", compute="_compute_alimentacion")
    # dominical = fields.Float("Dominical", compute="_compute_dominical")
    septimo = fields.Float("Septimo", compute="_compute_septimo")
    asuetos = fields.Float("Asuetos", compute="_compute_asuetos")

    def _obtain_tasks(self):
        xma_task= self.env['xma.task.activity']
        tasks = xma_task.search([
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('employee_id','=', self.employee_id.id)
                ])
        no_sundays = tasks.filtered(lambda t: datetime.strptime(t.date, '%Y-%m-%d').weekday() != 6)
        return no_sundays

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
        dias_tareas = [task.date.date() for task in xma_task_ids]
        dias_necesarios = 6 - self._cantidad_asuetos()
        semanas_trabajadas = self._organizacion_por_semanas(xma_task_ids)
        for semana in semanas_trabajadas:
            skip = "aun tengo que programar aqui"
        if len(set(dias_tareas)) < dias_necesarios:
            self.septimo = 0
        else:
            self.septimo = sum(xma_task_ids.mapped('total'))/len(set(dias_tareas))

    def _compute_asuetos(self):
        cant_asuetos = self._cantidad_asuetos()
        if cant_asuetos == 0:
            self.asuetos = 0
        else:
            inicio_semana = self.date_from - timedelta(days=7)
            final_semana = self.date_to - timedelta(days=7)
            xma_task = self.env['xma.task.activity']
            xma_task_ids = xma_task.search([
                ('date', '>=', inicio_semana),
                ('date', '<=', final_semana),
                ('employee_id', '=', self.employee_id.id)
            ])
            #acá puedo llamar al payslip anterior.
            #luego consulto sus campos
            valor_tarea_pasado = sum(xma_task_ids.mapped('total'))
            self.asuetos = cant_asuetos * (valor_tarea_pasado/6)

    def _cantidad_asuetos(self):
        cant_asuetos = 0
        resource_calendar_leaves = self.env['resource.calendar.leaves']
        
        calendar_leaves = resource_calendar_leaves.search([
            ('date_to', '>=', self.date_from),
            ('date_from', '<=', self.date_to),
        ])

        for leave in calendar_leaves:
            inicio_festivo = max(self.date_from, leave.date_from.date())
            final_festivo = min(self.date_to, leave.date_to.date())

            if inicio_festivo <= final_festivo:
                dias_festivos = (final_festivo - inicio_festivo).days + 1
                cant_asuetos += dias_festivos
        return cant_asuetos
    
    def _obtener_payslip_pasado(self):
        inicio_semana = self.date_from - timedelta(days=7)
        payslips = self.env['hr.payslip'].search([
            ('date_from', '=', inicio_semana),
            ('employee_id','=', self.employee_id.id)
        ])

    def _organizacion_por_semanas(self, tareas):
        tareas_ordenadas = tareas.sorted(key=lambda t: t.date)
        semanas = []
        semana_actual = []
        fecha_inicio_semana = None
        for tarea in tareas_ordenadas:
            fecha_tarea = tarea.date
            inicio_semana_tarea = fecha_tarea - timedelta(days=fecha_tarea.weekday())
            
            if fecha_inicio_semana is None:
                fecha_inicio_semana = inicio_semana_tarea

            if inicio_semana_tarea != fecha_inicio_semana:
                semanas.append(semana_actual)
                semana_actual = []
                fecha_inicio_semana = inicio_semana_tarea
            semana_actual.append(tarea)

        if semana_actual:
            semanas.append(semana_actual)

        return semanas
            
