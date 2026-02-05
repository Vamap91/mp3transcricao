import streamlit as st
import openai
from io import BytesIO
import tempfile
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Transcrição de Áudio - OpenAI Whisper",
    page_icon="🎙️",
    layout="wide"
)

# Título e descrição
st.title("🎙️ Transcrição de Áudio com OpenAI Whisper")
st.markdown("Faça upload de até **80 arquivos de áudio** (.mp3) para transcrição automática.")

# Sidebar com informações
with st.sidebar:
    st.header("⚙️ Configurações")
    st.success("✅ API Key configurada")
    
    st.markdown("---")
    st.markdown("""
    ### 📝 Como usar:
    1. Faça upload de até 80 arquivos .mp3
    2. Clique em 'Transcrever Áudios'
    3. Aguarde o processamento
    4. Baixe as transcrições em TXT ou PDF
    """)
    
    st.markdown("---")
    st.info("💡 **Dica:** Processamento de muitos arquivos pode levar tempo. Aguarde a conclusão.")

def gerar_pdf(resultados):
    """Gera PDF com as transcrições dos áudios"""
    buffer = BytesIO()
    
    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    titulo_style = ParagraphStyle(
        'TituloCustom',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#1f77b4',
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Estilo para nome do arquivo
    arquivo_style = ParagraphStyle(
        'ArquivoCustom',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#2ca02c',
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Estilo para o texto da transcrição
    transcricao_style = ParagraphStyle(
        'TranscricaoCustom',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=15,
        leading=14
    )
    
    # Criar conteúdo
    story = []
    
    # Título principal
    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    titulo = Paragraph(
        f"<b>Transcrições de Áudio</b><br/><font size=10>Gerado em {data_hora}</font>",
        titulo_style
    )
    story.append(titulo)
    story.append(Spacer(1, 0.5*cm))
    
    # Linha separadora
    story.append(Paragraph("<hr width='100%'/>", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Adicionar cada transcrição
    for idx, resultado in enumerate(resultados, 1):
        # Nome do arquivo
        nome_arquivo = Paragraph(
            f"<b>{idx}. {resultado['arquivo']}</b>",
            arquivo_style
        )
        story.append(nome_arquivo)
        
        # Transcrição
        transcricao_texto = resultado['transcricao'].replace('\n', '<br/>')
        transcricao = Paragraph(transcricao_texto, transcricao_style)
        story.append(transcricao)
        
        # Separador entre arquivos (exceto no último)
        if idx < len(resultados):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("<hr width='80%'/>", styles['Normal']))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer

# Carregar API Key do Streamlit Cloud Secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    openai.api_key = api_key
except Exception as e:
    st.error(f"❌ Erro ao carregar API Key: {str(e)}")
    st.stop()

# Upload de arquivos
st.markdown("### 📤 Upload de Áudios")
uploaded_files = st.file_uploader(
    "Selecione os arquivos de áudio (.mp3)",
    type=["mp3"],
    accept_multiple_files=True,
    help="Limite: 80 arquivos por vez"
)

# Validar número de arquivos
if uploaded_files:
    if len(uploaded_files) > 80:
        st.error(f"❌ Você enviou {len(uploaded_files)} arquivos. O limite é de 80 arquivos por vez.")
        st.stop()
    
    st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
    
    # Exibir lista de arquivos
    with st.expander("📋 Arquivos carregados", expanded=True):
        for i, file in enumerate(uploaded_files, 1):
            file_size = file.size / (1024 * 1024)  # Converter para MB
            st.write(f"{i}. **{file.name}** - {file_size:.2f} MB")
    
    st.markdown("---")
    
    # Botão para iniciar transcrição
    if st.button("🎯 Transcrever Áudios", type="primary", use_container_width=True):
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Container para resultados
        st.markdown("### 📄 Resultados das Transcrições")
        
        results = []
        
        # Processar cada arquivo
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                # Atualizar status
                status_text.text(f"Processando: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")
                
                # Criar arquivo temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Transcrever usando OpenAI Whisper (API v0.28)
                with open(tmp_file_path, "rb") as audio_file:
                    response = openai.Audio.transcribe(
                        model="whisper-1",
                        file=audio_file
                    )
                    transcript = response["text"]
                
                # Limpar arquivo temporário
                os.unlink(tmp_file_path)
                
                # Armazenar resultado
                results.append({
                    "arquivo": uploaded_file.name,
                    "transcricao": transcript
                })
                
                # Atualizar progresso
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            except Exception as e:
                st.error(f"❌ Erro ao processar {uploaded_file.name}: {str(e)}")
                results.append({
                    "arquivo": uploaded_file.name,
                    "transcricao": f"ERRO: {str(e)}"
                })
        
        # Limpar status
        status_text.empty()
        progress_bar.empty()
        
        # Exibir resultados
        if results:
            st.success(f"✅ Transcrição concluída! {len(results)} arquivo(s) processado(s).")
            
            for idx, result in enumerate(results, 1):
                with st.expander(f"📝 {idx}. {result['arquivo']}", expanded=True):
                    st.markdown("**Transcrição:**")
                    st.text_area(
                        label="Texto transcrito",
                        value=result['transcricao'],
                        height=150,
                        key=f"transcricao_{idx}",
                        label_visibility="collapsed"
                    )
            
            # Opção de download dos resultados
            st.markdown("---")
            st.markdown("### 💾 Download dos Resultados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Criar texto consolidado
                resultado_texto = ""
                for result in results:
                    resultado_texto += f"{'='*80}\n"
                    resultado_texto += f"ARQUIVO: {result['arquivo']}\n"
                    resultado_texto += f"{'='*80}\n\n"
                    resultado_texto += f"{result['transcricao']}\n\n\n"
                
                st.download_button(
                    label="📄 Baixar em TXT",
                    data=resultado_texto,
                    file_name="transcricoes.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Gerar PDF
                pdf_buffer = gerar_pdf(results)
                
                st.download_button(
                    label="📕 Baixar em PDF",
                    data=pdf_buffer,
                    file_name="transcricoes.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

else:
    st.info("👆 Faça upload de arquivos de áudio para começar.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Desenvolvido com Streamlit 🎈 | Powered by OpenAI Whisper 🤖
    </div>
    """,
    unsafe_allow_html=True
)
