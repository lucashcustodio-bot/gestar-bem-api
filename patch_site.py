# Lê o site original e injeta o código de geração de imagens
with open("/home/claude/gestar-bem-site.html","r") as f:
    html = f.read()

# Adiciona campo de URL do backend nas configurações
cfg_field = '''
    <div class="card">
      <div class="card-title">Backend de imagens</div>
      <div class="form-row">
        <label>URL do servidor (Render)</label>
        <input type="text" id="cfg-backend" placeholder="https://gestar-bem-api.onrender.com">
        <div style="font-size:11px;color:var(--dim);margin-top:5px">
          Cole aqui a URL do seu serviço na Render após o deploy.
        </div>
      </div>
    </div>

    <div class="card">
'''
html = html.replace(
    '''    <div class="card">
      <div class="card-title">Chave de API''',
    cfg_field + '''    <div class="card">
      <div class="card-title">Chave de API'''
)

# Adiciona botão de gerar imagens nas slide-actions
html = html.replace(
    '''        <button class="btn-sm accent" onclick="salvarHistorico()">''',
    '''        <button class="btn-sm accent" onclick="salvarHistorico()">'''
)

# Adiciona o botão de gerar imagens após o botão salvar
html = html.replace(
    '''      </div>
    </div>

  </div>

  <!-- ══════════ HISTÓRICO''',
    '''        <button class="btn-sm accent" id="btn-imagens" onclick="gerarImagens()" style="display:none">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          Gerar imagens
        </button>
      </div>
    </div>

  </div>

  <!-- ══════════ HISTÓRICO'''
)

# Adiciona loadConfig para backend e função gerarImagens no JS
html = html.replace(
    "  if(cfg.sug)    document.getElementById('cfg-sug').value=cfg.sug;",
    "  if(cfg.sug)    document.getElementById('cfg-sug').value=cfg.sug;\n  if(cfg.backend) document.getElementById('cfg-backend').value=cfg.backend;"
)

html = html.replace(
    "    sug:document.getElementById('cfg-sug').value,",
    "    sug:document.getElementById('cfg-sug').value,\n    backend:document.getElementById('cfg-backend').value.trim(),"
)

# Injeta função gerarImagens antes do fechamento do script
inject = '''
async function gerarImagens(){
  var backend = cfg.backend||'';
  if(!backend){
    alert('Configure a URL do backend nas Configurações primeiro.');
    showTab('config'); return;
  }
  if(!slides.length){ alert('Gere um roteiro primeiro.'); return; }
  var btn = document.getElementById('btn-imagens');
  btn.textContent='Gerando...'; btn.disabled=true;
  try{
    var res = await fetch(backend+'/gerar',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({slides:slides, cfg:{
        nome:cfg.nome||'Gestar Bem',
        insta:cfg.insta||'@gestarbem_',
        prof:cfg.prof||"Jéssica D'Agostini"
      }})
    });
    if(!res.ok) throw new Error('Erro no servidor');
    var blob = await res.blob();
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href=url; a.download='gestar-bem-carrossel.zip'; a.click();
    URL.revokeObjectURL(url);
    showToast('Download iniciado!');
  }catch(e){
    alert('Erro ao gerar imagens. Verifique a URL do backend nas Configurações.');
  }finally{
    btn.innerHTML='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg> Gerar imagens';
    btn.disabled=false;
  }
}
'''

html = html.replace(
    "loadConfig();\nloadHistorico();",
    inject + "loadConfig();\nloadHistorico();"
)

# Mostra botão de imagens após gerar roteiro
html = html.replace(
    "  document.getElementById('preview-wrap').scrollIntoView({behavior:'smooth',block:'nearest'});",
    "  document.getElementById('preview-wrap').scrollIntoView({behavior:'smooth',block:'nearest'});\n  document.getElementById('btn-imagens').style.display='inline-flex';"
)

with open("/home/claude/index.html","w") as f:
    f.write(html)

print("Site atualizado! Tamanho:", len(html), "bytes")
