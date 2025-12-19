-- A função serve para validar automaticamente a conclusão de desafios de leitura de um usuário, se baseando na quantidade de livros que o usuário coloca na prateleira 'Lidos' de sua estante durante o período de tempo do desafio.
-- O gatilho utiliza da função para, sempre que um usuário adiciona um livro na prateleira, trazê-la a tona e verificar automaticamente se o desafio que está participando foi concluído ou não.
-- O SGBD usado é o PostgreSQL.

CREATE OR REPLACE FUNCTION ValidarConclusaoDesafio()
RETURNS TRIGGER AS $$
DECLARE
    usuario_id INTEGER;
BEGIN

    SELECT UID INTO usuario_id FROM Estante WHERE EID = NEW.EID;
    
    INSERT INTO Concluidos (DID, UID, Meta_Alcancada)
    SELECT 
        du.DID,
        du.UID,
        COUNT(DISTINCT el.ISBN) as Livros_Lidos
    FROM DesafioLeitura_Usuario du
    JOIN Estante_Livro el ON el.EID IN (SELECT EID FROM Estante WHERE UID = du.UID)
    JOIN Estante e ON el.EID = e.EID
    WHERE du.UID = usuario_id
      AND el.Prateleira = 'Lidos'
      AND el.Data_Add BETWEEN du.Data_Inicio AND (
          SELECT Data_Fim FROM DesafioLeitura WHERE DID = du.DID
      )
    GROUP BY du.DID, du.UID
    HAVING COUNT(DISTINCT el.ISBN) >= (SELECT Meta FROM DesafioLeitura WHERE DID = du.DID)
    
    ON CONFLICT (DID, UID) 
    DO UPDATE SET Meta_Alcancada = EXCLUDED.Meta_Alcancada;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ValidarConclusaoDesafio
    AFTER INSERT OR UPDATE ON Estante_Livro
    FOR EACH ROW
    WHEN (NEW.Prateleira = 'Lidos')
    EXECUTE FUNCTION ValidarConclusaoDesafio();