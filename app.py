from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect
from urllib.parse import unquote
from flask import Flask, request, send_from_directory, render_template
from sqlalchemy.exc import IntegrityError

from model import Session, Valve
from logger import logger
from schemas import *
from flask_cors import CORS

info = Info(title="MVP API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# definindo tags para categorizar as operações da API

# a tag 'home_tag' é para documentação em geral, especificamente para a seleção de uma ferramenta de documentação chamada Swagger.
home_tag = Tag(name="Documentação",
               description="Seleção de documentação: Swagger")

# a tag 'valve_tag' é para ações relacionadas a válvulas, como adicionar, visualizar, editar e remover válvulas da base de dados.
valve_tag = Tag(
    name="Válvula", description="Adição, visualização,edição e remoção de válvulas da base")


def home():
    """Redireciona para a tela que permite a escolha do estilo de documentação Swagger.
    """
    return redirect('/openapi/swagger')


"""Adiciona a rota '/' para a função home com método GET
    """
app.add_url_rule('/', view_func=home, methods=['GET'])


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/x-icon')


@app.post('/valve', tags=[valve_tag],
          responses={"200": ValveViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_valve(form: ValveSchema):
    """Adiciona uma nova Válvula à base de dados.

    Retorna uma representação das válvulas.
    """
    # Criando objeto da classe Valve
    valve = Valve(
        nome=form.nome,
        descricao=form.descricao,
        tipo=form.tipo,
        vazao=form.vazao)
    logger.debug(f"Adicionando válvula de nome: '{valve.nome}'")
    try:
        # criando conexão com a base
        session = Session()
        # adicionando válvula
        session.add(valve)
        # efetivando o comando de adição de novo item na tabela
        session.commit()
        logger.debug(f"Adicionada válvula de nome: '{valve.nome}'")
        return apresenta_valve(valve), 200

    except IntegrityError as e:
        # como a duplicidade do nome é a provável razão do IntegrityError
        error_msg = "Válvula de mesmo nome já salva na base :/"
        logger.warning(
            f"Erro ao adicionar válvula '{valve.nome}', {error_msg}")
        return {"message": error_msg}, 409

    except Exception as e:
        # caso um erro fora do previsto
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(
            f"Erro ao adicionar válvula '{valve.nome}', {error_msg}")
        return {"message": error_msg}, 400


@app.get('/valves', tags=[valve_tag],
         responses={"200": ListagemValveSchema, "404": ErrorSchema})
def get_valves():
    """Faz a busca por todas as Válvulas cadastradas

    Retorna uma representação da listagem de válvulas.
    """
    logger.debug(f"Coletando Válvulas ")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    valves = session.query(Valve).all()

    if not valves:
        # se não há produtos cadastrados
        return {"válvulas": []}, 200
    else:
        logger.debug(f"%d válvulas econtradss" % len(valves))
        # retorna a representação de produto
        print(valves)
        return apresenta_valves(valves), 200


@app.delete('/valve', tags=[valve_tag],
            responses={"200": ValveDelSchema, "404": ErrorSchema})
def del_produto(query: ValveBuscaSchema):
    """Remove uma Válvula da base de dados.

      Retorna 204 em caso de sucesso.
      """
    valve_nome = unquote(unquote(query.nome))
    print(valve_nome)
    logger.debug(f"Deletando dados sobre válvula #{valve_nome}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(Valve).filter(
        Valve.nome == valve_nome).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletada válvula #{valve_nome}")
        return {"mesage": "Válvula removida", "Nome": valve_nome}
    else:
        # se o produto não foi encontrado
        error_msg = "Válvula não encontrada na base :/"
        logger.warning(
            f"Erro ao deletar válvula #'{valve_nome}', {error_msg}")
        return {"mesage": error_msg}, 404


@app.put('/valve', tags=[valve_tag], responses={"200": ValveViewSchema, "404": ErrorSchema})
def update_valve(form: ValveUpdateSchema):
    """Atualiza as informações de uma Válvula a partir do ID da válvula.

    Retorna uma representação das válvulas.
    """
    valve_id = form.id
    logger.debug(f"Atualizando dados sobre válvula #{valve_id}")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    valve = session.query(Valve).filter(Valve.id == valve_id).first()

    if not valve:
        # se a válvula não foi encontrada
        error_msg = "Válvula não encontrada"
        logger.warning(f"{error_msg}: {valve_id}")
        return {"message": error_msg}, 404

    # atualizando os dados da válvula
    valve.nome = form.nome
    valve.descricao = form.descricao
    valve.tipo = form.tipo
    valve.vazao = form.vazao

    # efetivando a atualização
    session.commit()

    logger.debug(f"Dados da válvula '{valve.nome}' atualizados")
    return apresenta_valve(valve), 200
