from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad


public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/actividades")
def mostrar_actividades():
    consulta = Actividad.query
    buscarNombre = request.args.get("buscar", "").strip()
    tienePlazas = request.args.get("plazas")

    if buscarNombre:
        consulta = consulta.filter(Actividad.nombre.ilike(f"%{buscarNombre}%"))

    if tienePlazas:
        consulta = consulta.filter(Actividad.plazas_libres > 0)

    actividades = consulta.all()

    deporte_fav = request.cookies.get("deporte_fav")

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):

    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.set_cookie(
        "deporte_fav",
        value=deporte,
        max_age=60 * 60 * 24 * 15,
        httponly=True,
        samesite="Lax",
    )

    return respuesta


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():

    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.delete_cookie("deporte_fav")

    return respuesta


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    #primero recuperar la session
    #guargar una lista vacia reservas que get recupera del diccionario la clave "" y [] crea una lista vacia si no se puede recuperar una o no habia
    reservas = session.get("reservas", []) 

    #recuperar los datos de la base de datos
    actividad = db.get_or_404(Actividad, act_id)

    if(actividad.plazas_libres == 0): #que tenga plazas libres
        flash("La actividad no tiene plazas libres", "error")
        return redirect(url_for("public.mostrar_actividades"))

    elif(act_id in reservas): #que ya no este en reservas
        flash("La actividad ya esta en reservas", "error") 
        return redirect(url_for("public.mostrar_actividades"))

    elif(len(reservas) >= 3): #que reservas tengo al menos tres actividadedes con la longitud len()
        flash("Se ha alcanzado el maximo de 3 reservas", "error")
        return redirect(url_for("public.mostrar_actividades"))

    else:
        reservas.append(act_id) #añade el identificador de id a la lista
        session.modified = True
        flash("Se ha inscrito con exito", "exito")
        return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():

    #recuperar base (otra ve cry) de los ids que esten en reserva
    reservas = session.get("reservas", []) #recuperamos primero la session de reserva

    #sacamos de actividad segun in reservas
    actividades = Actividad.query.filter(Actividad.id.in_(reservas)).all() #se saca el id y sacamos el query de los que id esten en reserva y all todos los que coincidad con la condicion del filter

    #declararlos para poder tenerlos a 0 si nada y poder remplazarlos adelante
    total = 0.0
    final = total
    conDescuento = False

    #usar for para sumar todas las cuotas
    for actividad in actividades:
        total += actividad.cuota 
    #aplicar descuento si tiene 3 actividades 
    if ( len(reservas) == 3):
        conDescuento = True
        final = total * (1-.20)
    

    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total,
        descuento_aplicado=conDescuento,
        total_final=final,
    )


@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):

    reservas = session.get("reservas", []) #recuperamos primero la session de reserva

    if act_id in reservas:
        reservas.remove(act_id)
        flash("Se ha cancelado con exito", "exito")
        return redirect(url_for("public.ver_reservas"))
    else:
        flash("No se ha podido cancelar", "error")
        return redirect(url_for("public.ver_reservas"))



@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():

    #recuperar session de nuevo y asignarla
    reservas = session.get("reservas", [])

    #consultar en base de datos las plazas libres
    actividades = Actividad.query.filter(Actividad.id.in_(reservas)).all()

    for actividad in actividades:
        actividad.plazas_libres -= 1

    db.session.commit()
    session.pop("reservas", None) #vaciar reservas

    return redirect(url_for("public.mostrar_actividades"))
