# CLAUDE.md - GreenScreen Bet Generator

## 🎯 Contexto do Projeto
MicroSaaS de automação de vídeo para nicho de apostas esportivas. Transforma dados (Odds, Lucro, Stats) em vídeos verticais (9:16) com estética "Analytical/Dark Mode".

## 💻 Tech Stack
- **Frontend:** React + Vite, Tailwind CSS, Lucide React (ícones).
- **Backend:** Python (FastAPI).
- **Video Engine:** MoviePy + Matplotlib (para gráficos).
- **Database/Auth:** Supabase.
- **Estilo Visual:** Dark Mode, Green Neon (#00FF00), fontes Inter e JetBrains Mono.

## 🏗️ Estrutura de Pastas Sugerida
- `/web`: Frontend React.
- `/server`: Backend FastAPI.
- `/server/templates`: Assets de vídeo (backgrounds, fontes).
- `/server/output`: Armazenamento temporário de vídeos gerados.

## 🛠 Comandos Frequentes
- **Instalar dependências (Python):** `pip install fastapi uvicorn moviepy matplotlib`
- **Rodar Backend:** `uvicorn main:app --reload`
- **Instalar dependências (React):** `npm install`
- **Rodar Frontend:** `npm run dev`

## 🎨 Guia de Estilo (Vibe 2026)
- **Cores:** Fundo #0B0E11 (quase preto), Texto #E5E7EB, Destaque #00FF00.
- **Animações:** Contador de lucro deve ser suave (ease-in-out). Gráfico de linha deve "desenhar" na tela.
- **Overlay:** Aplicar um leve ruído (grain) ou scanlines para look de "Terminal de Dados".

## 🚀 Roadmap MVP (Fim de Semana)
1. [ ] Script Python que gera vídeo MP4 com texto e um gráfico de linha básico.
2. [ ] API FastAPI que aceita POST e retorna o vídeo processado.
3. [ ] UI React com formulário e preview do vídeo.
4. [ ] Integração Supabase para salvar log de gerações.
