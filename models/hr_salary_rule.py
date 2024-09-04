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
        no_sundays = tasks.filtered(lambda t: t.date.weekday() != 6)
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
        semanas_trabajadas = self._organizacion_por_semanas(xma_task_ids)
        valor_septimos = 0
        for semana in semanas_trabajadas:
            inicio = semana[0].date.date()
            fin = semana[-1].date.date()
            # asuetos = self._obtener_asuetos(inicio,fin)
            dias_trabajados = len(set([tarea.date.date() for tarea in semana]))
            dias_necesarios = 6 - self._cantidad_asuetos(inicio, fin)
            #problema. si trabajo un domingo no se toma en cuenta la tarifa del domingo
            #deberia excluir domingos?
            if dias_trabajados >= dias_necesarios:
                valor_septimos += sum(tarea.total for tarea in semana)/dias_trabajados

        self.septimo = valor_septimos

    def _compute_asuetos(self):
        inicio_semana = self.date_from
        final_semana = self.date_from + timedelta(days=6)
        valor_asuetos = 0
        while inicio_semana < self.date_to:
            cant_asuetos = self._cantidad_asuetos(inicio_semana, final_semana)
            if cant_asuetos > 0:
                inicio_semana_pasada = self.date_from - timedelta(days=7)
                final_semana_pasada = self.date_to - timedelta(days=7)
                xma_task = self.env['xma.task.activity']
                xma_task_ids = xma_task.search([
                    ('date', '>=', inicio_semana_pasada),
                    ('date', '<=', final_semana_pasada),
                    ('employee_id', '=', self.employee_id.id)
                ])
                valor_tarea_pasado = sum(xma_task_ids.mapped('total'))
                # incentivo no se puede agregar, por que no esta asociado a una semana.
                # extraordinario no se puede agregar por que no esta asociado a una semana.
                # asuetos pasados
                trabajo_dominical = 0 #necesito el codigo de trabajo dominical
                valor_asuetos += cant_asuetos * ((valor_tarea_pasado)/6)
            inicio_semana += timedelta(days=7)
            final_semana += timedelta(days=7)
        self.asuetos = valor_asuetos

    def _obtener_asuetos_trabajados(self, inicio, fin):
        resource_calendar_leaves = self.env['resource.calendar.leaves']
        calendar_leaves = resource_calendar_leaves.search([
            ('date_to', '>=', inicio),
            ('date_from', '<=', fin),
        ])
        return calendar_leaves
        # return calendar_leaves.sorted(key=lambda t: t.date_to)

    def _cantidad_asuetos(self, inicio, fin):
        cant_asuetos = 0
        resource_calendar_leaves = self.env['resource.calendar.leaves']
        calendar_leaves = resource_calendar_leaves.search([
            ('date_to', '>=', inicio),
            ('date_from', '<=', fin),
        ])

        for leave in calendar_leaves:
            inicio_festivo = max(inicio, leave.date_from.date())
            final_festivo = min(fin, leave.date_to.date())

            if inicio_festivo <= final_festivo:
                dias_festivos = (final_festivo - inicio_festivo).days + 1
                cant_asuetos += dias_festivos
        return cant_asuetos
    
    def _obtener_payslip_pasado(self):
        inicio_semana = self.date_from - timedelta(days=14)
        #preguntar si siempre va a ser 14 días atras
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
            fecha_tarea = tarea.date.date()
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
            
