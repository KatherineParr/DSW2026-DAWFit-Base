import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()

    if form.validate_on_submit():

        #creacion de la actividad
        nueva_act = Actividad(
            nombre=form.nombre.data,
            deporte=form.deporte.data,
            cuota=form.cuota.data,
            plazas_libres=form.plazas_libres.data
        )

        nombre_imagen = None #inicializa por si no se sube

        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data #obtiene archivo
            nombre_imagen = (
                form.deporte.data.lower() #obtiene el deporte
                + "_" #el espacio entre nombre de actividad
                + secure_filename(archivo.filename) #secure limpia el nombre de problemas y filename consigue el nombre
            ) 
            #guardado fisico
            carpeta_subidas = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(carpeta_subidas, exist_ok=True)
            archivo.save(os.path.join(carpeta_subidas, nombre_imagen))

        #guardado en base de datos
        nueva_act.imagen = nombre_imagen

        db.session.add(nueva_act)
        db.session.commit()
        flash("Actividad creada correctamente.", "exito")
        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad)

    #sacar los datos del form del archivo
    if form.validate_on_submit():
        actividad.nombre = form.nombre.data
        actividad.deporte = form.deporte.data
        actividad.cuota = form.cuota.data
        actividad.plazas_libres = form.plazas_libres.data

        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data #obtiene archivo
            nombre_imagen = (
                form.deporte.data.lower() #obtiene el deporte
                + "_" #el espacio entre nombre de actividad
                + secure_filename(archivo.filename) #secure limpia el nombre de problemas y filename consigue el nombre
            ) 
            carpeta_subidas = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(carpeta_subidas, exist_ok=True)
            archivo.save(os.path.join(carpeta_subidas, nombre_imagen))

            #eliminar la imagen vieja
            if actividad.imagen and actividad.imagen != nombre_imagen:
                ruta_antigua = os.path.join(carpeta_subidas, actividad.imagen)
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)

            actividad.imagen = nombre_imagen

        db.session.commit()
        flash("Actividad actualizada con éxito.", "exito")
        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)

    if (actividad.plazas_libres == 0):
        #error
        flash("No se puede eliminar una actividad con el cupo lleno", "error") #esto es un mensaje, primero el mensaje y luego el tipo (info, error, exito)
        return redirect(url_for("public.mostrar_actividades"))

    else:
        if (actividad.imagen): #comprueba que umagen del objeto de actividad tiene un valor, si lo tiene continua
            carpeta_subidas = current_app.config["UPLOAD_FOLDER"]
            ruta_imagen = os.path.join(carpeta_subidas, actividad.imagen) #saca la ruta de la imagen
            if os.path.exists(ruta_imagen): #si el camino existe
                os.remove(ruta_imagen) #se elimina la imagen

        #borra el registro de la base de datos tanto si tiene imagen como si no
        db.session.delete(actividad)
        db.session.commit()

    return redirect(url_for("public.mostrar_actividades"))


# ejercicio/ bloque 2 validacion
@admin_bp.before_request
def verificar_permisos_admin():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.es_monitor:
        abort(403)