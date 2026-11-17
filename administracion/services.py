"""Consultas y métricas locales. Nunca llaman al proveedor de IA."""
from datetime import timedelta
from django.db.models import Count, Min, Q
from django.utils import timezone
from online.models import Preguntas, Usuario

def estadisticas():
    preguntas = Preguntas.objects.filter(archivada=False).annotate(primera_atencion=Min('respuesta__FechaHora',
        filter=Q(respuesta__Usuario__admin=True) | Q(respuesta__Usuario__tecnico=True)))
    tiempos = [(p.primera_atencion - p.Fecha_creacion).total_seconds() for p in preguntas
               if p.primera_atencion and p.primera_atencion >= p.Fecha_creacion]
    promedio = f'{sum(tiempos) / len(tiempos) / 3600:.2f} horas' if tiempos else 'Sin atenciones registradas'
    total = preguntas.count()
    resueltas = preguntas.filter(estado__in=['resuelto', 'cerrado']).count()
    return {'total_preguntas': total,
            'preguntas_sin_respuesta': sum(p.primera_atencion is None for p in preguntas),
            'porcentaje_resueltas': round(resueltas * 100 / total, 1) if total else 0,
            'tiempo_promedio_respuesta': promedio,
            'total_preguntas_mes': preguntas.filter(Fecha_creacion__gte=timezone.now()-timedelta(days=30)).count(),
            'categorias_tendencia': dict(Preguntas.objects.filter(archivada=False).values('categoria').annotate(total=Count('pk')).order_by('-total').values_list('categoria', 'total')),
            'usuarios_activos': Usuario.objects.annotate(num_preguntas=Count('preguntas', filter=Q(preguntas__archivada=False))).order_by('-num_preguntas')[:10]}
