---
name: cote-para-mim
description: Cota um produto (eletroportáteis, eletrodomésticos e similares) nos fornecedores da Ventura (Martins, Tambasa, FastShop, Casa e Vídeo, Fujioka Distribuidor, Bartofil, Gazin, Friopeças, Belmicro) e devolve links e preços. Use quando pedirem "cote para mim" ou para procurar um produto nesses fornecedores.
---

# Cote para mim

Pesquisa um produto nos sites dos fornecedores da Ventura Comércio (revenda) usando o Chrome do usuário e entrega uma tabela com os anúncios encontrados, links e preços.

## Entrada

A descrição do produto, de preferência com marca, modelo, capacidade, cor e voltagem. Se faltar o produto, pergunte antes de começar.

## Fornecedores e como pesquisar em cada um

Pesquise SEMPRE em todos os 9. Primeiro pelo código do modelo; se não achar, tente também o código sem o último caractere (ex.: GN-B372PFM2 → GN-B372PFM / GN-B372) e depois um termo genérico (ex.: "geladeira lg").

| Fornecedor | Como buscar | Observações |
|---|---|---|
| Martins | `https://www.martinsatacado.com.br/busca/<termo>` | Preço só com login de revenda ("Ver Preço"). Role a página até o fim para carregar todos os itens. |
| Tambasa | Site `https://tambasa.com`; o formulário de busca (campo `keyword`) faz POST. Preencha o campo e envie o form. | Preço só com login ("Identifique-se para ver o preço"). |
| FastShop | `https://site.fastshop.com.br/s?q=<termo>` | Busca pelo código exato às vezes falha; use termo descritivo (ex.: "geladeira lg 375"). Pode ter vários anúncios do mesmo produto (vendedores diferentes). |
| Casa e Vídeo | `https://www.casaevideo.com.br/s?q=<termo>` | Mostra preço no Pix e parcelado. |
| Fujioka | **Usar SOMENTE `https://www.fujiokadistribuidor.com.br/`** (site de revenda), nunca o site comum da Fujioka. A busca por URL não funciona: digitar na caixa de busca e Enter. | Preço pode exigir login de revendedor. Linha forte em informática, ar e TVs. |
| Bartofil | Site `https://www.bartofil.com.br`; usar a caixa de busca e Enter (a URL `/busca?q=` carrega lenta). | Mensagem "Nenhum produto encontrado" quando não tem. |
| Gazin | `https://www.gazin.com.br/busca/<termo>` | Mostra "A partir de" (Pix) e parcelado. |
| Friopeças | `https://www.friopecas.com.br/<termo>?_q=<termo>&map=ft` (domínio com **s**: friopecas) | "OOPS! Não encontramos..." quando não tem. |
| Belmicro | `https://www.belmicro.com.br/<termo>?_q=<termo>&map=ft` ou caixa de busca | "OOPS! Não encontramos..." quando não tem. |

Dicas de navegação:
- Trabalhe na aba que o usuário tem aberta; use `browser_batch` (navegar + extrair com JavaScript) para ir rápido.
- Para extrair, filtre os links cujo texto contém o código do modelo e suba até o elemento que contém "R$" para pegar o preço.
- Recuse cookies não essenciais quando aparecer o aviso.
- Nunca faça login nem digite senha; se o preço exigir login, apenas informe.

## Regras de filtragem

1. **Analise todos os resultados da página**, não só os primeiros. Filtre pelo modelo, não pela posição.
2. **Cor:** se o usuário não informar cor, inclua todas as cores encontradas e indique a cor de cada anúncio. Se informar, mostre só essa cor.
3. **Voltagem:** se o usuário informar voltagem (ex.: "127V ou bivolt"), mostre só essas. 110V e 127V são equivalentes. Se não informar, inclua todas e indique a de cada uma.
4. **Código diferente:** se o código exato não existir mas houver variação muito próxima (mesmo produto, sufixo diferente, ex.: PFM2 vs PFM/PFMB), inclua e avise claramente que o código não é idêntico e que vale confirmar com o fornecedor.
5. **Exclua** acessórios e peças que só citam o modelo (receptor, capa, bolsa, filtro) e modelos diferentes. Kits que contêm o produto podem ir numa seção separada.
6. Anúncios repetidos (patrocinado + orgânico do mesmo produto) contam uma vez só.

## Formato da resposta

Seja DIRETO e CLARO. Nada de introdução, explicação de processo ou texto além do necessário.

Ordem obrigatória:

1. **Opções primeiro:** tabela com colunas Fornecedor | Anúncio (link com título curto, incluindo cor e voltagem) | Preço na busca (Pix/à vista e parcelado; ou "só com login").
2. **Justificativa depois:** lista curta, um item por ponto, explicando por que esses anúncios entraram e outros ficaram de fora (ex.: código não é idêntico, voltagem diferente, cor, acessório). Inclua aqui, em uma linha por fornecedor, onde não encontrei e o que apareceu.
3. Se precisar, uma única linha final de aviso (preço pode mudar / exige login).

Não invente preços: se não aparecer, escreva "sem preço na busca" ou "só com login".
