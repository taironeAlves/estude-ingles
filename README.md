# Estude Inglês

Aplicação web para aprendizado de inglês: dicionário pessoal de palavras com
áudio (texto-para-fala) e treinamentos de escuta/escrita.

## Funcionalidades

- **Dicionário**: cadastro de palavras em inglês com tradução e frase de
  exemplo. O áudio da palavra é gerado automaticamente (via
  [edge-tts](https://github.com/rany2/edge-tts)) caso ainda não exista,
  seguindo a "regra das 21 vezes": a palavra é repetida 21 vezes, com 1
  segundo de silêncio entre cada repetição, tudo no mesmo arquivo de áudio.
  Cada palavra também pode ter um áudio "humanizado" opcional da sua frase
  de exemplo, gerado sob demanda pelo botão "Gerar áudio IA" (usa o modelo
  [OmniVoice](https://github.com/k2-fsa/OmniVoice) via um Space público no
  Hugging Face — veja a seção [Áudio humanizado](#áudio-humanizado-omnivoice-opcional)).
- **Treinamento**:
  - *Ouvir e digitar*: toca o áudio de uma palavra aleatória e o usuário
    digita o que ouviu.
  - *Complete a frase*: mostra uma frase de exemplo com a palavra oculta e o
    usuário precisa digitá-la.

Novos tipos de treinamento podem ser adicionados futuramente na aba
Treinamento.

## Stack

- Backend: Python + [FastAPI](https://fastapi.tiangolo.com/) + SQLite
  (`sqlite3` da stdlib)
- TTS: [edge-tts](https://github.com/rany2/edge-tts) (gratuito, sem API key)
- Montagem do áudio (repetição 21x + silêncio): [pydub](https://github.com/jiaaro/pydub)
  usando o ffmpeg embutido via [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
  (não precisa instalar ffmpeg manualmente)
- Frontend: HTML/CSS/JS puro, servido como arquivos estáticos pelo próprio
  backend

## Dados locais (não versionados)

O banco de dados (`data/dictionary.db`) e os áudios gerados
(`data/audio/*.mp3`) ficam em `data/` e **não são enviados ao GitHub**
(veja `.gitignore`). Isso mantém o repositório público livre de conteúdo
gerado localmente e específico do seu vocabulário/progresso.

## Como rodar

### Usando os scripts prontos (recomendado)

**Windows:**
```bat
setup.bat
start.bat
```

**Linux/Mac:**
```bash
./setup.sh
./start.sh
```

`setup` cria o ambiente virtual (`.venv`) e instala as dependências.
`start` sobe o servidor e abre o navegador automaticamente em
http://localhost:8010 (a porta 8010 é usada para evitar conflito com a 8000,
comumente ocupada por outros projetos).

### Manualmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8010
```

Acesse http://localhost:8010

Na primeira execução, o banco SQLite e a pasta de áudios são criados
automaticamente. A geração de áudio requer conexão com a internet (o
edge-tts consulta o serviço de TTS da Microsoft Edge).

## Áudio humanizado (OmniVoice, opcional)

O botão "Gerar áudio IA" na frase de exemplo de cada palavra chama o Space
público [k2-fsa/OmniVoice](https://huggingface.co/spaces/k2-fsa/OmniVoice)
no Hugging Face (GPU compartilhada gratuita, "ZeroGPU"). Pontos importantes:

- **Não é uma API oficial/estável** — é um demo comunitário; pode ficar
  lento, enfileirado ou mudar sem aviso. Por isso é uma ação manual e
  opcional, separada da geração automática de áudio da palavra (que continua
  sempre no edge-tts, rápido e confiável).
- **Cota gratuita é curta**: sem autenticação, a cota do ZeroGPU se esgota
  rápido (na prática, poucas gerações). Para uma cota maior, crie um token
  gratuito em https://huggingface.co/settings/tokens e coloque num arquivo
  `.env` na raiz do projeto (não versionado):
  ```
  HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```
- Não requer instalação de PyTorch/modelo local — só a lib `gradio_client`,
  já incluída no `requirements.txt`.

## Estrutura

```
app/
  main.py          # app FastAPI, monta rotas e arquivos estáticos
  config.py        # caminhos (data/, static/, etc.)
  database.py      # conexão e schema SQLite
  tts.py           # geração de áudio da palavra sob demanda (edge-tts)
  omnivoice.py     # áudio humanizado opcional da frase (OmniVoice/HF Space)
  routers/
    words.py       # CRUD do dicionário
    training.py    # exercícios de treinamento
static/            # frontend (HTML/CSS/JS)
data/              # banco + áudios (gitignored, exceto data/audio/.gitkeep)
```
