---
name: pesquisa-google
description: Pesquisa um item no Google (só resultados orgânicos), entra nos sites encontrados, entende o site, busca o item dentro dele e classifica se o site é fabricante, distribuidor ou revenda daquele item. Use no robô de cotação depois dos fornecedores padrão, ou quando pedirem para cotar pelo Google.
---

# Pesquisa no Google

Acha onde comprar um item fora da lista de fornecedores padrão, usando o Chrome do usuário.

## 1. Montar as buscas

Da descrição, tire o que identifica o produto: fabricante, modelo/referência, part number e 2 ou 3 especificações chave.
Faça de 2 a 3 buscas, da mais específica para a mais genérica. Exemplos:
- `"NEWORK" "14.1 04HR"` (fabricante + referência entre aspas)
- `microventilador 80x80x25 12V 0,40A`
- `microventilador 12v 80mm comprar`

Abra `https://www.google.com/search?q=<termo>&hl=pt-BR&gl=br` (espaços viram `+`).

## 2. Ler só os resultados orgânicos

**Ignore tudo que for patrocinado**: anúncios no topo e no rodapé ("Patrocinado", "Sponsored", "Anúncio"), carrossel de
Shopping patrocinado e qualquer link de `googleadservices.com` ou com `/aclk?`. Os orgânicos ficam em `#rso`; os anúncios
ficam fora dele (`#tads`, `#bottomads`). Para listar só os orgânicos, rode:

```js
[...document.querySelectorAll('#rso a h3')].map(h => {
  const a = h.closest('a');
  const bloco = h.closest('[data-hveid]') || a.parentElement;
  const cite = bloco.querySelector('cite');
  return {
    titulo: h.innerText,
    site: (cite ? cite.innerText : '').split(/\s›|\s>/)[0].trim(),
    url: a.href,
    patrocinado: /Patrocinad|Sponsored|Anúncio/i.test(bloco.innerText.slice(0, 80)),
    trecho: (bloco.innerText || '').slice(0, 300).replace(/\n+/g, ' ')
  };
}).filter(r => r.url.startsWith('http') && !/googleadservices|\/aclk\?/.test(r.url) && !r.patrocinado)
```

O `url` costuma vir como `https://www.google.com/goto?url=...` (redirecionador do Google); o domínio real está em `site`.
Navegue pelo `url` e, no anúncio, use o endereço final da página (`location.href`) como link, nunca o `goto`.

Se aparecer a página "tráfego incomum" / CAPTCHA do Google, **não resolva**: pare a pesquisa no Google e registre `google bloqueado`.

Descarte resultados que não vendem nem fabricam: notícias, fóruns, YouTube, Wikipédia, PDFs de manual, sites de comparação de preço
sem loja, Mercado Livre/OLX de pessoa física. **Abra pelo menos 6 sites** diferentes (um por domínio, até uns 10),
priorizando lojas e distribuidores brasileiros, e não repita os fornecedores padrão que já foram cotados.
Faça pelo menos 4 buscas diferentes e olhe a 2ª página quando a 1ª trouxer poucas lojas brasileiras.

## 3. Em cada site: entender, buscar, conferir

1. Abra o resultado. Leia a página inicial ou o rodapé/"Quem somos" o suficiente para responder: o que esse site é?
2. Se o link não caiu direto no produto, use a **caixa de busca do próprio site** com o modelo ou o termo principal.
3. Abra a página do produto e confira as especificações principais contra a descrição (modelo, tensão, potência, medidas etc.).
4. Anote preço (à vista e parcelado, se houver) ou "sob consulta"/"só com login". Nunca faça login.
5. Se não tiver preço, anote o contato de vendas que o site mostrar (telefone, WhatsApp, e-mail).

Recuse cookies não essenciais. Não preencha formulários, não peça orçamento, não adicione ao carrinho.

## 4. Classificar o site

`tipo_site` de cada resultado:
- `fabricante`: o site é da marca que fabrica o item (ex.: site oficial da NEWORK para um produto NEWORK).
- `distribuidor`: vende no atacado/para revenda (pede CNPJ, fala em "atacado", "distribuidor", "revenda", preço só com login de lojista).
- `revenda`: loja que vende ao consumidor final ou a empresas no varejo.
- `marketplace`: Mercado Livre, Amazon, Magalu, Shopee etc. (diga o vendedor, se aparecer).

Explique em poucas palavras por que classificou assim (o que o site mostrou).

## 5. O que devolver

Cada site útil vira um anúncio com: fornecedor (nome da loja/empresa), título, link da página do produto, preço,
`tipo_site`, `origem: "google"`, contato (se não houver preço) e observação (o que confere ou não com a descrição).
Sites visitados que não serviram vão em "não encontrado" com o motivo (ex.: "não vende, é fórum", "modelo diferente").
