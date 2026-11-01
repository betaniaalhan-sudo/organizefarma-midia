"""Checagem de legendas contra a RDC 96/2008 (propaganda de medicamentos).

É uma triagem automática por palavras e padrões. Ela não substitui a
revisão técnica da farmacêutica responsável: aponta trechos que merecem
atenção antes de publicar.

Base: RDC Anvisa 96/2008, arts. 8º, 9º, 10, 11, 26, 27, 29 e 32.
Conferir sempre se houve alteração da norma antes de usar como fundamento.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

ALTO = "ALTO"
MEDIO = "MÉDIO"
INFO = "INFO"


@dataclass
class Alerta:
    nivel: str
    trecho: str
    motivo: str
    base: str

    def __str__(self) -> str:
        return f"[{self.nivel}] \"{self.trecho}\" — {self.motivo} ({self.base})"


@dataclass
class Resultado:
    alertas: list[Alerta] = field(default_factory=list)

    @property
    def bloqueia(self) -> bool:
        """True quando há pelo menos um alerta de nível ALTO."""
        return any(a.nivel == ALTO for a in self.alertas)

    def resumo(self) -> str:
        if not self.alertas:
            return "Nenhum alerta encontrado. Revisão humana continua recomendada."
        linhas = [str(a) for a in self.alertas]
        status = "REVISAR ANTES DE PUBLICAR" if self.bloqueia else "Pontos de atenção"
        return status + ":\n- " + "\n- ".join(linhas)


def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar padrões com segurança."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.lower()


# (padrão regex sobre o texto normalizado, nível, motivo, base legal)
_REGRAS: list[tuple[str, str, str, str]] = [
    # Art. 8º, VII — imperativos que induzem ao consumo
    (r"\b(tome|tomem|use|usem|experimente|experimentem|tenha|tenham)\b",
     MEDIO,
     "Imperativo que pode induzir ao consumo de medicamento. Se o post falar de medicamento, reescreva sem o imperativo.",
     "RDC 96/2008, art. 8º, VII"),
    # Art. 8º, VI — sabor agradável
    (r"\b(saboros[oa]s?|gostos[oa]s?|delicios[oa]s?)\b",
     MEDIO,
     "Sugerir sabor agradável de medicamento é vedado (informar o sabor é permitido).",
     "RDC 96/2008, art. 8º, VI e art. 9º, II"),
    # Art. 8º, I e XI — uso indiscriminado / medo de não usar
    (r"\b(sem (receita|prescricao)|automedica\w*|nao fique sem|nao deixe de tomar|sua saude depende)\b",
     ALTO,
     "Pode estimular uso indiscriminado ou sugerir que a saúde será afetada sem o medicamento.",
     "RDC 96/2008, art. 8º, I e XI"),
    # Art. 8º, II — sugerir diagnóstico
    (r"\b(voce (tem|esta com|pode estar com)|descubra se voce tem|sintomas de que voce tem)\b",
     MEDIO,
     "Pode sugerir diagnóstico ao público. Prefira orientar a procurar o profissional de saúde.",
     "RDC 96/2008, art. 8º, II"),
    # Art. 8º, IV — "novo" por mais de 2 anos
    (r"\b(novo|nova|lancamento)\b",
     INFO,
     "Só anuncie medicamento como \"novo\" até 2 anos do início da comercialização no Brasil.",
     "RDC 96/2008, art. 8º, IV"),
    # Art. 26, I — comprovação científica (isentos de prescrição)
    (r"\b(comprovad[oa] cientificamente|cientificamente comprovad[oa]|demonstrado em ensaios clinicos)\b",
     ALTO,
     "Expressão vedada para medicamentos isentos de prescrição.",
     "RDC 96/2008, art. 26, I"),
    # Art. 26, II — única alternativa / dispensa médico
    (r"\b(unic[oa] (solucao|alternativa|tratamento)|dispensa (o )?medico|nao precisa (de )?medico|sem precisar de medico)\b",
     ALTO,
     "Não pode sugerir que o medicamento é a única alternativa ou que a consulta é dispensável.",
     "RDC 96/2008, art. 26, II"),
    # Art. 26, IV — excessos etílicos ou gastronômicos
    (r"\b(ressaca|exagerou na (comida|bebida)|depois da balada|comeu demais|bebeu demais)\b",
     ALTO,
     "Relacionar medicamento a excessos etílicos ou gastronômicos é vedado.",
     "RDC 96/2008, art. 26, IV"),
    # Art. 26, V — desempenho e beleza
    (r"\b(emagrec\w*|perca peso|perder peso|mais energia|turbin\w*|desempenho sexual|potencia sexual|mais disposicao|pele perfeita|rejuvenesc\w*)\b",
     MEDIO,
     "Associar medicamento a desempenho físico, intelectual, sexual ou à beleza só é permitido se for propriedade aprovada pela Anvisa.",
     "RDC 96/2008, art. 26, V"),
    # Art. 9º, III e IV — superlativos sem referência
    (r"\b(100% (seguro|eficaz)|totalmente seguro|sem efeitos? colaterais?|absolut[oa]|perfeit[oa]|eficacia (maxima|total))\b",
     ALTO,
     "Superlativos de eficácia ou segurança só com estudo científico referenciado na própria peça.",
     "RDC 96/2008, art. 9º, III e IV"),
    (r"\b(seguro|eficaz)\b",
     INFO,
     "\"Seguro\"/\"eficaz\" exigem frase de justificativa com referência científica.",
     "RDC 96/2008, art. 9º, III"),
    # Art. 10 — fidelidade com medicamento
    (r"\b(sorteio|sorteamos|ganhe pontos|acumule pontos|brinde|premio)\b",
     MEDIO,
     "Programas de fidelidade, sorteios e prêmios não podem ter medicamento como objeto, e o material deve informar essa restrição.",
     "RDC 96/2008, art. 10"),
    # Art. 11, §4º — desconto sem preço integral
    (r"\b(\d{1,2}\s?% (de )?(off|desconto)|desconto de \d{1,2}\s?%|promocao)\b",
     MEDIO,
     "Ao anunciar desconto ou preço promocional de medicamento, informe também o preço integral.",
     "RDC 96/2008, art. 11, §4º"),
    # Art. 8º, IX — expectativa de venda (dirigida a farmácias)
    (r"\b(nao perca vendas|acerte no estoque|o melhor para seus lucros)\b",
     ALTO,
     "Criar expectativa de venda é vedado.",
     "RDC 96/2008, art. 8º, IX; IN 5/2009"),
    # Art. 27, 29 e 32 — tarjados, controlados e GLP-1 ao público leigo
    (r"\b(ozempic|wegovy|mounjaro|saxenda|victoza|trulicity|semaglutida|tirzepatida|liraglutida|dulaglutida|"
     r"rivotril|clonazepam|alprazolam|zolpidem|ritalina|metilfenidato|venvanse|lisdexanfetamina|"
     r"sibutramina|isotretinoina|roacutan|tadalafila|sildenafila|viagra|cialis|"
     r"amoxicilina|azitromicina|antibiotic\w*)\b",
     ALTO,
     "Medicamento de venda sob prescrição (ou controlado/antimicrobiano/GLP-1): propaganda só para profissionais habilitados, nunca em perfil aberto ao público. Conteúdo educativo sem marca e sem apelo de venda deve ser avaliado caso a caso.",
     "RDC 96/2008, arts. 27, 29 e 32"),
    # Conteúdo voltado a crianças (isentos de prescrição)
    (r"\b(criancas?|infantil|kids|pequenos)\b",
     INFO,
     "Mensagens dirigidas a crianças ou adolescentes são vedadas na propaganda de medicamentos isentos de prescrição.",
     "RDC 96/2008, art. 26, VII"),
]

_ADVERTENCIA = re.compile(
    r"(e um medicamento\.? seu uso pode trazer riscos|procure (o )?medico e (o )?farmaceutico|leia a bula)"
)
_PALAVRAS_MEDICAMENTO = re.compile(
    r"\b(medicamento|remedio|comprimido|capsula|xarope|pomada|gotas|analgesico|antialergico|antiacido|vitamina)\b"
)


def checar_legenda(texto: str) -> Resultado:
    """Analisa uma legenda e devolve os alertas encontrados."""
    norm = _normalizar(texto)
    resultado = Resultado()
    vistos: set[tuple[str, str]] = set()

    for padrao, nivel, motivo, base in _REGRAS:
        for m in re.finditer(padrao, norm):
            trecho = texto[m.start():m.end()]
            chave = (trecho.lower(), base)
            if chave in vistos:
                continue
            vistos.add(chave)
            resultado.alertas.append(Alerta(nivel, trecho, motivo, base))

    fala_de_medicamento = bool(_PALAVRAS_MEDICAMENTO.search(norm))
    if fala_de_medicamento:
        # Com medicamento no texto, apelo infantil deixa de ser lembrete e vira alerta.
        for a in resultado.alertas:
            if a.base == "RDC 96/2008, art. 26, VII":
                a.nivel = ALTO

    if fala_de_medicamento and not _ADVERTENCIA.search(norm):
        resultado.alertas.append(Alerta(
            MEDIO,
            "(advertência ausente)",
            "Se o post divulgar medicamento isento de prescrição, inclua a advertência obrigatória "
            "(ex.: \"[NOME] É UM MEDICAMENTO. SEU USO PODE TRAZER RISCOS. PROCURE O MÉDICO E O "
            "FARMACÊUTICO. LEIA A BULA.\") e os dados do art. 22.",
            "RDC 96/2008, arts. 22 a 24",
        ))

    ordem = {ALTO: 0, MEDIO: 1, INFO: 2}
    resultado.alertas.sort(key=lambda a: ordem[a.nivel])
    return resultado
