"""Exceções do pipeline: cada tipo de falha tem um nome claro para facilitar o diagnóstico."""


class PipelineErro(Exception):
    """Base de todas as falhas controladas do pipeline."""


class ArquivoAusenteErro(PipelineErro):
    """Um CSV esperado não existe na pasta de dados."""


class EstruturaInvalidaErro(PipelineErro):
    """O cabeçalho do CSV não corresponde ao contrato em schema.py."""


class QualidadeErro(PipelineErro):
    """Uma validação obrigatória falhou (tipos, chaves, integridade, reconciliação...)."""
