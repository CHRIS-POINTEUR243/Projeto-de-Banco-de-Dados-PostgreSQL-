import streamlit as st
import psycopg2
from datetime import date

# ---------------------------------
# CONFIGURAÇÃO DO BANCO
# ---------------------------------
DB_CONFIG = {
    "dbname": "bd_goodreads",
    "user": "postgres",      # usuário do PostgreSQL
    "password": "12345",   # senha 
    "host": "localhost",
    "port": 5432,
}


def get_connection():
    """Abre uma conexão simples com o PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


def execute_query(sql: str, params=None):
    """Executa uma consulta SQL e retorna (colunas, linhas)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return colnames, rows


def show_table(colnames, rows, empty_msg="Nenhum resultado encontrado."):
    """Mostra o resultado em formato de tabela no Streamlit."""
    if not rows:
        st.info(empty_msg)
        return
    data = [dict(zip(colnames, row)) for row in rows]
    st.table(data)


# =========================================================
#   SEÇÃO 1 – OPERAÇÕES / GATILHO (TRABALHO PARTE 3)
# =========================================================

def op_listar_desafios():
    """Consulta sem parâmetro – listar desafios de leitura."""
    st.subheader("Desafios de leitura (consulta sem parâmetro)")

    sql = """
        SELECT DID, Meta, Data_Fim
        FROM DesafioLeitura
        ORDER BY DID;
    """
    try:
        cols, rows = execute_query(sql)
        show_table(cols, rows, "Nenhum desafio encontrado.")
    except Exception as e:
        st.error(f"Erro ao listar desafios: {e}")


def op_listar_livros_lidos_usuario():
    """Consulta com parâmetro – livros 'Lidos' de um usuário."""
    st.subheader("Livros 'Lidos' de um usuário (consulta com parâmetro)")

    uid = st.number_input("UID do usuário", min_value=1, step=1)

    if st.button("Buscar livros lidos"):
        sql = """
            SELECT el.EID, el.ISBN, el.Prateleira, el.Data_Add
            FROM Estante_Livro el
            JOIN Estante e ON el.EID = e.EID
            WHERE e.UID = %s
              AND el.Prateleira = 'Lidos'
            ORDER BY el.Data_Add;
        """
        try:
            cols, rows = execute_query(sql, (uid,))
            show_table(
                cols,
                rows,
                f"Nenhum livro 'Lido' encontrado para o usuário UID={uid}."
            )
        except Exception as e:
            st.error(f"Erro ao listar livros lidos: {e}")


def op_adicionar_livro_lido():
    """INSERT que dispara o gatilho de validação de desafios."""
    st.subheader("Adicionar livro 'Lido' (dispara o gatilho)")

    st.markdown(
        """
        Quando você insere um livro na prateleira **'Lidos'**, o gatilho
        **`trg_ValidarConclusaoDesafio`** é disparado e chama a função
        `ValidarConclusaoDesafio()`, que verifica automaticamente se o
        usuário atingiu a meta de algum Desafio de Leitura.
        """
    )

    eid = st.number_input("EID da estante", min_value=1, step=1)
    isbn = st.text_input("ISBN do livro (13 dígitos)")
    data_add = date.today()

    if st.button("Inserir livro como 'Lido'"):
        if not isbn:
            st.warning("Informe um ISBN válido.")
            return

        sql = """
            INSERT INTO Estante_Livro (EID, ISBN, Prateleira, Data_Add)
            VALUES (%s, %s, 'Lidos', %s);
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(sql, (eid, isbn, data_add))
            conn.commit()
            cur.close()
            conn.close()

            st.success("Livro inserido na prateleira 'Lidos'.")
            st.info(
                "Se a meta de algum desafio foi alcançada, "
                "a tabela 'Concluidos' foi atualizada pelo gatilho."
            )
        except Exception as e:
            st.error(f"Erro ao inserir livro: {e}")


def op_listar_desafios_concluidos_usuario():
    """Consulta com parâmetro – desafios concluídos de um usuário."""
    st.subheader("Desafios concluídos de um usuário (consulta com parâmetro)")

    uid = st.number_input(
        "UID do usuário", min_value=1, step=1, key="uid_concluidos_op"
    )

    if st.button("Buscar desafios concluídos"):
        sql = """
            SELECT c.DID, c.Meta_Alcancada
            FROM Concluidos c
            WHERE c.UID = %s;
        """
        try:
            cols, rows = execute_query(sql, (uid,))
            show_table(
                cols,
                rows,
                f"Nenhum desafio concluído encontrado para o usuário UID={uid}."
            )
        except Exception as e:
            st.error(f"Erro ao listar desafios concluídos: {e}")


def secao_operacoes_gatilho():
    st.header("Operações / Gatilho (Parte 3)")

    escolha = st.radio(
        "Escolha uma opção:",
        [
            "1 - Listar desafios (sem parâmetro)",
            "2 - Livros 'Lidos' de um usuário (com parâmetro)",
            "3 - Adicionar livro 'Lido' (dispara gatilho)",
            "4 - Desafios concluídos de um usuário (com parâmetro)",
        ],
    )

    if escolha.startswith("1"):
        op_listar_desafios()
    elif escolha.startswith("2"):
        op_listar_livros_lidos_usuario()
    elif escolha.startswith("3"):
        op_adicionar_livro_lido()
    elif escolha.startswith("4"):
        op_listar_desafios_concluidos_usuario()


# =========================================================
#   SEÇÃO 2 – CONSULTAS PARTE II (ARQUIVO consultas.sql)
# =========================================================

def consulta_1():
    st.subheader("1. Usuários que participam de todos os grupos de fantasia.")

    sql = """
        SELECT u.UID, u.Nome
        FROM Usuario u
        WHERE NOT EXISTS (
            SELECT g.GID 
            FROM Grupo g 
            WHERE g.Categoria = 'Fantasia'
            EXCEPT
            SELECT p.GID 
            FROM Participacao p 
            WHERE p.UID = u.UID
        );
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum usuário encontrado.")


def consulta_2():
    st.subheader("2. Autores com livros em múltiplos gêneros.")

    sql = """
        SELECT 
            u.Nome as Autor,
            a.Nacionalidade,
            COUNT(DISTINCT lg.Genero) as Generos_Distintos
        FROM Autor a
        JOIN Usuario u ON a.UID = u.UID
        JOIN Autor_Livro al ON a.UID = al.UID
        JOIN Livro_Genero lg ON al.ISBN = lg.ISBN
        GROUP BY u.Nome, a.Nacionalidade, a.UID
        HAVING COUNT(DISTINCT lg.Genero) > 1;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum autor com múltiplos gêneros encontrado.")


def consulta_3():
    st.subheader(
        "3. Usuários que publicaram mais de N postagens e os grupos em que participam."
    )

    # PARAMETRIZADA: mínimo de postagens (na Parte II era fixo > 2)
    minimo_postagens = st.number_input(
        "Mínimo de postagens", min_value=1, value=2, step=1
    )

    if st.button("Executar consulta 3"):
        sql = """
            SELECT 
                u.Nome,
                COUNT(p.PID) as Total_Postagens,
                COUNT(DISTINCT pg.GID) as Grupos_Participantes
            FROM Usuario u
            LEFT JOIN Postagem p ON u.UID = p.UID
            LEFT JOIN Postagem_Grupo pg ON p.PID = pg.PID
            GROUP BY u.UID, u.Nome
            HAVING COUNT(p.PID) > %s
            ORDER BY Total_Postagens DESC;
        """
        cols, rows = execute_query(sql, (minimo_postagens,))
        show_table(
            cols,
            rows,
            f"Nenhum usuário com mais de {minimo_postagens} postagens encontrado.",
        )


def consulta_4():
    st.subheader(
        "4. Popularidade dos livros por gênero: total de resenhas e média de notas."
    )

    sql = """
        SELECT 
            g.Nome as Genero,
            l.Titulo,
            COUNT(DISTINCT r.PID) as Total_Resenhas,
            AVG(r.Nota) as Media_Nota
        FROM Genero g
        JOIN Livro_Genero lg ON g.Nome = lg.Genero
        JOIN Livro l ON lg.ISBN = l.ISBN
        LEFT JOIN Resenha r ON l.ISBN = r.ISBN
        GROUP BY g.Nome, l.Titulo, l.ISBN
        ORDER BY Genero, Total_Resenhas DESC;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum dado de popularidade encontrado.")


def consulta_5():
    st.subheader(
        "5. Desafios de Leitura onde os participantes atingiram em média "
        "mais de 70% da meta."
    )

    sql = """
        SELECT 
            d.DID,
            g.Nome as Grupo,
            d.Meta,
            COUNT(DISTINCT du.UID) as Total_Participantes,
            AVG(c.Meta_Alcancada) as Media_Conclusao
        FROM DesafioLeitura d
        LEFT JOIN Grupo g ON d.GID = g.GID
        JOIN DesafioLeitura_Usuario du ON d.DID = du.DID
        JOIN Concluidos c ON d.DID = c.DID AND du.UID = c.UID
        GROUP BY d.DID, g.Nome, d.Meta
        HAVING AVG(c.Meta_Alcancada) > d.Meta * 0.7
        ORDER BY Media_Conclusao DESC;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum desafio encontrado com média > 70% da meta.")


def consulta_6():
    st.subheader(
        "6. Usuários mais ativos (2 ou mais postagens), ordenados por seguidores."
    )

    sql = """
        SELECT 
            eu.Nome,
            eu.Total_Resenhas,
            eu.Total_Discussoes,
            eu.Total_Postagens,
            eu.Total_Grupos,
            COUNT(DISTINCT s.Seguidor_UID) as Seguidores
        FROM EstatisticasUsuario eu
        JOIN Segue s ON eu.UID = s.Seguido_UID
        WHERE eu.Total_Postagens > 1 
        GROUP BY eu.UID, eu.Nome, eu.Total_Resenhas, eu.Total_Discussoes, 
                 eu.Total_Postagens, eu.Total_Grupos
        ORDER BY Seguidores DESC;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum usuário ativo encontrado.")


def consulta_7():
    st.subheader(
        "7. Enquetes com mais de 5 votos, com grupo e total de votos."
    )

    sql = """
        SELECT 
            e.Pergunta,
            g.Nome as Grupo,
            COUNT(DISTINCT v.UID) as Total_Votos,
            COUNT(DISTINCT o.Opcao_ID) as Total_Opcoes
        FROM Enquete e
        JOIN Postagem p ON e.PID = p.PID
        LEFT JOIN Postagem_Grupo pg ON p.PID = pg.PID
        LEFT JOIN Grupo g ON pg.GID = g.GID
        JOIN Opcoes o ON e.PID = o.PID
        JOIN Voto v ON o.Opcao_ID = v.Opcao_ID
        GROUP BY e.PID, e.Pergunta, g.Nome
        HAVING COUNT(DISTINCT v.UID) > 5
        ORDER BY Total_Votos DESC;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhuma enquete com mais de 5 votos encontrada.")


def consulta_8():
    st.subheader(
        "8. Usuários que compraram mais de N livros, com métricas de transações."
    )

    # PARAMETRIZADA: mínimo de livros (na Parte II era fixo > 2)
    minimo_livros = st.number_input(
        "Mínimo de livros comprados", min_value=1, value=2, step=1
    )

    if st.button("Executar consulta 8"):
        sql = """
            SELECT 
                eu.Nome,
                COUNT(DISTINCT t.TID) as Total_Transacoes,
                SUM(tl.Quantidade) as Total_Livros_Comprados,
                AVG(tl.Quantidade) as Media_Livros_Por_Transacao
            FROM EstatisticasUsuario eu
            JOIN Transacao t ON eu.UID = t.UID
            JOIN Transacao_Livro tl ON t.TID = tl.TID
            GROUP BY eu.UID, eu.Nome
            HAVING SUM(tl.Quantidade) > %s
            ORDER BY Total_Livros_Comprados DESC;
        """
        cols, rows = execute_query(sql, (minimo_livros,))
        show_table(
            cols,
            rows,
            f"Nenhum usuário com mais de {minimo_livros} livros comprados.",
        )


def consulta_9():
    st.subheader("9. Livros mais favoritados por usuários.")

    sql = """
        SELECT 
            l.Titulo,
            COUNT(DISTINCT el.EID) as Total_Estantes_Favoritos,
            STRING_AGG(DISTINCT u.Nome, ', ') as Usuarios_Que_Favoritaram
        FROM Livro l
        JOIN Estante_Livro el ON l.ISBN = el.ISBN
        JOIN Estante e ON el.EID = e.EID
        JOIN Usuario u ON e.UID = u.UID
        WHERE el.Prateleira = 'Favoritos'
        GROUP BY l.ISBN, l.Titulo
        HAVING COUNT(DISTINCT el.EID) > 1
        ORDER BY Total_Estantes_Favoritos DESC;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum livro favoritado por múltiplos usuários.")


def consulta_10():
    st.subheader(
        "10. Usuários que nunca postaram, mas participam de grupos, "
        "mostrando quantos grupos frequentam."
    )

    sql = """
        SELECT 
            u.UID,
            u.Nome,
            u.Email,
            COUNT(pg.GID) as Total_Grupos_Participantes
        FROM Usuario u
        JOIN Participacao pg ON u.UID = pg.UID
        WHERE NOT EXISTS (
            SELECT 1 
            FROM Postagem p 
            WHERE p.UID = u.UID
        )
        GROUP BY u.UID, u.Nome, u.Email
        ORDER BY Total_Grupos_Participantes DESC;
    """
    cols, rows = execute_query(sql)
    show_table(cols, rows, "Nenhum usuário encontrado com esse perfil.")


def secao_consultas_parte_ii():
    st.header("Consultas – Parte II do Trabalho")

    opcoes = {
        "Consulta 1 – Usuários em todos os grupos de fantasia": consulta_1,
        "Consulta 2 – Autores com livros em múltiplos gêneros": consulta_2,
        "Consulta 3 – Usuários com mais de N postagens": consulta_3,
        "Consulta 4 – Popularidade dos livros por gênero": consulta_4,
        "Consulta 5 – Desafios com média > 70% da meta": consulta_5,
        "Consulta 6 – Usuários mais ativos por seguidores": consulta_6,
        "Consulta 7 – Enquetes com mais de 5 votos": consulta_7,
        "Consulta 8 – Usuários que compraram mais de N livros": consulta_8,
        "Consulta 9 – Livros mais favoritados": consulta_9,
        "Consulta 10 – Usuários que nunca postaram, mas participam de grupos": consulta_10,
    }

    escolha = st.selectbox("Escolha a consulta:", list(opcoes.keys()))
    func = opcoes[escolha]
    func()


# =========================================================
#   MAIN
# =========================================================

def main():
    st.title("Trabalho Banco de Dados Goodreads")

    secao = st.sidebar.radio(
        "Escolha a seção:",
        [
            "Operações / Gatilho (Parte 3)",
            "Consultas Parte II (arquivo consultas.sql)",
        ],
    )

    if secao.startswith("Operações"):
        secao_operacoes_gatilho()
    else:
        secao_consultas_parte_ii()


if __name__ == "__main__":
    main()

