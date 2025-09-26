# En reactores/context_processors.py

def nav_context(request):
    """
    Añade el nombre de la ruta actual al contexto de todas las plantillas.
    Esto nos permite saber qué página está activa para resaltarla en la navegación.
    """
    if request.resolver_match:
        return {'current_path': request.resolver_match.url_name}
    return {}