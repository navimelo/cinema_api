class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NaoEncontradoError(AppError):
    status_code = 404


class ConflitoError(AppError):
    """Duplicidade, assento já vendido, exclusão com dependências, estado incompatível."""
    status_code = 409


class RegraNegocioError(AppError):
    """Violação de regra de negócio (dados válidos em tipo, mas inválidos no domínio)."""
    status_code = 422
