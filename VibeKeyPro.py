import os
import sys
import warnings

os.environ["NUMBA_NUM_THREADS"] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module="numba")

import threading
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import librosa
import numpy as np
import csv
import pygame
import subprocess
import imageio_ffmpeg
import pyloudnorm as pysn
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import shutil
import time
import random
import webbrowser
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from PIL import Image, ImageTk, ImageDraw
import io

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

try:
    pygame.mixer.init()
except Exception as e:
    print(f"Aviso no Pygame mixer: {e}")

KEY_MAPPING = {
    'C major': '8B', 'C# major': '3B', 'Db major': '3B', 'D major': '10B',
    'D# major': '5B', 'Eb major': '5B', 'E major': '12B', 'F major': '7B',
    'F# major': '2B', 'Gb major': '2B', 'G major': '9B', 'G# major': '4B',
    'Ab major': '4B', 'A major': '11B', 'A# major': '6B', 'Bb major': '6B',
    'B major': '1B', 'C minor': '5A', 'C# minor': '12A', 'Db minor': '12A',
    'D minor': '7A', 'D# minor': '2A', 'Eb minor': '2A', 'E minor': '9A',
    'F minor': '4A', 'F# minor': '11A', 'Gb minor': '11A', 'G minor': '6A',
    'G# minor': '1A', 'Ab minor': '1A', 'A minor': '8A', 'A# minor': '3A',
    'Bb minor': '3A', 'B minor': '10A'
}

COLOR_PALETTES = {
    "Azul Estúdio": {"primary": "#0284c7", "hover": "#0369a1", "text": "#38bdf8", "accent": "#4f46e5", "border": "#0369a1"},
    "Verde Cyber": {"primary": "#16a34a", "hover": "#15803d", "text": "#4ade80", "accent": "#059669", "border": "#15803d"},
    "Vermelho Neon": {"primary": "#dc2626", "hover": "#b91c1c", "text": "#f87171", "accent": "#e11d48", "border": "#b91c1c"},
    "Amarelo Solar": {"primary": "#ca8a04", "hover": "#a16207", "text": "#facc15", "accent": "#d97706", "border": "#a16207"},
    "Roxo Deep": {"primary": "#9333ea", "hover": "#7e22ce", "text": "#c084fc", "accent": "#a855f7", "border": "#7e22ce"},
}

class CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.TkdndVersion = TkinterDnD._require(self)
        except Exception as e:
            print(f"Aviso DnD: {e}")

class SongAnalyzerProApp(CTk):
    def __init__(self):
        super().__init__()

        self.title("VIBE KEY FINDER PRO - Studio Edition")
        self.geometry("1380x890")
        self.minsize(1180, 750)
        
        self.current_theme_mode = "Dark"
        self.current_palette_name = "Azul Estúdio"
        self.is_rgb_active = False
        self.rgb_job = None
        self.is_shuffle_active = False
        self.is_repeat_active = False

        self.configure(fg_color="#121215")

        self.analyzed_data = {}
        self.current_playing_path = None
        self.current_audio_y = None
        self.current_audio_sr = None
        self.animation_job = None
        self.current_selected_item = None
        self.sort_directions = {}
        self.current_cover_image = None
        
        self.playback_start_offset_sec = 0.0

        raw_tips = [
            # Bloco Suno & ACE Studio (30)
            "Utilize tags de metatags entre colchetes como [Verse], [Chorus] e [Drop] para controlar a estrutura no Suno.",
            "Insira instrumentação específica nos prompts do Suno, como [Heavy Analog Bassline] ou [Roland TR-909 Drums].",
            "Para evitar vozes estridentes no Suno, adicione descrições de timbres como [Warm Baritone Vocals].",
            "Use o recurso de Extend no Suno estrategicamente a partir de um refrão forte para formar faixas completas de 5 minutos.",
            "No ACE Studio, ajuste os parâmetros de expressão vocal manualmente nota a nota para humanizar acapellas.",
            "Importe arquivos MIDI limpos para o ACE Studio para garantir alinhamento exato com a escala desejada.",
            "Adicione a tag [Instrumental Break] ao gerar instrumentais no Suno para evitar vocais indesejados.",
            "Use descrições de mixagem nos prompts do Suno como [Sidechain Compression] e [Punchy Master].",
            "Gere stems curtos de 30 segundos no Suno focados em texturas de efeitos para transições de DJ.",
            "Ajuste o alinhamento temporal das consoantes no ACE Studio para evitar atrasos rítmicos vocais.",
            "Passe áudios do Suno com ruído por ferramentas de IA de separação de stems para limpá-los.",
            "Use tags de transição de energia como [Build-up] e [Drum Roll] 8 compassos antes do drop.",
            "Altere o parâmetro de Gender Factor no ACE Studio para criar coros vocais encorpados.",
            "Insira nomes de microfones lendários nos prompts do Suno (ex: [Recorded via Neumann U87]).",
            "Utilize ferramentas de transcrição para MIDI quando o Suno criar uma progressão de acordes perfeita.",
            "Desenhe curvas de dinâmica de volume expressivas nas notas longas do ACE Studio.",
            "Evite usar nomes de artistas reais diretamente nos prompts do Suno para prevenir bloqueios de copyright.",
            "Adicione texturas orgânicas como [Subtle Vinyl Crackle] nos prompts de produções eletrónicas.",
            "Explore diferentes fonemas e respirações artificiais nos finais de frases no ACE Studio.",
            "Divida letras longas em blocos menores no Suno para garantir dicção alinhada ao tempo.",
            "Utilize tags de tom exato para forçar o Suno a gerar faixas compatíveis com a Roda Camelot.",
            "Utilize o editor de formantes do ACE Studio para dar maior peso a vozes agudas sintéticas.",
            "Crie variações de uma mesma faixa no Suno alterando apenas o estilo secundário de género.",
            "Utilize o modo manual de letras no Suno para pontuar com vírgulas e ditar pausas de respiração.",
            "Ajuste o parâmetro de portamento no ACE Studio para simular cantores executando notas ligadas.",
            "Extraia linhas de sintetizador do Suno e reutilize-as como camadas secundárias no seu DAW.",
            "Insira [Minimalist Arrangement] no Suno para garantir espaço livre para os seus próprios elementos.",
            "Crie dublagens vocais (double tracks) no ACE Studio com pequenas variações de afinação estéreo.",
            "Utilize prompts baseados em décadas (ex: [80s Synthwave Bass]) para guiar timbres vintage.",
            "Salve um documento com seus prompts de maior sucesso para formar sua biblioteca pessoal de IA.",

            # Bloco FL Studio (30)
            "Utilize o mixer do FL Studio roteando baterias para um sub-grupo com compressão paralela.",
            "Organize o Playlist do FL Studio usando cores padronizadas por categorias de instrumentos.",
            "Utilize o plugin Fruity Parametric EQ 3 em modo linear phase para cortes cirúrgicos.",
            "Aplique o Gross Beat em automações criativas de half-time em breaks gerados por IA.",
            "Configure o Edison no canal mestre do FL Studio para capturar ideias rápidas em tempo real.",
            "Utilize o plugin Patcher para criar cadeias complexas de efeitos paralelos num só lugar.",
            "Use a ferramenta de LFO no piano roll do FL Studio para desenhar automações de velocidade por nota.",
            "Ative Keep on Remind nas configurações de renderização para evitar sobrecarga de buffer.",
            "Utilize o Slicex para fatiar loops complexos de percussão e reatribuí-los a pads MIDI.",
            "Configure a compensação de atraso de plugin (PDC) em modo automático no FL Studio.",
            "Use o Peak Controller para ligar o brilho de um sintetizador ao volume de uma bateria.",
            "Organize plugins favoritos na pasta Plugin Database do FL Studio para acesso instantâneo.",
            "Utilize o modo de estiramento Pro Transient nas propriedades de audio clips do Playlist.",
            "Insira um medidor de correlação de fase Wave Candy no master do mixer.",
            "Utilize Alt + T no Playlist para adicionar marcadores de tempo estruturais.",
            "Use o Control Surface para criar painéis de macro personalizados para sintetizadores.",
            "Aplique compilação de áudio gravando múltiplas tomadas vocais em modo loop contínuo.",
            "Utilize o Limiter nativo apenas como segurança em sub-grupos, reservando masters para limiters dedicados.",
            "Escolha curvas matemáticas perfeitas ao criar eventos de automação no FL Studio.",
            "Salve projetos como Project with Assets para garantir que nenhum sample externo se perca.",
            "Utilize o Sytrus para criar sub-basses limpos baseados em síntese FM de alta qualidade.",
            "Use o seletor de polifonia no Channel Rack para limitar vozes ativas em pads longos.",
            "Crie automações de filtro suaves usando o botão de interpolação de pontos do FL Studio.",
            "Utilize o Soundgoodizer com cautela em baixos percentuais para dar brilho rápido.",
            "Consolide padrões MIDI complexos em arquivos WAV usando Consolidate Track para poupar CPU.",
            "Configure atalhos de teclado personalizados para comandos frequentes no FL Studio.",
            "Utilize o Fruity Convolver com impulsos acústicos reais para criar reverbs autênticos.",
            "Use a função Noise Profile do Edison para remover ruídos de fundo em gravações caseiras.",
            "Organize os canais do mixer em sub-misturas lógicas de Drums, Bass, Instruments e Vocals.",
            "Utilize o Performance Mode do FL Studio para testar arranjos ao vivo estilo Ableton Clip View.",

            # Bloco Ableton Live (30)
            "Domine a Session View do Ableton Live para improvisar arranjos e testar loops em tempo real.",
            "Utilize o modo Warp em Complex Pro para esticar acapellas sem artefatos metálicos.",
            "Mapeie macros do Ableton para um único botão físico para controlar múltiplos efeitos juntos.",
            "Utilize racks de áudio nativos para criar cadeias de efeitos divididas por bandas de frequência.",
            "Utilize o Drum Buss no Ableton para dar peso imediato e controle de transientes a baterias.",
            "Configure o atalho Capture MIDI para resgatar ideias tocadas antes de gravar.",
            "Utilize o Operator para criar pads modulados e baixos limpos com baixo consumo de CPU.",
            "Use locators coloridos no Arrangement View para marcar os pontos vitais da música.",
            "Utilize o dispositivo Utility para automatizar ganho ou colocar canais instantaneamente em mono.",
            "Configure o Max for Live para utilizar dispositivos personalizados de análise espectral.",
            "Use cenas no modo Session para disparar blocos inteiros e criar progressões automáticas.",
            "Utilize o compressor nativo em modo RMS com ganho automático para avaliações rápidas.",
            "Aplique modulação LFO em parâmetros de efeitos usando o dispositivo LFO do Max for Live.",
            "Utilize Freeze e Flatten para liberar recursos de CPU ao trabalhar com plugins pesados de IA.",
            "Configure o navegador do Ableton com pastas inteligentes para localizar samples em segundos.",
            "Utilize o Glue Compressor modelado em consoles analógicos para colar elementos de bateria.",
            "Use o Groove Pool para injetar swing humano em sequências robóticas de IA.",
            "Utilize Pedal ou Saturator para adicionar sujeira analógica a leads digitais.",
            "Configure sub-rotas de envio (Sends) com reverbs e delays para manter o mix limpo.",
            "Utilize recursos avançados de sintonia e escalas no Ableton Live 12 para corrigir notas.",
            "Utilize o Gate com tempos rápidos de release para cortar ruídos estáticos em acapellas.",
            "Crie automações de panejamento em hi-hats para expandir a largura espacial da mixagem.",
            "Utilize o Tuner nativo para verificar a afinação exata de kicks e snares antes da masterização.",
            "Configure o metrónomo para emitir sons discretos que não interfiram com a audição crítica.",
            "Utilize o Multi-clip Editing para editar notas MIDI de várias faixas simultaneamente.",
            "Explore os modos de modulação analógica no dispositivo Echo para criar ambientes dub.",
            "Utilize Slice to New MIDI Track para fatiar vocais rapidamente em partes rítmicas.",
            "Configure gravação em sessão para registrar improvisações diretamente no arranjo.",
            "Utilize Limiter no canal master com teto regulado em -0.3 dB True Peak.",
            "Pratique criar um esboço completo de música em menos de 45 minutos usando templates base.",

            # Bloco Virtual DJ (30)
            "Configure o sistema de stems em tempo real no Virtual DJ para isolar vocais e beats ao vivo.",
            "Utilize o mapeamento personalizado de controladoras para atribuir hot cues a pads secundários.",
            "Ative a sincronização harmónica automática no Virtual DJ para visualizar chaves Camelot.",
            "Utilize efeitos de vídeo integrados do Virtual DJ para apresentações em telões de clubes.",
            "Configure ganho automático por software no Virtual DJ para equalizar saltos de volume.",
            "Utilize a gravação interna do Virtual DJ em FLAC ou WAV para registrar seus sets.",
            "Crie pastas virtuais inteligentes (Smart Folders) baseadas em critérios automáticos de BPM e tom.",
            "Utilize o modo scratch avançado do Virtual DJ com baixa latência em controladoras DVS.",
            "Ajuste pontos de loop automático para disparar trechos perfeitos de 4 ou 8 compassos instantaneamente.",
            "Utilize shaders de vídeo e efeitos gráficos visuais controlados pelo ritmo da batida.",
            "Configure atalhos de teclado do Virtual DJ para acesso rápido a funções de Beatjump.",
            "Utilize o sampler do Virtual DJ para disparar jingles e acapellas de efeito durante transições.",
            "Ajuste a curva do crossfader para cortes secos ideais para práticas de turntablism.",
            "Utilize a pré-escuta inteligente no navegador para conferir o drop sem alterar o deck principal.",
            "Sincronize o relógio do Virtual DJ com sistemas de iluminação DMX para shows de luzes.",
            "Utilize filtros passa-alta e passa-baixa combinados com eco para transições suaves.",
            "Ative o salvamento automático de histórico de sessões para conferir faixas tocadas posteriormente.",
            "Utilize o equalizador de 3 bandas em modo isolador para remover frequências graves antes do drop.",
            "Configure formas de onda em modo vertical paralelo para facilitar o alinhamento visual de beats.",
            "Utilize a remoção de voz do Virtual DJ em emergências para transformar faixas em instrumentais.",
            "Ajuste o tamanho do buffer de áudio para valores entre 256ms e 512ms para garantir estabilidade.",
            "Utilize listas preparadas mas mantenha flexibilidade para aceitar pedidos usando busca instantânea.",
            "Configure o Virtual DJ para iniciar em tela cheia, ocultando barras do sistema operacional.",
            "Utilize slip mode para realizar loops complexos sem perder o compasso original ao soltar o jog.",
            "Utilize colunas personalizadas no navegador para exibir ratings de estrelas e níveis de energia.",
            "Utilize efeitos de flanger em transições longas para criar tensão antes de novos drops.",
            "Mantenha drivers de placas de som externos atualizados especificamente para o Virtual DJ.",
            "Utilize o assistente de remix em tempo real para misturar acapellas de IA sobre instrumentais.",
            "Configure perfis de usuário separados caso partilhe o computador com outros DJs.",
            "Teste o sistema de som do local usando o sinal de teste integrado do Virtual DJ.",

            # Bloco Rekordbox & Pioneer DJ (30)
            "Prepare sua coleção no Rekordbox usando grids de alinhamento rigorosos para o Beat Sync.",
            "Utilize cores de Memory Cues no Rekordbox para identificar visualmente breaks e vocais.",
            "Exporte sua biblioteca para USB através do Rekordbox formatando em FAT32 ou exFAT.",
            "Utilize a funcionalidade de frases musicais do Rekordbox para analisar estruturas de faixas.",
            "Configure Hot Cues automáticos no Rekordbox 8 compassos antes de mudanças estruturais.",
            "Utilize o Lighting Mode do Rekordbox para programar sequências de luzes DMX controladas por frases.",
            "Utilize Pad FX no modo Performance do Rekordbox para criar transições rítmicas com um toque.",
            "Organize Active Intelligent Playlists no Rekordbox baseadas em critérios dinâmicos.",
            "Utilize análise Camelot no Rekordbox ativando visualização de chaves harmónicas.",
            "Edite manualmente grides de compasso deslocados em faixas com variações de tempo orgânicas.",
            "Utilize Cloud Library Sync do Rekordbox para sincronizar estúdio e portátil de palco.",
            "Configure modo quantize no Rekordbox para garantir que loops encaixem no beat grid.",
            "Utilize a coluna My Tag para criar etiquetas personalizadas de características de pista.",
            "Utilize formas de onda duplas verticais ou horizontais para conferir alinhamento espetral.",
            "Exporte relatórios de histórico em formato HTML ou CSV do Rekordbox para relatórios.",
            "Utilize a função Related Tracks para encontrar recomendações automáticas na biblioteca.",
            "Configure preferências de jog wheel no Rekordbox para ajustar sensibilidade de toque.",
            "Utilize Track Preview do Rekordbox para ouvir trechos diretamente na árvore de pastas.",
            "Faça backups regulares da base de dados do Rekordbox para evitar perda de hot cues.",
            "Utilize exportação de link para conectar o portátil diretamente aos CDJs via Pro DJ Link.",
            "Edite a tag de comentários para inserir códigos de energia ou notas de reações do público.",
            "Utilize Beat FX integrados como Echo e Roll para criar texturas rítmicas nos breakdowns.",
            "Faça edições rápidas de trechos longos (Short Edits) usando o modo Edit do Rekordbox.",
            "Configure curvas de volume de crossfader para apresentações de formato aberto.",
            "Utilize ratings por estrelas no Rekordbox para classificar o impacto real das músicas.",
            "Utilize atalhos de teclado para navegar rapidamente entre playlists e pastas.",
            "Verifique se os ficheiros de música estão no disco local e não em diretórios temporários na nuvem.",
            "Utilize conversão de tags ID3 em lote no Rekordbox para corrigir metadados de IA.",
            "Defina cores de decks personalizadas no Rekordbox para diferenciar canais de música e sampler.",
            "Pratique carregar faixas novas usando apenas o painel de pesquisa por texto do Rekordbox.",

            # Bloco Avançado, IA, Sound Design e Produção (151 a 300)
            "Combine stems geradas por inteligência artificial com vinis clássicos para mashups exclusivos.",
            "Utilize compressores multibanda no master para controlar picos de frequências desreguladas.",
            "Estude a teoria de tensão e relaxamento na construção de sets para guiar a pista de dança.",
            "Monitore a fadiga auditiva fazendo pausas e evitando volumes excessivos nos auscultadores.",
            "Utilize gravadores portáteis para capturar sons reais e transformá-los em efeitos orgânicos.",
            "Explore distorção harmônica subtil em canais de bateria para adicionar calor analógico.",
            "Mantenha firmwares de controladoras e CDJs atualizados para evitar falhas de USB.",
            "Crie edições estendidas de faixas curtas de IA adicionando intros e outros de 32 compassos.",
            "Utilize automações de filtro passa-baixa em subgrupos para criar efeitos de submersão.",
            "Teste seus masters em múltiplos dispositivos antes de tocar em clubes de grande porte.",
            "Estude géneros musicais fora da sua zona de conforto para expandir sua bagagem criativa.",
            "Utilize sidechain sutil entre guitarras e a voz principal para garantir clareza absoluta.",
            "Organize sessões semanais dedicadas exclusivamente à criação de prompts inovadores para IA.",
            "Crie um canal privado para enviar rascunhos rápidos de ideias gravadas no telemóvel.",
            "Utilize ferramentas de IA para gerar capas de EPs que combinem com a estética da sua marca.",
            "Monitore o consumo de CPU ao usar múltiplos plugins pesados de IA em projetos complexos.",
            "Pratique transição manual de BPMs distantes usando efeitos de brake e stop de vinil.",
            "Mantenha chaves de licença de softwares e plugins organizadas num documento seguro na nuvem.",
            "Utilize equalização dinâmica para atenuar frequências ressonantes agressivas em sintetizadores.",
            "Explore delays estéreo com tempos cruzados (ping-pong) para tridimensionalidade espacial.",
            "Desenvolva uma assinatura sonora única usando efeitos recorrentes em suas produções.",
            "Participe ativamente de fóruns de produção para trocar dicas sobre resolução de bugs.",
            "Utilize IA para gerar variações percussivas e aplique-as como camadas secundárias em loops.",
            "Configure templates padrão nos DAWs para iniciar novos projetos com roteamentos prontos.",
            "Monitore a integridade de ficheiros de áudio para evitar surpresas com faixas corrompidas.",
            "Utilize controle de ganho de entrada de forma rigorosa para manter níveis consistentes.",
            "Crie transições baseadas em harmónicos complementares usando a Roda Camelot.",
            "Utilize plugins de expansão estéreo com cautela para evitar cancelamento de fase mono.",
            "Estude o comportamento acústico de salas fechadas e pistas de dança comerciais.",
            "Mantenha rotina de limpeza física de controladoras, auscultadores e cabos.",
            "Utilize IA para gerar variações de acordes progressivos em faixas de techno melódico.",
            "Pratique alinhamento de frases musicais contando blocos de 8, 16 e 32 compassos.",
            "Utilize plugins de saturação de fita para colar elementos digitais de áudio.",
            "Mantenha um bloco de notas físico por perto no estúdio para anotar ideias de arranjo.",
            "Utilize quantização MIDI para corrigir pequenas imperfeições temporais em execuções.",
            "Explore o uso de ruído texturizado de vinil em baixíssimos volumes para dar nostalgia.",
            "Teste compatibilidade de faixas de IA em sistemas de som de automóveis.",
            "Utilize atalhos de teclado para alternar rapidamente entre janelas de plugins no DAW.",
            "Crie edições estendidas exclusivas para seus sets usando ferramentas de loop estrutural.",
            "Monitore temperatura e bateria de portáteis ao realizar apresentações longas ao vivo.",
            "Utilize processamento paralelo em compressores de bateria para reter transientes.",
            "Estude técnicas de mixagem em volumes baixos para garantir balanço central perfeito.",
            "Utilize IA para remover vocais e criar bases instrumentais de apoio para remixes.",
            "Mantenha cópias redundantes de sua biblioteca de música em dois discos externos.",
            "Utilize automações de pan em delays para criar movimento dinâmico panorâmico.",
            "Explore design de percussão usando ruído filtrado combinado com osciladores senoidais.",
            "Participe de masterclasses com engenheiros de som para absorver novas técnicas.",
            "Utilize IA para gerar ideias de letras conceptuais para faixas vocais experimentais.",
            "Configure seu estúdio com iluminação LED indireta em tons escuros para foco criativo.",
            "Divirta-se explorando os limites da tecnologia, transformando cada erro numa nova arte!",

            # Bloco ACE Music / ACE-Step (100)
            "Organize as tags de estilo no ACE Music de forma hierárquica, colocando primeiro o género principal e depois os instrumentos.",
            "Utilize modificadores de atmosfera e ambição na caixa de estilo (ex: club atmosphere, underground) para dar espacialidade imediata.",
            "Evite sobrecarregar o ACE com excesso de termos vagos; tags diretas e técnicas funcionam muito melhor.",
            "Especifique texturas de percussão específicas (ex: Roland TR-808 percussion) para direcionar o timbre das batidas.",
            "Combine tags de época (ex: 90s rave stabs) com elementos modernos para criar sonoridades híbridas e originais.",
            "Utilize o parâmetro de Seed numérica de forma consistente para testar variações de letras sem perder a vibe instrumental.",
            "Insira termos de mixagem na descrição de estilo (ex: sidechain compression, wide stereo image) para orientar o balanço espetral.",
            "Para faixas instrumentais puras destinadas a jogos ou trilhas, deixe o campo de letras vazio e use apenas tags de ambiente.",
            "Especifique o tipo de linha de baixo desejada com clareza (ex: acid bassline, rolling bass, deep sub-bass).",
            "Adicione tags de ritmo e groove (ex: driving rhythm, hypnotic syncopation) para dar mais movimento rítmico.",
            "Explore subgéneros underground específicos nas tags (ex: minimal deep tech, melodic house) para timbres refinados.",
            "Use descrições de texturas analógicas (ex: warm analog warmth, tape saturation) para suavizar a digitalização excessiva.",
            "Defina o clima emocional da faixa com precisão usando tags como melancholic, euphoric, dark ou cinematic.",
            "Evite usar nomes de artistas protegidos por direitos de autor nas tags do ACE Music para prevenir erros.",
            "Utilize tags de densidade instrumental (ex: sparse arrangement, wall of sound) para controlar o espaço no arranjo.",
            "Combine tags de instrumentos acústicos e sintéticos para texturas complexas e ricas em harmónicos.",
            "Especifique a velocidade e o andamento diretamente nas tags de estilo para forçar o BPM desejado.",
            "Utilize tags de timbres vocais específicos (ex: breathy female vocals, raspy male delivery) para moldar a voz.",
            "Salve seus melhores conjuntos de tags em um documento de texto para reutilizá-los como templates.",
            "Experimente gerar versões experimentais invertendo a ordem das tags de género e instrumentos.",
            "Utilize rigorosamente os marcadores estruturais oficiais suportados pelo ACE Music ([Verse], [Chorus], [Bridge]).",
            "Insira a marcação [inst] nos blocos onde deseja apenas partes instrumentais ou solos de sintetizador.",
            "Pontue suas letras com vírgulas e pontos finais estratégicos para forçar pausas naturais na respiração.",
            "Escreva versos com métrica e contagem de sílabas regulares para evitar que o modelo tropece no tempo.",
            "Evite refrões excessivamente longos; blocos de 4 a 8 linhas geram hooks mais cativantes e fáceis de memorizar.",
            "Utilize letras maiúsculas em palavras que deseja enfatizar emocionalmente na interpretação vocal.",
            "Insira marcações de efeitos vocais entre colchetes no meio das letras (ex: [whisper], [falsetto]).",
            "Divida composições complexas em partes menores e utilize o recurso de extensão do ACE Music.",
            "Verifique se o idioma selecionado nas configurações ou prompts está alinhado com o idioma da letra.",
            "Crie coros secundários colocando marcações de vozes em camadas entre parênteses logo abaixo do verso.",
            "Utilize palavras com vogais abertas em refrões para facilitar a projeção vocal limpa gerada pelo modelo.",
            "Insira pausas rítmicas nas letras usando reticências (...) para simular que o cantor segura a nota.",
            "Faça testes gerando a mesma letra com estilos totalmente opostos para ver a versatilidade do modelo.",
            "Mantenha cópias limpas das letras originais sem marcações guardadas à parte para edições rápidas.",
            "Evite caracteres especiais ou símbolos gráficos complexos no meio das letras que possam confundir a IA.",
            "Utilize repetições estratégicas de frases curtas no refrão para fixar o gancho principal da música.",
            "Testes de inclusão de pequenas falas faladas (spoken word) na introdução usando marcadores de texto.",
            "Certifique-se de que o número total de caracteres de letra respeita os limites recomendados.",
            "Analise o resultado vocal gerado e ajuste a posição das palavras caso note desalinhamento rítmico.",
            "Use o ACE Music para gerar demos rápidas de composições próprias antes de investir em estúdio físico.",
            "Anote sempre o número do Seed gerado nas suas faixas favoritas para poder replicar a estrutura.",
            "Altere apenas a letra ou uma tag de estilo de cada vez mantendo o Seed fixo para entender as mudanças.",
            "Explore diferentes versões do modelo base para comparar melhorias de nitidez e qualidade de áudio.",
            "Utilize a geração rápida do ACE Music para criar dezenas de rascunhos em poucos minutos.",
            "Salve os ficheiros gerados imediatamente em diretórios organizados no computador.",
            "Teste rodar instâncias locais do ACE-Step se tiver GPU com VRAM adequada para gerações ilimitadas.",
            "Compare resultados obtidos no ACE Music com outras plataformas abertas do mercado.",
            "Utilize o Seed fixo para criar variações de mixagem ou versões instrumentais complementares.",
            "Documente os parâmetros de duração configurados para faixas curtas ou músicas completas.",
            "Aproveite a natureza open-source da plataforma para estudar a comunidade de criadores.",
            "Limpe o histórico de gerações antigas irrelevantes para manter a interface organizada.",
            "Monitore o consumo de créditos ou restrições de planos ativos caso utilize versão web.",
            "Utilize o ACE Music para gerar trilhas sonoras de fundo dinâmicas e livres de direitos autorais.",
            "Experimente gerar efeitos sonoros e paisagens ambientes usando tags puramente descritivas.",
            "Crie playlists de referência com as melhores gerações obtidas via ACE Music.",
            "Participe de fóruns e comunidades no Reddit dedicadas ao ACE-Step para descobrir prompts secretos.",
            "Utilize o modelo para gerar bases de acordes para posterior estudo harmónico em DAW.",
            "Verifique periodicamente atualizações de pacotes e melhorias na interface web oficial.",
            "Exporte os ficheiros de áudio gerados diretamente para a nossa ferramenta de análise de BPM e Tom.",
            "Mantenha uma mentalidade aberta e experimental com a IA aberta.",
            "Passe todas as faixas geradas pelo ACE Music através de separadores de stems por IA.",
            "Aplique equalização corretiva nos vocais extraídos para remover ressonâncias metálicas nos médios.",
            "Utilize compilação de áudio no seu DAW para juntar o melhor trecho de múltiplos takes.",
            "Verifique o nível de LUFS integrado dos arquivos gerados para garantir compatibilidade.",
            "Adicione camadas de percussão analógica real por cima das baterias geradas pelo ACE.",
            "Utilize limiters transparentes de alta qualidade na masterização final de faixas do ACE.",
            "Corrija eventuais desafinações pontuais em vocais gerados usando pitch correction profissional.",
            "Crie versões estendidas (Extended Mixes) adicionando intros e outros de 32 compassos.",
            "Verifique a compatibilidade mono das faixas geradas pelo ACE para evitar cancelamento de fase.",
            "Utilize saturação suave para dar corpo e aquecer a resposta de frequência nos graves.",
            "Aplique automações de filtro passa-alta nas transições de entrada de faixas geradas.",
            "Utilize faixas instrumentais do ACE Music como bases para praticar misturas harmónicas.",
            "Organize os ficheiros exportados do ACE numa pasta dedicada no seu gestor de música.",
            "Renomear ficheiros incorporando automaticamente informações de BPM e Tom Camelot.",
            "Crie mashups exclusivos misturando acapellas geradas no ACE com instrumentais clássicos.",
            "Utilize o ACE Music para gerar trilhas de introdução para podcasts e Twitch.",
            "Monitore a integridade dos ficheiros WAV exportados para evitar perdas de dados.",
            "Pratique masterização híbrida combinando ferramentas de IA e processadores emulados.",
            "Utilize o ACE Music para expandir rapidamente sua biblioteca pessoal com remixes exclusivos.",
            "Divirta-se explorando o potencial ilimitado desta tecnologia open-source.",
            "Combine estilos geográficos distantes (ex: Celtic folk com industrial techno) nas tags.",
            "Utilize descrições de microfones vintage nas tags de estilo para influenciar a harmonia.",
            "Gere versões puramente percussivas (drum loops) para usar como ferramentas de apoio.",
            "Use o ACE Music para criar trilhas atmosféricas para RPGs e mundos virtuais.",
            "Estude a resposta dinâmica de diferentes tamanhos de blocos de letras gerados.",
            "Mantenha registo diário dos prompts mais bem-sucedidos para construir seu livro de receitas.",
            "Otimize seu fluxo de trabalho abrindo a aplicação de análise lado a lado com o ACE.",
            "Utilize técnicas de sidechain agressivo entre pads gerados pelo ACE e kicks orgânicos.",
            "Participe de desafios criativos online gerando faixas completas com prazos limitados.",
            "Experimente gerar temas com vozes corais em línguas estrangeiras ou inventadas.",
            "Faça auditoria semanal dos ficheiros gerados, descartando rascunhos fracos.",
            "Utilize o ACE Music como fonte infinita de samples e texturas para fatiar em beats.",
            "Explore criação de faixas experimentais de IDM e ambient sem refrão tradicional.",
            "Ajuste cortes de alta frequência em masters gerados caso pratos fiquem excessivamente brilhantes.",
            "Conecte conhecimento de DAW tradicional com as capacidades geradoras do ACE.",
            "Mantenha drivers de áudio e navegador atualizados para evitar falhas de execução.",
            "Crie temas personalizados para amigos e eventos usando ferramentas rápidas de letra.",
            "Explore fusão de elementos acústicos clássicos com sintetizadores modulares do ACE.",
            "Utilize análises detalhadas de energia e LUFS para validar se músicas estão prontas para clube.",
            "Viva a música sem barreiras técnicas comandando a direção artística total!"
        ]
        self.pro_tips = [f"💡 Dica Pro {i+1}: {t}" for i, t in enumerate(raw_tips)]
        self.current_tip_index = 0

        self.executor = ThreadPoolExecutor(max_workers=8)

        # Fundo em Aço Escovado Seguro
        self.bg_image_tk = self.create_brushed_steel_texture(1380, 890)
        self.bg_label = tk.Label(self, image=self.bg_image_tk, bd=0, highlightthickness=0)
        self.bg_label.place(x=0, relwidth=1, y=0, relheight=1)
        self.bind("<Configure>", self.on_window_resize)

        # Cabeçalho Principal
        self.header_frame = ctk.CTkFrame(self, fg_color="#18181d", corner_radius=12, border_width=1, border_color="#0369a1")
        self.header_frame.pack(pady=12, fill="x", padx=20)

        self.title_label = ctk.CTkLabel(self.header_frame, text="⚡VIBE KEY PRO⚡", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38bdf8")
        self.title_label.pack(side="left", padx=18, pady=12)

        self.export_btn = ctk.CTkButton(self.header_frame, text="CSV", command=self.export_csv, width=65, height=32, fg_color="#15803d", hover_color="#166534", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold"))
        self.export_btn.pack(side="right", padx=6, pady=12)

        self.save_as_btn = ctk.CTkButton(self.header_frame, text="Salvar Como", command=self.save_all_renamed_files, width=105, height=32, fg_color="#0284c7", hover_color="#0369a1", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold"))
        self.save_as_btn.pack(side="right", padx=6, pady=12)

        self.smart_mix_btn = ctk.CTkButton(self.header_frame, text="🔀 Smart Mix", command=self.open_smart_playlist, width=100, height=32, fg_color="#d97706", hover_color="#b45309", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold"))
        self.smart_mix_btn.pack(side="right", padx=6, pady=12)

        self.folder_btn = ctk.CTkButton(self.header_frame, text="Pasta", command=self.load_folder_dialog, width=80, height=32, fg_color="#27272c", hover_color="#3f3f46", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold"))
        self.folder_btn.pack(side="right", padx=6, pady=12)

        self.select_btn = ctk.CTkButton(self.header_frame, text="Add Music", command=self.load_files_dialog, width=90, height=32, fg_color="#4f46e5", hover_color="#4338ca", corner_radius=8, font=ctk.CTkFont(size=11, weight="bold"))
        self.select_btn.pack(side="right", padx=6, pady=12)

        # Barra Superior
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.pack(pady=(0, 8), fill="x", padx=20)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_table)
        self.search_entry = ctk.CTkEntry(self.toolbar_frame, textvariable=self.search_var, placeholder_text="🔍 Pesquisar música, tom, BPM...", width=260, height=34, fg_color="#18181d", border_color="#0369a1", border_width=1, corner_radius=8)
        self.search_entry.pack(side="left")

        self.tips_center_container = ctk.CTkFrame(self.toolbar_frame, fg_color="#18181d", corner_radius=8, border_width=1, border_color="#0369a1")
        self.tips_center_container.pack(side="left", expand=True, padx=10)

        self.tip_prev_btn = ctk.CTkButton(self.tips_center_container, text="◀", command=self.prev_tip, width=28, height=24, fg_color="#27272c", hover_color="#3f3f46", corner_radius=6, font=ctk.CTkFont(size=10, weight="bold"))
        self.tip_prev_btn.pack(side="left", padx=6, pady=5)

        self.top_tip_label = ctk.CTkLabel(self.tips_center_container, text=self.pro_tips[0], text_color="#38bdf8", font=ctk.CTkFont(size=11, weight="bold"))
        self.top_tip_label.pack(side="left", padx=10, pady=5)

        self.tip_next_btn = ctk.CTkButton(self.tips_center_container, text="▶", command=self.next_tip_manual, width=28, height=24, fg_color="#27272c", hover_color="#3f3f46", corner_radius=6, font=ctk.CTkFont(size=10, weight="bold"))
        self.tip_next_btn.pack(side="left", padx=6, pady=5)

        self.progress_status_label = ctk.CTkLabel(self.toolbar_frame, text="Pronto.", text_color="#38bdf8", font=ctk.CTkFont(size=12, weight="bold"))
        self.progress_status_label.pack(side="right", padx=5)

        # Container Central
        self.center_control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_control_frame.pack(pady=(0, 8), fill="x", padx=20)

        self.cover_frame = ctk.CTkFrame(self.center_control_frame, fg_color="#18181d", corner_radius=10, border_width=1, border_color="#0369a1", width=125, height=125)
        self.cover_frame.pack(side="left", padx=(0, 12))
        self.cover_frame.pack_propagate(False)

        self.cover_label = ctk.CTkLabel(self.cover_frame, text="🎵\nSem Capa", text_color="#71717a", font=ctk.CTkFont(size=11, weight="bold"))
        self.cover_label.pack(expand=True, fill="both")

        self.right_player_panel = ctk.CTkFrame(self.center_control_frame, fg_color="transparent")
        self.right_player_panel.pack(side="left", fill="x", expand=True)

        self.player_frame = ctk.CTkFrame(self.right_player_panel, fg_color="#18181d", corner_radius=10, border_width=1, border_color="#0369a1", height=54)
        self.player_frame.pack(fill="x", pady=(0, 6))

        self.shuffle_btn = ctk.CTkButton(self.player_frame, text="🔀 RM", command=self.toggle_shuffle, width=32, height=32, fg_color="#27272c", hover_color="#3f3f46", corner_radius=8, font=ctk.CTkFont(size=11))
        self.shuffle_btn.pack(side="left", padx=6, pady=11)

        self.repeat_btn = ctk.CTkButton(self.player_frame, text="🔁 LP", command=self.toggle_repeat, width=32, height=32, fg_color="#27272c", hover_color="#3f3f46", corner_radius=8, font=ctk.CTkFont(size=11))
        self.repeat_btn.pack(side="left", padx=2, pady=11)

        self.prev_btn = ctk.CTkButton(self.player_frame, text="⏮ Prev", command=self.play_previous, width=60, height=32, fg_color="#27272c", hover_color="#3f3f46", corner_radius=8, state="disabled")
        self.prev_btn.pack(side="left", padx=6, pady=11)

        self.play_btn = ctk.CTkButton(self.player_frame, text="▶ Play", command=self.toggle_play, width=70, height=32, fg_color="#0284c7", hover_color="#0369a1", corner_radius=8, state="disabled", font=ctk.CTkFont(weight="bold"))
        self.play_btn.pack(side="left", padx=3, pady=11)

        self.stop_btn = ctk.CTkButton(self.player_frame, text="⏹ Stop", command=self.stop_play, width=60, height=32, fg_color="#991b1b", hover_color="#7f1d1d", corner_radius=8, state="disabled")
        self.stop_btn.pack(side="left", padx=3, pady=11)

        self.next_btn = ctk.CTkButton(self.player_frame, text="Next ⏭", command=self.play_next, width=60, height=32, fg_color="#27272c", hover_color="#3f3f46", corner_radius=8, state="disabled")
        self.next_btn.pack(side="left", padx=3, pady=11)

        self.player_status_label = ctk.CTkLabel(self.player_frame, text="Selecione uma faixa para ouvir o preview.", text_color="#a1a1aa", font=ctk.CTkFont(size=11))
        self.player_status_label.pack(side="left", padx=10)

        self.volume_slider = ctk.CTkSlider(self.player_frame, from_=0.0, to=1.0, number_of_steps=100, width=90, command=self.change_volume, button_color="#38bdf8", progress_color="#0284c7")
        self.volume_slider.set(1.0)
        self.volume_slider.pack(side="right", padx=12)

        # Waveform Panel
        self.wave_frame = ctk.CTkFrame(self.right_player_panel, fg_color="#18181d", corner_radius=10, border_width=1, border_color="#0369a1", height=65)
        self.wave_frame.pack(fill="x")
        
        self.fig, self.ax = plt.subplots(figsize=(8, 0.65), facecolor='#18181d')
        self.ax.set_facecolor('#18181d')
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.wave_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas.get_tk_widget().bind("<Button-1>", self.on_waveform_click)
        self.draw_empty_waveform()

        self.create_table()

        # Rodapé
        self.footer_container = ctk.CTkFrame(self, fg_color="#18181d", corner_radius=10, border_width=1, border_color="#0369a1", height=44)
        self.footer_container.pack(pady=(4, 8), fill="x", padx=20)
        self.footer_container.pack_propagate(False)

        self.footer_left_controls = ctk.CTkFrame(self.footer_container, fg_color="transparent")
        self.footer_left_controls.pack(side="left", padx=10, pady=6)

        self.theme_option = ctk.CTkOptionMenu(self.footer_left_controls, values=["Dark", "Light", "System"], command=self.change_appearance_mode, width=80, height=26, font=ctk.CTkFont(size=10), fg_color="#0284c7", button_color="#0369a1", button_hover_color="#0284c7")
        self.theme_option.set("Dark")
        self.theme_option.pack(side="left", padx=3)

        self.palette_option = ctk.CTkOptionMenu(self.footer_left_controls, values=list(COLOR_PALETTES.keys()), command=self.change_color_palette, width=100, height=26, font=ctk.CTkFont(size=10), fg_color="#0284c7", button_color="#0369a1", button_hover_color="#0284c7")
        self.palette_option.set("Azul Estúdio")
        self.palette_option.pack(side="left", padx=3)

        self.rgb_btn = ctk.CTkButton(self.footer_left_controls, text="🌈 RGB", command=self.toggle_rgb_mode, width=54, height=26, fg_color="#4f46e5", hover_color="#4338ca", corner_radius=6, font=ctk.CTkFont(size=10, weight="bold"))
        self.rgb_btn.pack(side="left", padx=3)

        self.signature_label = ctk.CTkLabel(self.footer_container, text="@combarbaa / DezDesign", text_color="#38bdf8", font=ctk.CTkFont(size=10, weight="bold", underline=True), cursor="hand2")
        self.signature_label.pack(side="right", padx=14)
        self.signature_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.instagram.com/combarbaa/"))

        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_drop)
        except Exception as e:
            print(f"Drag and drop desativado: {e}")

        self.rotate_tips()

    def create_brushed_steel_texture(self, width, height):
        w, h = max(width, 100), max(height, 100)
        np.random.seed(42)
        noise_array = np.random.randint(-12, 12, (h, w, 3), dtype=np.int32)
        base_color = np.array([22, 22, 26], dtype=np.int32)
        img_array = np.clip(base_color + noise_array, 10, 45).astype(np.uint8)
        
        final_img = Image.fromarray(img_array, 'RGB')
        return ImageTk.PhotoImage(final_img)

    def on_window_resize(self, event):
        if event.widget == self and event.width > 100 and event.height > 100:
            new_img = self.create_brushed_steel_texture(event.width, event.height)
            self.bg_label.configure(image=new_img)
            self.bg_image_tk = new_img

    def extract_album_art(self, file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            img_data = None
            if ext == '.mp3':
                audio = ID3(file_path)
                for tag in audio.values():
                    if tag.FrameID.startswith('APIC'):
                        img_data = tag.data
                        break
            elif ext == '.flac':
                audio = FLAC(file_path)
                if audio.pictures:
                    img_data = audio.pictures[0].data
            if img_data:
                image = Image.open(io.BytesIO(img_data))
                image = image.resize((115, 115), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Erro capa: {e}")
        return None

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#18181d", fg="#f4f4f5", activebackground="#0284c7", activeforeground="#ffffff", font=("Segoe UI", 10))
        self.context_menu.add_command(label="▶ Reproduzir / Pausar", command=self.toggle_play)
        self.context_menu.add_command(label="🧠 Análise Espectral & Prompt Neural", command=self.open_ai_prompt_generator)
        self.context_menu.add_command(label="💾 Salvar Como...", command=self.context_save_as)
        self.context_menu.add_command(label="🏷️ Renomear Ficheiro", command=self.rename_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 Propriedades do Ficheiro", command=self.open_file_properties)
        self.context_menu.add_command(label="📁 Abrir Pasta no Explorador", command=self.open_file_folder)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.on_row_select(None)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def open_ai_prompt_generator(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.analyzed_data: return
        data = self.analyzed_data[sel[0]]

        prompt_win = ctk.CTkToplevel(self)
        prompt_win.title(f"Análise Neural: {data['filename']}")
        prompt_win.geometry("680x540")
        prompt_win.attributes("-topmost", True)

        ctk.CTkLabel(prompt_win, text="🧠 Relatório Espectral & Prompt Baseado no Hardware", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8").pack(pady=12)
        spectral_profile = "Heavy Sub-Bass Presence, Crisp Transients" if int(data['energy'].replace('%','')) > 60 else "Warm Ambient Textures, Smooth Dynamic Range"
        
        generated_prompt = (
            f"[Hardware Audio Analysis Report]\n"
            f" - Target File: {data['filename']}\n"
            f" - Measured Tempo: {data['bpm']} | Key Signature: {data['alt_key']} ({data['key']})\n"
            f" - Spectral Dynamic Profile: {spectral_profile} | Integrated Loudness: {data['lufs']}\n\n"
            f"[Generated Neural Prompt for Suno/Udio]:\n"
            f"[Style: Electronic House, {spectral_profile}, Professional Mastered Sound]\n"
            f"[Tempo: {data['bpm']} BPM | Key: {data['alt_key']}]"
        )

        txt_box = ctk.CTkTextbox(prompt_win, width=620, height=330, fg_color="#18181d", text_color="#f4f4f5", font=("Consolas", 11))
        txt_box.pack(padx=20, pady=5)
        txt_box.insert("1.0", generated_prompt)

        def copy_to_clipboard():
            prompt_win.clipboard_clear()
            prompt_win.clipboard_append(generated_prompt)
            messagebox.showinfo("Copiado!", "Relatório copiado com sucesso!")

        ctk.CTkButton(prompt_win, text="📋 Copiar Relatório Completo", command=copy_to_clipboard, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=12)

    def context_save_as(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.analyzed_data: return
        data = self.analyzed_data[sel[0]]
        old_path = data["file_path"]
        if not os.path.exists(old_path): return
        clean_bpm = data["bpm"].replace(" BPM", "")
        name, ext = os.path.splitext(data["filename"])
        default_name = f"{name} [{clean_bpm}BPM - {data['alt_key']}]{ext}"
        dest = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=ext, filetypes=[("Áudio", f"*{ext}")])
        if dest:
            try: shutil.copy2(old_path, dest)
            except Exception as e: messagebox.showerror("Erro", str(e))

    def open_file_properties(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.analyzed_data: return
        data = self.analyzed_data[sel[0]]
        prop_win = ctk.CTkToplevel(self)
        prop_win.title(f"Propriedades: {data['filename']}")
        prop_win.geometry("450x380")
        prop_win.attributes("-topmost", True)
        ctk.CTkLabel(prop_win, text="📊 Propriedades Técnicas", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8").pack(pady=15)
        info_frame = ctk.CTkFrame(prop_win, fg_color="#18181d", corner_radius=8)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        details = [("Ficheiro:", data['filename']), ("Duração:", data['time']), ("Tom:", data['key']), ("Camelot:", data['alt_key']), ("BPM:", data['bpm']), ("LUFS:", data['lufs']), ("Qualidade:", data['quality']), ("Energia:", data['energy'])]
        for label, val in details:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa", width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=11), text_color="#f4f4f5", anchor="w").pack(side="left", fill="x", expand=True)

    def open_file_folder(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.analyzed_data: return
        path = self.analyzed_data[sel[0]]["file_path"]
        if os.path.exists(path):
            folder = os.path.dirname(path)
            if sys.platform == "win32": os.startfile(folder)
            elif sys.platform == "darwin": subprocess.run(["open", folder])
            else: subprocess.run(["xdg-open", folder])

    def open_smart_playlist(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.analyzed_data:
            messagebox.showwarning("Aviso", "Selecione uma faixa base na tabela!")
            return
        base_data = self.analyzed_data[sel[0]]
        target_code = base_data['alt_key']
        compatible_codes = self.get_compatible_camelot(target_code)
        mix_win = ctk.CTkToplevel(self)
        mix_win.title(f"Smart Mix para: {base_data['filename']}")
        mix_win.geometry("780x450")
        mix_win.attributes("-topmost", True)
        ctk.CTkLabel(mix_win, text=f"🔀 Mixagem Harmónica (Tom Base: {target_code})", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8").pack(pady=12)
        cols = ("File Name", "Time", "Key", "Alt Key", "BPM")
        tree_mix = ttk.Treeview(mix_win, columns=cols, show="headings", height=12)
        for c in cols:
            tree_mix.heading(c, text=c)
            tree_mix.column(c, width=120, anchor="center")
        tree_mix.column("File Name", width=300, anchor="w")
        tree_mix.pack(fill="both", expand=True, padx=15, pady=5)
        for item_id, d in self.analyzed_data.items():
            if d['alt_key'] in compatible_codes and d['file_path'] != base_data['file_path']:
                tree_mix.insert("", "end", values=(d['filename'], d['time'], d['key'], d['alt_key'], d['bpm']))

    def change_appearance_mode(self, new_mode: str):
        self.current_theme_mode = new_mode
        ctk.set_appearance_mode(new_mode)
        is_light = (new_mode == "Light")
        card = "#ffffff" if is_light else "#18181d"
        tree_bg = "#ffffff" if is_light else "#18181d"
        tree_fg = "#18181b" if is_light else "#f4f4f5"
        for f in [self.header_frame, self.player_frame, self.wave_frame, self.footer_container, self.cover_frame, self.tips_center_container]:
            f.configure(fg_color=card)
        ttk.Style().configure("Treeview", background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg)

    def change_color_palette(self, palette_name: str):
        self.current_palette_name = palette_name
        p = COLOR_PALETTES[palette_name]
        if self.is_rgb_active: self.toggle_rgb_mode()
        
        # Atualizar textos e cores gerais
        self.title_label.configure(text_color=p["text"])
        self.progress_status_label.configure(text_color=p["text"])
        self.top_tip_label.configure(text_color=p["text"])
        self.signature_label.configure(text_color=p["text"])
        
        # Atualizar botões principais
        self.select_btn.configure(fg_color=p["accent"], hover_color=p["primary"])
        self.save_as_btn.configure(fg_color=p["primary"], hover_color=p["hover"])
        self.smart_mix_btn.configure(fg_color=p["primary"], hover_color=p["hover"])
        self.volume_slider.configure(button_color=p["text"], progress_color=p["primary"])
        
        # Atualizar os CTkOptionMenu (Menus Dropdown do Rodapé) e o botão RGB
        self.theme_option.configure(fg_color=p["primary"], button_color=p["hover"], button_hover_color=p["primary"])
        self.palette_option.configure(fg_color=p["primary"], button_color=p["hover"], button_hover_color=p["primary"])
        self.rgb_btn.configure(fg_color=p["accent"])

        for f in [self.header_frame, self.player_frame, self.wave_frame, self.footer_container, self.cover_frame, self.tips_center_container, self.search_entry]:
            try: f.configure(border_color=p["border"])
            except: pass
            
        if self.is_shuffle_active: self.shuffle_btn.configure(fg_color=p["primary"])
        if self.is_repeat_active: self.repeat_btn.configure(fg_color=p["primary"])
        if self.current_audio_y is not None: self.update_waveform_display(self.current_audio_y, progress_ratio=0.0)

    def toggle_rgb_mode(self):
        if not self.is_rgb_active:
            self.is_rgb_active = True
            self.rgb_btn.configure(fg_color="#ef4444", text="🌈 ON")
            self.run_rgb_effect()
        else:
            self.is_rgb_active = False
            if self.rgb_job: self.after_cancel(self.rgb_job)
            self.rgb_btn.configure(fg_color="#4f46e5", text="🌈 RGB")
            self.change_color_palette(self.current_palette_name)

    def run_rgb_effect(self):
        if not self.is_rgb_active: return
        colors = ["#38bdf8", "#4ade80", "#facc15", "#f87171", "#c084fc", "#ec4899"]
        c = colors[int(time.time() * 2) % len(colors)]
        self.title_label.configure(text_color=c)
        self.progress_status_label.configure(text_color=c)
        self.top_tip_label.configure(text_color=c)
        self.signature_label.configure(text_color=c)
        self.theme_option.configure(fg_color=c, button_color=c)
        self.palette_option.configure(fg_color=c, button_color=c)
        self.rgb_btn.configure(fg_color=c)
        if self.is_shuffle_active: self.shuffle_btn.configure(fg_color=c)
        if self.is_repeat_active: self.repeat_btn.configure(fg_color=c)
        for f in [self.header_frame, self.player_frame, self.wave_frame, self.footer_container, self.cover_frame, self.tips_center_container, self.search_entry]:
            try: f.configure(border_color=c)
            except: pass
        self.rgb_job = self.after(500, self.run_rgb_effect)

    def toggle_shuffle(self):
        self.is_shuffle_active = not self.is_shuffle_active
        active_color = COLOR_PALETTES[self.current_palette_name]["primary"] if not self.is_rgb_active else "#38bdf8"
        if self.is_shuffle_active: self.shuffle_btn.configure(fg_color=active_color, text_color="#ffffff")
        else: self.shuffle_btn.configure(fg_color="#27272c", text_color="#f4f4f5")

    def toggle_repeat(self):
        self.is_repeat_active = not self.is_repeat_active
        active_color = COLOR_PALETTES[self.current_palette_name]["primary"] if not self.is_rgb_active else "#38bdf8"
        if self.is_repeat_active: self.repeat_btn.configure(fg_color=active_color, text_color="#ffffff")
        else: self.repeat_btn.configure(fg_color="#27272c", text_color="#f4f4f5")

    def change_volume(self, value):
        pygame.mixer.music.set_volume(float(value))

    def filter_table(self, *args):
        query = self.search_var.get().strip().lower()
        for item_id in self.tree.get_children(): self.tree.detach(item_id)
        for item_id, data in self.analyzed_data.items():
            if not query or query in f"{data['filename']} {data['key']} {data['alt_key']} {data['bpm']} {data['lufs']}".lower():
                self.tree.reattach(item_id, "", "end")

    def next_tip(self):
        self.current_tip_index = (self.current_tip_index + 1) % len(self.pro_tips)
        active_color = COLOR_PALETTES[self.current_palette_name]["text"] if not self.is_rgb_active else "#38bdf8"
        self.top_tip_label.configure(text=self.pro_tips[self.current_tip_index], text_color=active_color)

    def next_tip_manual(self): self.next_tip()
    def prev_tip(self):
        self.current_tip_index = (self.current_tip_index - 1) % len(self.pro_tips)
        active_color = COLOR_PALETTES[self.current_palette_name]["text"] if not self.is_rgb_active else "#38bdf8"
        self.top_tip_label.configure(text=self.pro_tips[self.current_tip_index], text_color=active_color)

    def rotate_tips(self):
        def fade():
            self.next_tip()
            self.after(11000, fade)
        self.after(11000, fade)

    def draw_empty_waveform(self):
        self.ax.clear()
        self.ax.set_facecolor("#18181d")
        self.ax.axis('off')
        self.canvas.draw()

    def update_waveform_display(self, y, progress_ratio=0.0):
        self.ax.clear()
        self.ax.set_facecolor("#18181d")
        self.ax.axis('off')
        active_color = COLOR_PALETTES[self.current_palette_name]["primary"] if not self.is_rgb_active else "#38bdf8"
        samples = y[::max(1, len(y) // 1500)]
        split_idx = int(len(samples) * progress_ratio)
        if split_idx > 0: self.ax.plot(range(split_idx), samples[:split_idx], color=active_color, linewidth=1.3)
        if split_idx < len(samples): self.ax.plot(range(split_idx, len(samples)), samples[split_idx:], color="#3f3f46", linewidth=1.2, alpha=0.7)
        self.canvas.draw()

    def on_waveform_click(self, event):
        if self.current_audio_y is not None and self.current_playing_path:
            w = self.canvas.get_tk_widget().winfo_width()
            if w > 0:
                ratio = max(0.0, min(1.0, event.x / w))
                target_second = ratio * (len(self.current_audio_y) / self.current_audio_sr)
                try:
                    self.playback_start_offset_sec = target_second
                    pygame.mixer.music.load(self.current_playing_path)
                    pygame.mixer.music.play(start=target_second)
                    self.play_btn.configure(text="⏸ Pause")
                    if self.animation_job: self.after_cancel(self.animation_job)
                    self.animate_playback()
                except Exception as e: print(e)

    def create_table(self):
        self.columns = ("File Name", "Time", "Key", "Alt Key", "BPM", "LUFS", "Quality", "Intensity")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#18181d", foreground="#f4f4f5", fieldbackground="#18181d", rowheight=34, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#202025", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        table_frame = ctk.CTkFrame(self, fg_color="#18181d", corner_radius=10, border_width=1, border_color="#0369a1")
        table_frame.pack(pady=4, fill="both", expand=True, padx=20)
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        widths = [280, 70, 75, 70, 70, 80, 130, 75]
        for col, w in zip(self.columns, widths):
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=w, anchor="center")
        self.tree.column("File Name", anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        scrollbar.pack(side="right", fill="y", pady=3)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.setup_context_menu()
        self.tree.bind("<Button-3>", self.show_context_menu)

    def sort_column(self, col):
        rev = self.sort_directions.get(col, False)
        self.sort_directions[col] = not rev
        rows = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]
        rows.sort(key=lambda x: x[0], reverse=rev)
        for idx, (_, child) in enumerate(rows): self.tree.move(child, "", idx)

    def load_files_dialog(self):
        paths = filedialog.askopenfilenames(title="Escolha as músicas", filetypes=[("Áudio", "*.mp3 *.wav *.flac *.m4a")])
        if paths: self.process_file_list(paths)

    def load_folder_dialog(self):
        folder = filedialog.askdirectory(title="Selecione a Pasta")
        if folder:
            files = [os.path.join(r, f) for r, _, fs in os.walk(folder) for f in fs if f.lower().endswith(('.mp3', '.wav', '.flac', '.m4a'))]
            if files: self.process_file_list(files)

    def handle_drop(self, event):
        files = [p for p in self.tk.splitlist(event.data) if p.lower().endswith(('.mp3', '.wav', '.flac', '.m4a'))]
        if files: self.process_file_list(files)

    def process_file_list(self, files):
        for f in files:
            item_id = self.tree.insert("", "end", values=(os.path.basename(f), "--:--", "Analisando...", "...", "...", "...", "...", "..."))
            self.executor.submit(self.analyze_audio_worker, f, item_id)

    def analyze_audio_worker(self, file_path, item_id):
        try:
            y_full, sr_full = librosa.load(file_path, sr=None, mono=True)
            duration_sec = len(y_full) / sr_full
            mins, secs = int(duration_sec // 60), int(duration_sec % 60)
            time_str = f"{mins:02d}:{secs:02d}"
            y_res, sr_res = librosa.resample(y_full, orig_sr=sr_full, target_sr=22050), 22050
            tempo, _ = librosa.beat.beat_track(y=y_res, sr=sr_res)
            bpm_val = float(np.atleast_1d(tempo)[0])
            chroma = librosa.feature.chroma_cqt(y=y_res, sr=sr_res)
            chroma_mean = np.mean(chroma, axis=1)
            major = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            best, key = -1, "Unknown"
            for i in range(12):
                maj_corr = np.corrcoef(np.roll(major, i), chroma_mean)[0, 1]
                min_corr = np.corrcoef(np.roll(minor, i), chroma_mean)[0, 1]
                if maj_corr > best: best, key = maj_corr, f"{notes[i]} major"
                if min_corr > best: best, key = min_corr, f"{notes[i]} minor"
            alt_key = KEY_MAPPING.get(key, "8B")
            loudness = pysn.Meter(sr_res).integrated_loudness(y_res)
            quality = "💎 Ultra (Lossless)" if os.path.splitext(file_path)[1].lower() in ['.wav', '.flac'] else "🔥 Alto (320k)"
            rms_mean = np.mean(librosa.feature.rms(y=y_res))
            energy_val = int(min(98, max(15, (rms_mean * 350) + (np.mean(librosa.onset.onset_strength(y=y_res, sr=sr_res)) * 18))))
            cover_img = self.extract_album_art(file_path)
            self.after(0, lambda: self.update_tree_item(item_id, file_path, time_str, key, alt_key, f"{bpm_val:.1f} BPM", f"{loudness:.1f} dB", quality, f"{energy_val}%", y_res, sr_res, cover_img))
        except Exception as e: print(f"Erro worker: {e}")

    def update_tree_item(self, item_id, path, time_str, key, alt_key, bpm, lufs, qual, energy, y, sr, cover_img):
        filename = os.path.basename(path)
        self.tree.item(item_id, values=(filename, time_str, key, alt_key, bpm, lufs, qual, energy))
        self.analyzed_data[item_id] = {"file_path": path, "filename": filename, "time": time_str, "key": key, "alt_key": alt_key, "bpm": bpm, "lufs": lufs, "quality": qual, "energy": energy, "y": y, "sr": sr, "cover": cover_img}
        self.filter_table()

    def on_row_select(self, event):
        sel = self.tree.selection()
        if sel and sel[0] in self.analyzed_data:
            d = self.analyzed_data[sel[0]]
            self.current_selected_item = sel[0]
            self.current_playing_path, self.current_audio_y, self.current_audio_sr = d["file_path"], d["y"], d["sr"]
            self.playback_start_offset_sec = 0.0
            self.update_waveform_display(d["y"], progress_ratio=0.0)
            if d["cover"]:
                self.cover_label.configure(text="", image=d["cover"])
                self.cover_label.image = d["cover"]
            else:
                self.cover_label.configure(image="", text="🎵\nSem Capa")
            self.prev_btn.configure(state="normal")
            self.play_btn.configure(state="normal", text="▶ Play")
            self.stop_btn.configure(state="normal")
            self.next_btn.configure(state="normal")
            self.player_status_label.configure(text=f"Pronto: {d['filename']} | Tom: {d['alt_key']} | BPM: {d['bpm']}")
            self.highlight_harmonic_matches(d['alt_key'])

    def get_compatible_camelot(self, code):
        if not code or len(code) < 2: return [code]
        try:
            num, letter = int(code[:-1]), code[-1]
            return [code, f"{num}{'B' if letter == 'A' else 'A'}", f"{(num % 12) + 1}{letter}", f"{((num - 2) % 12) + 1}{letter}"]
        except: return [code]

    def highlight_harmonic_matches(self, target_code):
        compatible_codes = self.get_compatible_camelot(target_code)
        for item_id in self.tree.get_children():
            if item_id in self.analyzed_data:
                row_alt = self.analyzed_data[item_id]["alt_key"]
                self.tree.item(item_id, tags=('compatible',) if row_alt in compatible_codes else ('normal',))
        self.tree.tag_configure('compatible', background='#064e3b')
        self.tree.tag_configure('normal', background='#18181d')

    def play_audio(self):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(400)
                time.sleep(0.3)
            pygame.mixer.music.load(self.current_playing_path)
            pygame.mixer.music.play(start=self.playback_start_offset_sec)
            self.play_btn.configure(text="⏸ Pause")
            if self.animation_job: self.after_cancel(self.animation_job)
            self.animate_playback()
        except Exception as e: messagebox.showerror("Erro", str(e))

    def toggle_play(self):
        if self.current_playing_path:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(300)
                self.play_btn.configure(text="▶ Play")
                if self.animation_job:
                    self.after_cancel(self.animation_job)
                    self.animation_job = None
            else: self.play_audio()

    def stop_play(self):
        pygame.mixer.music.fadeout(300)
        self.play_btn.configure(text="▶ Play")
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.playback_start_offset_sec = 0.0
        if self.current_audio_y is not None: self.update_waveform_display(self.current_audio_y, progress_ratio=0.0)

    def play_next(self):
        children = self.tree.get_children()
        if not children: return
        nxt = random.choice(children) if self.is_shuffle_active else (children[(children.index(self.current_selected_item) + 1) % len(children)] if self.current_selected_item in children else children[0])
        self.tree.selection_set(nxt)
        self.on_row_select(None)
        self.play_audio()

    def play_previous(self):
        children = self.tree.get_children()
        if children and self.current_selected_item in children:
            prv = children[(children.index(self.current_selected_item) - 1) % len(children)]
            self.tree.selection_set(prv)
            self.on_row_select(None)
            self.play_audio()

    def animate_playback(self):
        if pygame.mixer.music.get_busy() and self.current_audio_y is not None:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                current_sec = self.playback_start_offset_sec + (pos_ms / 1000.0)
                dur = len(self.current_audio_y) / self.current_audio_sr
                self.update_waveform_display(self.current_audio_y, progress_ratio=min(1.0, max(0.0, current_sec / dur)))
            self.animation_job = self.after(100, self.animate_playback)
        else:
            if self.animation_job:
                self.after_cancel(self.animation_job)
                self.animation_job = None
            if self.current_playing_path:
                if self.is_repeat_active: self.play_audio()
                else: self.play_next()

    def export_csv(self):
        if not self.analyzed_data: return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["filename", "time", "key", "alt_key", "bpm", "lufs", "quality", "energy"])
                writer.writeheader()
                for d in self.analyzed_data.values(): writer.writerow({k: d[k] for k in writer.fieldnames})

    def rename_selected_file(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.analyzed_data: return
        data = self.analyzed_data[sel[0]]
        old_path = data["file_path"]
        directory, filename = os.path.split(old_path)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name} [{data['bpm'].replace(' BPM', '')}BPM - {data['alt_key']}]{ext}"
        new_path = os.path.join(directory, new_filename)
        try:
            os.rename(old_path, new_path)
            data["file_path"], data["filename"] = new_path, new_filename
            self.tree.item(sel[0], values=(new_filename, data["time"], data["key"], data["alt_key"], data["bpm"], data["lufs"], data["quality"], data["energy"]))
        except Exception as e: messagebox.showerror("Erro", str(e))

    def save_all_renamed_files(self):
        if not self.analyzed_data: return
        folder = filedialog.askdirectory(title="Selecione a Pasta")
        if folder:
            for d in self.analyzed_data.values():
                if os.path.exists(d["file_path"]):
                    name, ext = os.path.splitext(d["filename"])
                    shutil.copy2(d["file_path"], os.path.join(folder, f"{name} [{d['bpm'].replace(' BPM', '')}BPM - {d['alt_key']}]{ext}"))

if __name__ == "__main__":
    app = SongAnalyzerProApp()
    app.mainloop()
