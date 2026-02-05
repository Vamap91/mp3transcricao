import streamlit as st
import openai
from io import BytesIO
import tempfile
import os

# Configuração da página
st.set_page_config(
    page_title="Transcrição de Áudio - OpenAI Whisper",
    page_icon="🎙️",
    layout="wide"
)

# Título e descrição
st.title("🎙️ Transcrição de Áudio com OpenAI Whisper")
st.markdown("Faça upload de até **10 arquivos de áudio** (.mp3) para transcrição automática.")

# Sidebar para configuração da API Key
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Tentar pegar a chave do secrets primeiro
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    
    # Se não houver no secrets, permitir input manual
    if not api_key:
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Insira sua chave da API OpenAI"
        )
    else:
        st.success("✅ API Key carregada dos secrets")
    
    st.markdown("---")
    st.markdown("""
    ### 📝 Como usar:
    1. Configure sua API Key da OpenAI
    2. Faça upload de até 10 arquivos .mp3
    3. Clique em 'Transcrever Áudios'
    4. Aguarde o processamento
    """)
    
    st.markdown("---")
    st.info("💡 **Dica:** Arquivos grandes podem levar mais tempo para processar.")

# Verificar se a API key foi fornecida
if not api_key:
    st.warning("⚠️ Por favor, configure sua OpenAI API Key na barra lateral.")
    st.stop()

# Configurar o cliente OpenAI
openai.api_key = api_key

# Upload de arquivos
st.markdown("### 📤 Upload de Áudios")
uploaded_files = st.file_uploader(
    "Selecione os arquivos de áudio (.mp3)",
    type=["mp3"],
    accept_multiple_files=True,
    help="Limite: 10 arquivos por vez"
)

# Validar número de arquivos
if uploaded_files:
    if len(uploaded_files) > 10:
        st.error(f"❌ Você enviou {len(uploaded_files)} arquivos. O limite é de 10 arquivos por vez.")
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
                
                # Transcrever usando OpenAI Whisper
                with open(tmp_file_path, "rb") as audio_file:
                    transcript = openai.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                
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
            
            # Criar texto consolidado
            resultado_texto = ""
            for result in results:
                resultado_texto += f"{'='*80}\n"
                resultado_texto += f"ARQUIVO: {result['arquivo']}\n"
                resultado_texto += f"{'='*80}\n\n"
                resultado_texto += f"{result['transcricao']}\n\n\n"
            
            st.download_button(
                label="⬇️ Baixar Todas as Transcrições (.txt)",
                data=resultado_texto,
                file_name="transcricoes.txt",
                mime="text/plain",
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
