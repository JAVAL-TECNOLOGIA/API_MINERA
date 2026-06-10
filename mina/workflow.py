from auth_api.serializers import get_user_roles

from .models import CartillaOperacionMina


ACTION_SUBMIT = "submit"
ACTION_OBSERVE = "observe"
ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_CLOSE = "close"


WORKFLOW_ACTIONS = {
    ACTION_SUBMIT: {
        "to_state": CartillaOperacionMina.ESTADO_ENVIADO,
        "from_states": {
            CartillaOperacionMina.ESTADO_BORRADOR,
            CartillaOperacionMina.ESTADO_OBSERVADO,
        },
        "requires_comment": False,
        "permission": "submit",
    },
    ACTION_OBSERVE: {
        "to_state": CartillaOperacionMina.ESTADO_OBSERVADO,
        "from_states": {CartillaOperacionMina.ESTADO_ENVIADO},
        "requires_comment": True,
        "permission": "review",
    },
    ACTION_APPROVE: {
        "to_state": CartillaOperacionMina.ESTADO_APROBADO,
        "from_states": {CartillaOperacionMina.ESTADO_ENVIADO},
        "requires_comment": False,
        "permission": "review",
    },
    ACTION_REJECT: {
        "to_state": CartillaOperacionMina.ESTADO_RECHAZADO,
        "from_states": {
            CartillaOperacionMina.ESTADO_ENVIADO,
            CartillaOperacionMina.ESTADO_OBSERVADO,
        },
        "requires_comment": True,
        "permission": "review",
    },
    ACTION_CLOSE: {
        "to_state": CartillaOperacionMina.ESTADO_CERRADO,
        "from_states": {CartillaOperacionMina.ESTADO_APROBADO},
        "requires_comment": False,
        "permission": "close",
    },
}


def role_codes(user):
    return set(get_user_roles(user))


def has_any_role(user, role_codes_):
    return bool(role_codes(user) & set(role_codes_))


def can_manage_all(user):
    return user.is_staff or user.is_superuser or has_any_role(user, ["admin"])


def can_review(user):
    return can_manage_all(user) or has_any_role(user, ["supervisor", "revisor"])


def can_close(user):
    return can_review(user)


def can_view_cartilla(cartilla, user):
    return cartilla.user_id == user.id or can_review(user)


def has_workflow_permission(user, cartilla, permission):
    if permission == "submit":
        return cartilla.user_id == user.id or can_manage_all(user)
    if permission == "review":
        return can_review(user)
    if permission == "close":
        return can_close(user)
    return False


def get_available_cartilla_actions(cartilla, user):
    can_view = can_view_cartilla(cartilla, user)
    can_edit_actor = cartilla.user_id == user.id or can_manage_all(user)
    editable_state = cartilla.estado_workflow in {
        CartillaOperacionMina.ESTADO_BORRADOR,
        CartillaOperacionMina.ESTADO_OBSERVADO,
    }
    review_allowed = can_review(user)

    return {
        "canSubmit": (
            editable_state
            and has_workflow_permission(user, cartilla, "submit")
        ),
        "canObserve": (
            cartilla.estado_workflow == CartillaOperacionMina.ESTADO_ENVIADO
            and review_allowed
        ),
        "canApprove": (
            cartilla.estado_workflow == CartillaOperacionMina.ESTADO_ENVIADO
            and review_allowed
        ),
        "canReject": (
            cartilla.estado_workflow
            in {
                CartillaOperacionMina.ESTADO_ENVIADO,
                CartillaOperacionMina.ESTADO_OBSERVADO,
            }
            and review_allowed
        ),
        "canClose": (
            cartilla.estado_workflow == CartillaOperacionMina.ESTADO_APROBADO
            and can_close(user)
        ),
        "canView": can_view,
        "canEditDraft": can_view
        and can_edit_actor
        and editable_state,
    }
