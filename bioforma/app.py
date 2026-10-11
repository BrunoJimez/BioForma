from __future__ import annotations
from .i18n import tr

import csv
import io
import json
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .core import (BASE_COLORS, DEMO_DNA, DEFAULT_CIRCUIT, MAX_BASES, MAX_FILE_BYTES, atomic_write,
                   normalize_dna, parse_fasta, parse_genbank, parse_pdb, fasta_text,
                   sequence_stats, positional_difference, reverse_complement,
                   read_small, simulate_circuit, validate_project)
from .viewer import Viewport, dna_geometry, pdb_geometry
from . import __version__
from .guides import get_help
from .i18n import LANGUAGES, get_language, set_language, translate_existing
from .paths import load_language, save_language, log_dir, UI_FONT, MONO_FONT
from .references import catalog,load_reference,fetch_ncbi,local_source,sha256

BG, PANEL, FG, MUTED, ACCENT = '#0c121b', '#172231', '#e5eef7', '#90a7bc', '#53dfb0'


def text_area(parent, height=10):
    container=ttk.Frame(parent)
    widget=tk.Text(container, height=height, wrap='char', bg='#101824', fg=FG,
                   insertbackground=ACCENT, selectbackground='#2d5360', relief='flat',
                   padx=14,pady=12,font=(MONO_FONT,11),undo=True, maxundo=100)
    bar=ttk.Scrollbar(container,command=widget.yview)
    widget.configure(yscrollcommand=bar.set)
    bar.pack(side='right',fill='y')
    widget.pack(side='left',fill='both',expand=True)
    return container,widget


class BioForma(tk.Tk):
    def __init__(self,language=None,preferences_path=None):
        self.preferences_path=preferences_path
        set_language(language or load_language(preferences_path))
        super().__init__()
        self.title(tr('BioForma Studio {0} • bancada digital').format(__version__))
        self.geometry('1320x830')
        self.minsize(1020,700)
        self.configure(bg=BG)
        self.name='BioForma demo'
        self.baseline=DEMO_DNA
        self.current_seq=DEMO_DNA
        self.pdb_text=''
        self.sequence_source=None
        self.pdb_source=None
        self.download_queue=queue.Queue()
        self.download_poll=None
        self.atoms=[]
        self.project_path=None
        self.dirty=False
        self.loading=False
        self.pending=None
        self.sim_result=None
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.style_ui()
        self.build_ui()
        self.set_editor(DEMO_DNA)
        self.circuit_editor.insert('1.0',json.dumps(DEFAULT_CIRCUIT,indent=2))
        self.circuit_editor.edit_modified(False)
        self.run_circuit(mark=False)
        self.update_sequence()
        self.dirty=False
        self.update_title()
        self.bind('<Control-s>',lambda e:self.save_project())
        self.bind('<Control-Shift-S>',lambda e:self.save_as())
        self.bind('<Control-o>',lambda e:self.open_project())
        self.bind('<F5>',lambda e:self.update_sequence())

    def style_ui(self):
        s=ttk.Style(self)
        s.theme_use('clam')
        s.configure('.',background=BG,foreground=FG,font=(UI_FONT,10))
        s.configure('TFrame',background=BG)
        s.configure('Panel.TFrame',background=PANEL)
        s.configure('TLabel',background=BG,foreground=FG)
        s.configure('Muted.TLabel',foreground=MUTED)
        s.configure('Title.TLabel',font=(UI_FONT,23,'bold'))
        s.configure('TButton',background='#213244',foreground=FG,padding=(12,8),borderwidth=0)
        s.map('TButton',background=[('active','#2f485f')])
        s.configure('Accent.TButton',background=ACCENT,foreground='#0c211d')
        s.map('Accent.TButton',background=[('active','#89eac9')])
        s.configure('TNotebook',background=BG,borderwidth=0)
        s.configure('TNotebook.Tab',background=PANEL,foreground=MUTED,padding=(22,12))
        s.map('TNotebook.Tab',background=[('selected','#23384a')],foreground=[('selected',ACCENT)])
        s.configure('TCombobox',fieldbackground=PANEL,background=PANEL,foreground=FG)
        s.map('TCombobox',fieldbackground=[('readonly',PANEL)],foreground=[('readonly',FG)])
        s.configure('TSpinbox',fieldbackground=PANEL,foreground=FG,arrowcolor=ACCENT)
        s.configure('TEntry',fieldbackground=PANEL,foreground=FG)
        s.configure('TPanedwindow',background=BG)

    def build_ui(self):
        top=ttk.Frame(self,padding=(22,15))
        top.pack(fill='x')
        ttk.Label(top,text='BioForma',style='Title.TLabel').pack(side='left')
        self.brand_subtitle=ttk.Label(top,text=tr('STUDIO  /  {0}\nBiologia em código, modelos à vista').format(__version__),style='Muted.TLabel')
        self.brand_subtitle.pack(side='left',padx=18)
        ttk.Button(top,text=tr('Salvar projeto'),style='Accent.TButton',command=self.save_project).pack(side='right')
        ttk.Button(top,text=tr('Abrir projeto'),command=self.open_project).pack(side='right',padx=8)
        ttk.Button(top,text=tr('Exemplo inicial'),command=self.reset_demo).pack(side='right')
        self.language_choice=tk.StringVar(value=LANGUAGES[get_language()])
        language_box=ttk.Combobox(top,textvariable=self.language_choice,values=list(LANGUAGES.values()),state='readonly',width=18)
        language_box.pack(side='right',padx=12)
        language_box.bind('<<ComboboxSelected>>',lambda e:self.change_language())
        self.tabs=ttk.Notebook(self)
        self.tabs.pack(fill='both',expand=True,padx=18,pady=(0,10))
        self.dna_tab=ttk.Frame(self.tabs,padding=12)
        self.pdb_tab=ttk.Frame(self.tabs,padding=12)
        self.circuit_tab=ttk.Frame(self.tabs,padding=12)
        self.reference_tab=ttk.Frame(self.tabs,padding=16)
        self.help_tab=ttk.Frame(self.tabs,padding=16)
        for frame,label in ((self.dna_tab,tr('01  Sequência + DNA 3D')),(self.pdb_tab,tr('02  Estruturas moleculares')),
                            (self.circuit_tab,tr('03  Circuito digital')),
                            (self.reference_tab,tr('04  Referências públicas')),(self.help_tab,tr('Guia e limites'))):
            self.tabs.add(frame,text=label)
        self.build_dna()
        self.build_pdb()
        self.build_circuit()
        self.build_references()
        self.build_help()
        self.status=tk.StringVar(value=tr('Pronto • execução local • sem conta ou API'))
        ttk.Label(self,textvariable=self.status,style='Muted.TLabel',padding=(22,8)).pack(fill='x')

    def build_dna(self):
        split=ttk.Panedwindow(self.dna_tab,orient='horizontal')
        split.pack(fill='both',expand=True)
        left,right=ttk.Frame(split),ttk.Frame(split)
        split.add(left,weight=2)
        split.add(right,weight=3)
        bar=ttk.Frame(left)
        bar.pack(fill='x',pady=(0,10))
        ttk.Button(bar,text=tr('Importar DNA'),command=self.import_sequence).pack(side='left')
        ttk.Button(bar,text=tr('Exportar FASTA'),command=self.export_fasta).pack(side='left',padx=6)
        ttk.Button(bar,text=tr('Referências'),command=lambda:self.tabs.select(self.reference_tab)).pack(side='left')
        self.seq_name=tk.StringVar(value=self.name)
        ttk.Label(left,textvariable=self.seq_name,font=(UI_FONT,12,'bold'),wraplength=420).pack(anchor='w',pady=(0,6))
        self.source_caption=tk.StringVar()
        ttk.Label(left,textvariable=self.source_caption,style='Muted.TLabel',wraplength=420).pack(anchor='w',pady=(0,6))
        ttk.Label(left,text=tr('DNA 5′ → 3′  •  edite as letras; a análise acompanha'),style='Muted.TLabel').pack(anchor='w')
        frame,self.editor=text_area(left,9)
        frame.pack(fill='both',expand=True,pady=8,padx=(0,10))
        for base,col in BASE_COLORS.items():
            self.editor.tag_configure(base,foreground=col)
        self.editor.bind('<<Modified>>',self.edited)
        actions=ttk.Frame(left)
        actions.pack(fill='x')
        ttk.Button(actions,text=tr('Analisar · F5'),command=self.update_sequence).pack(side='left')
        ttk.Button(actions,text=tr('Reverso complementar'),command=self.reverse).pack(side='left',padx=5)
        ttk.Button(actions,text=tr('Fixar referência'),command=self.set_baseline).pack(side='left')
        self.metrics=tk.StringVar()
        ttk.Label(left,textvariable=self.metrics,foreground=ACCENT,wraplength=420,justify='left').pack(anchor='w',pady=(12,6))
        self.comparison=tk.StringVar()
        ttk.Label(left,textvariable=self.comparison,style='Muted.TLabel',wraplength=420).pack(anchor='w')
        opts=ttk.Frame(left)
        opts.pack(fill='x',pady=(14,5))
        ttk.Label(opts,text=tr('Tradução teórica • quadro')).pack(side='left')
        self.reading_frame=tk.StringVar(value='+1')
        box=ttk.Combobox(opts,textvariable=self.reading_frame,values=['+1','+2','+3'],state='readonly',width=4)
        box.pack(side='left',padx=8)
        box.bind('<<ComboboxSelected>>',lambda e:self.frame_changed())
        frame,self.protein=text_area(left,4)
        frame.pack(fill='x',padx=(0,10))
        self.protein.configure(state='disabled')
        ttk.Label(left,text=tr('Código genético padrão. * = parada; X = códon ambíguo.\nNão identifica genes, splicing ou expressão real.'),style='Muted.TLabel').pack(anchor='w',pady=8)
        controls=ttk.Frame(right)
        controls.pack(fill='x',pady=(0,10))
        ttk.Label(controls,text=tr('Janela: início')).pack(side='left')
        self.window_start=tk.StringVar(value='1')
        ttk.Spinbox(controls,from_=1,to=MAX_BASES,textvariable=self.window_start,width=7).pack(side='left',padx=4)
        ttk.Label(controls,text=tr('bases')).pack(side='left')
        self.window_size=tk.StringVar(value='30')
        ttk.Spinbox(controls,from_=10,to=160,textvariable=self.window_size,width=5).pack(side='left',padx=4)
        ttk.Button(controls,text=tr('Ver'),command=self.refresh_dna_view).pack(side='left',padx=4)
        ttk.Button(controls,text='SVG',command=lambda:self.export_view(self.dna_view)).pack(side='right')
        ttk.Button(controls,text=tr('Enquadrar'),command=lambda:self.dna_view.reset()).pack(side='right',padx=4)
        self.dna_view=Viewport(right)
        self.dna_view.pack(fill='both',expand=True)
        ttk.Label(right,text=tr('A verde  ·  T âmbar  ·  C azul  ·  G lilás  |  Rosa: posição diferente da referência\nHélice idealizada; os pontos representam bases, não átomos.'),style='Muted.TLabel').pack(anchor='w',pady=10)

    def build_pdb(self):
        toolbar=ttk.Frame(self.pdb_tab)
        toolbar.pack(fill='x',pady=(0,10))
        ttk.Button(toolbar,text=tr('Abrir arquivo PDB'),style='Accent.TButton',command=self.import_pdb).pack(side='left')
        ttk.Button(toolbar,text=tr('Exemplo geométrico'),command=self.load_pdb_demo).pack(side='left',padx=8)
        self.pdb_mode=tk.StringVar(value=tr('Átomos'))
        box=ttk.Combobox(toolbar,textvariable=self.pdb_mode,values=[tr('Átomos'),tr('Traço Cα')],state='readonly',width=12)
        self.pdb_modes=box
        box.pack(side='left',padx=6)
        box.bind('<<ComboboxSelected>>',lambda e:self.refresh_pdb())
        ttk.Button(toolbar,text=tr('Exportar SVG'),command=lambda:self.export_view(self.pdb_view)).pack(side='right')
        ttk.Button(toolbar,text=tr('Enquadrar'),command=lambda:self.pdb_view.reset()).pack(side='right',padx=6)
        self.pdb_summary=tk.StringVar(value=tr('Importe coordenadas de uma estrutura existente. O editor de DNA não recalcula esse arquivo.'))
        ttk.Label(self.pdb_tab,textvariable=self.pdb_summary,style='Muted.TLabel',wraplength=1050).pack(anchor='w',pady=(0,10))
        self.pdb_source_caption=tk.StringVar()
        ttk.Label(self.pdb_tab,textvariable=self.pdb_source_caption,style='Muted.TLabel',wraplength=1050).pack(anchor='w',pady=(0,8))
        self.pdb_view=Viewport(self.pdb_tab)
        self.pdb_view.pack(fill='both',expand=True)
        ttk.Label(self.pdb_tab,text=tr('PDB: primeiro modelo; conformações alternativas A/vazia. Traço Cα não representa ligações atômicas.\nCoordenadas importadas não são uma previsão de dobramento; a origem experimental ou computacional deve ser conferida na fonte.'),
                  style='Muted.TLabel').pack(anchor='w',pady=10)

    def build_circuit(self):
        split=ttk.Panedwindow(self.circuit_tab,orient='horizontal')
        split.pack(fill='both',expand=True)
        left,right=ttk.Frame(split),ttk.Frame(split)
        split.add(left,weight=2)
        split.add(right,weight=3)
        ttk.Label(left,text=tr('Um circuito que você pode programar'),font=(UI_FONT,13,'bold')).pack(anchor='w',pady=(0,8))
        ttk.Label(left,text=tr('Edite o JSON e execute. Parâmetros em unidades arbitrárias.\nOperadores: AND, OR, NOT_A ou XOR.'),style='Muted.TLabel').pack(anchor='w')
        frame,self.circuit_editor=text_area(left,15)
        frame.pack(fill='both',expand=True,pady=12,padx=(0,12))
        self.circuit_editor.bind('<<Modified>>',self.circuit_edited)
        bar=ttk.Frame(left)
        bar.pack(fill='x')
        ttk.Button(bar,text=tr('Executar simulação'),style='Accent.TButton',command=self.run_circuit).pack(side='left')
        ttk.Button(bar,text=tr('Exportar CSV'),command=self.export_circuit).pack(side='left',padx=8)
        ttk.Label(left,text=tr('dm/dt = transcription × entrada − decay_m × m\ndp/dt = translation × m − decay_p × p\nm(0) = p(0) = 0; entradas constantes.'),style='Muted.TLabel').pack(anchor='w',pady=12)
        self.circuit_summary=tk.StringVar()
        ttk.Label(right,textvariable=self.circuit_summary,foreground=ACCENT,wraplength=650).pack(anchor='w',pady=(0,10))
        self.chart=tk.Canvas(right,bg='#101824',highlightthickness=0)
        self.chart.pack(fill='both',expand=True)
        self.chart.bind('<Configure>',lambda e:self.draw_circuit())
        ttk.Label(right,text=tr('Modelo didático de produção e degradação. A célula é uma ilustração.\nA simulação não gera DNA nem prevê um organismo; portas contínuas são abstrações matemáticas.'),style='Muted.TLabel').pack(anchor='w',pady=10)

    def build_references(self):
        ttk.Label(self.reference_tab,text=tr('Dados reais, origem documentada'),font=(UI_FONT,17,'bold')).pack(anchor='w')
        ttk.Label(self.reference_tab,text=tr('Os três exemplos incluídos funcionam offline. Selecione um e abra na bancada.'),style='Muted.TLabel').pack(anchor='w',pady=8)
        split=ttk.Panedwindow(self.reference_tab,orient='horizontal')
        split.pack(fill='both',expand=True,pady=10)
        left,right=ttk.Frame(split),ttk.Frame(split)
        split.add(left,weight=2)
        split.add(right,weight=3)
        self.reference_list=tk.Listbox(left,bg=PANEL,fg=FG,selectbackground='#2d5360',font=(UI_FONT,11),relief='flat',height=8,exportselection=False)
        self.reference_list.pack(fill='both',expand=True,padx=(0,14))
        self.reference_list.bind('<<ListboxSelect>>',lambda e:self.show_reference_details())
        ttk.Button(left,text=tr('Abrir referência selecionada'),style='Accent.TButton',command=self.open_reference).pack(anchor='w',pady=12)
        frame,self.reference_details=text_area(right,14)
        frame.pack(fill='both',expand=True)
        self.reference_details.configure(state='disabled',wrap='word',font=(UI_FONT,11))
        network=ttk.Frame(self.reference_tab)
        network.pack(fill='x',pady=(10,5))
        ttk.Label(network,text=tr('NCBI • acesso com versão')).pack(side='left')
        self.accession=tk.StringVar(value='NR_027552.1')
        ttk.Entry(network,textvariable=self.accession,width=24).pack(side='left',padx=10)
        self.download_button=ttk.Button(network,text=tr('Buscar FASTA no NCBI'),command=self.download_reference)
        self.download_button.pack(side='left')
        ttk.Label(self.reference_tab,text=tr('A busca opcional envia apenas o acesso ao NCBI e requer internet. Limite: 100.000 bases.\nFASTA traz sequência; esta versão não interpreta genes ou anotações FEATURES.'),style='Muted.TLabel').pack(anchor='w',pady=5)
        self.populate_references()

    def populate_references(self):
        selected=self.reference_list.curselection()
        self.reference_list.delete(0,'end')
        for record in catalog():
            self.reference_list.insert('end',record['accession']+'  ·  '+tr(record['title']))
        self.reference_list.selection_set(selected[0] if selected else 0)
        self.show_reference_details()

    def show_reference_details(self):
        selected=self.reference_list.curselection()
        if not selected:
            return
        record=catalog()[selected[0]]
        lines=[tr(record['title']),record['accession'],record['provider'],record['record_url'],
               '',tr(record['description']),'',tr(record['molecule_note']),
               '',tr('Coleta UTC: {0}').format(record['retrieved_utc'])]
        self.reference_details.configure(state='normal')
        self.reference_details.delete('1.0','end')
        self.reference_details.insert('1.0','\n'.join(lines))
        self.reference_details.configure(state='disabled')

    def open_reference(self):
        selected=self.reference_list.curselection()
        if not selected:
            return
        try:
            self.apply_reference(load_reference(selected[0]))
        except (OSError,ValueError,UnicodeError) as exc:
            self.error(exc)

    def apply_reference(self,record):
        if record['format']=='fasta':
            if not self.confirm_discard():
                return
            self.name=record['name']
            self.seq_name.set(self.name)
            self.baseline=record['sequence']
            self.sequence_source=record['source']
            self.reading_frame.set('+1')
            self.set_editor(record['sequence'])
            self.window_start.set('1')
            self.project_path=None
            self.mark_dirty()
            self.update_sequence()
            self.tabs.select(self.dna_tab)
        else:
            self.pdb_text=record['text']
            self.atoms,_=parse_pdb(self.pdb_text)
            self.pdb_source=record['source']
            self.mark_dirty()
            self.refresh_pdb(reset=True)
            self.tabs.select(self.pdb_tab)
        self.notify(tr('Referência carregada. Origem e hashes serão preservados no projeto.'))

    def download_reference(self):
        if self.download_poll is not None:
            return
        accession=self.accession.get()
        self.download_button.configure(state='disabled')
        self.notify(tr('Consultando o NCBI…'))
        def worker():
            try:
                result=(True,fetch_ncbi(accession))
            except Exception as exc:
                result=(False,str(exc))
            self.download_queue.put(result)
        threading.Thread(target=worker,daemon=True).start()
        self.download_poll=self.after(100,self.poll_download)

    def poll_download(self):
        try:
            success,result=self.download_queue.get_nowait()
        except queue.Empty:
            self.download_poll=self.after(100,self.poll_download)
            return
        self.download_poll=None
        self.download_button.configure(state='normal')
        if success:
            self.apply_reference(result)
        else:
            self.notify(tr('A busca falhou. O projeto atual foi preservado.'))
            self.error(ValueError(tr('Falha na consulta ao NCBI: {0}').format(result)))

    def update_source_caption(self):
        source=self.sequence_source
        if not source:
            self.source_caption.set(tr('Sequência sem origem de referência documentada.'))
            return
        try:
            matches=sha256(self.get_sequence().encode('ascii'))==source.get('sequence_sha256')
        except ValueError:
            matches=False
        state=tr('igual à sequência importada') if matches else tr('alterada em relação à sequência importada')
        note=tr(source.get('molecule_note',''))
        self.source_caption.set(tr('Origem: {0} • {1}').format(source.get('label',''),state)+('\n'+note if note else ''))

    def build_help(self):
        toolbar=ttk.Frame(self.help_tab)
        toolbar.pack(fill='x',pady=(0,10))
        ttk.Button(toolbar,text=tr('Exportar registro de reprodução'),command=self.export_record).pack(side='left')
        frame,guide=text_area(self.help_tab,25)
        frame.pack(fill='both',expand=True)
        self.guide=guide
        guide.insert('1.0',get_help())
        guide.configure(state='disabled',wrap='word',font=(UI_FONT,11))

    def notify(self,text):
        self.status.set(text)

    def report_callback_exception(self,exc_type,exc_value,tb):
        import os
        import traceback
        folder=log_dir()
        try:
            folder.mkdir(parents=True,exist_ok=True)
            (folder/'erro.log').write_text(''.join(traceback.format_exception(exc_type,exc_value,tb)),encoding='utf-8')
            self.error(tr('Ocorreu um erro. Diagnóstico salvo em {0}').format(folder / 'erro.log'))
        except OSError:
            self.error(exc_value)

    def error(self,exc):
        if isinstance(exc,json.JSONDecodeError):
            text=tr('JSON inválido: {0}').format(exc.msg)
        elif isinstance(exc,OSError):
            text=tr('Falha ao acessar arquivo: {0}').format(exc)
        elif isinstance(exc,UnicodeError):
            text=tr('Arquivo de texto inválido: {0}').format(exc)
        else:
            text=str(exc)
        messagebox.showerror(tr('BioForma • verifique a entrada'),text,parent=self)

    def change_language(self,language=None,persist=True):
        selected=language or next(k for k,v in LANGUAGES.items() if v==self.language_choice.get())
        old=get_language()
        if selected==old:
            return
        # Translate existing widgets without rebuilding editors or losing undo history.
        trace_mode=self.pdb_mode.get()==tr('Traço Cα')
        circuit_caption=translate_existing(self.circuit_summary.get(),old,selected)
        set_language(selected)
        self.language_choice.set(LANGUAGES[selected])
        def visit(widget):
            if isinstance(widget,ttk.Notebook):
                for tab in widget.tabs():
                    widget.tab(tab,text=translate_existing(widget.tab(tab,'text'),old,selected))
            try:
                if not widget.cget('textvariable'):
                    widget.configure(text=translate_existing(widget.cget('text'),old,selected))
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                visit(child)
        visit(self)
        self.brand_subtitle.configure(text=tr('STUDIO  /  {0}\nBiologia em código, modelos à vista').format(__version__))
        self.pdb_mode.set(tr('Traço Cα') if trace_mode else tr('Átomos'))
        self.pdb_modes.configure(values=[tr('Átomos'),tr('Traço Cα')])
        self.guide.configure(state='normal')
        self.guide.delete('1.0','end')
        self.guide.insert('1.0',get_help())
        self.guide.configure(state='disabled')
        self.populate_references()
        self.update_sequence(quiet=True)
        self.refresh_pdb()
        self.circuit_summary.set(circuit_caption)
        if self.sim_result is not None:
            self.set_circuit_summary(self.sim_result)
        self.draw_circuit()
        self.update_title()
        self.notify(tr('Idioma alterado. Os dados e os cálculos foram preservados.'))
        if persist:
            try:
                save_language(selected,self.preferences_path)
            except OSError as exc:
                self.notify(tr('Não foi possível salvar a preferência de idioma: {0}').format(exc))

    def update_title(self):
        self.title(tr('BioForma Studio {0} • {1}').format(__version__,self.name)+(' *' if self.dirty else ''))

    def mark_dirty(self):
        if not self.loading:
            self.dirty=True
            self.update_title()

    def edited(self,event=None):
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        if self.loading:
            return
        self.mark_dirty()
        if self.pending is not None:
            self.after_cancel(self.pending)
        self.pending=self.after(450,lambda:self.update_sequence(quiet=True))

    def circuit_edited(self,event=None):
        if self.circuit_editor.edit_modified():
            self.circuit_editor.edit_modified(False)
            self.mark_dirty()
            if not self.loading:
                self.sim_result=None
                self.circuit_summary.set(tr('Código alterado: execute novamente para atualizar a simulação.'))
                self.draw_circuit()

    def set_editor(self,seq):
        old=self.loading
        self.loading=True
        self.editor.delete('1.0','end')
        self.editor.insert('1.0','\n'.join(seq[i:i+60] for i in range(0,len(seq),60)))
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.loading=old

    def get_sequence(self):
        return normalize_dna(self.editor.get('1.0','end-1c'))

    def update_sequence(self,quiet=False):
        self.update_source_caption()
        if self.pending is not None:
            self.after_cancel(self.pending)
            self.pending=None
        try:
            seq=self.get_sequence()
            stats=sequence_stats(seq,int(self.reading_frame.get()[1:])-1)
            diff=positional_difference(self.baseline,seq)
        except (ValueError,tk.TclError) as exc:
            self.metrics.set(tr('Entrada inválida • corrija o editor para visualizar.'))
            self.comparison.set('')
            self.protein.configure(state='normal')
            self.protein.delete('1.0','end')
            self.protein.configure(state='disabled')
            self.dna_view.set_model([],[],tr('DNA inválido — visualização suspensa'))
            self.notify(str(exc))
            if not quiet:
                self.error(exc)
            return False
        self.current_seq=seq
        gc=tr('indefinido') if stats['gc_percent'] is None else f'{stats["gc_percent"]:.1f}%'
        self.metrics.set(tr('{0:,} bases   •   GC {1}   •   {2} ambíguas\n{3} códons completos   •   {4} paradas   •   {5} bases finais não traduzidas').format(stats['length'], gc, stats['ambiguous'], len(stats['protein']), stats['stops'], stats['trailing_bases']))
        self.comparison.set(tr('Comparação por posição: {0} diferenças na região comum; variação de tamanho {1:+d}.\nNão é alinhamento: inserções deslocam as posições seguintes.').format(diff['mismatches'], diff['length_delta']))
        self.protein.configure(state='normal')
        self.protein.delete('1.0','end')
        self.protein.insert('1.0',stats['protein'])
        self.protein.configure(state='disabled')
        raw=self.editor.get('1.0','end-1c')
        # Highlight a bounded prefix so large sequences remain responsive.
        for base in BASE_COLORS:
            self.editor.tag_remove(base,'1.0','end')
            indices=[]
            for i,char in enumerate(raw[:6000]):
                if char.upper()==base:
                    indices.extend((f'1.0+{i}c',f'1.0+{i+1}c'))
            if indices:
                self.editor.tag_add(base,*indices)
        self.refresh_dna_view(quiet=quiet)
        self.notify(tr('Análise atualizada • GC calculado apenas sobre A/C/G/T • coloração do editor nas primeiras 6.000 posições de texto'))
        return True

    def frame_changed(self):
        self.mark_dirty()
        self.update_sequence()

    def refresh_dna_view(self,quiet=False):
        try:
            seq=self.get_sequence()
            start=int(self.window_start.get())
            size=int(self.window_size.get())
            if not 1<=start<=len(seq) or not 10<=size<=160:
                raise ValueError(tr('Início deve existir na sequência; janela deve conter de 10 a 160 bases.'))
        except (ValueError,tk.TclError) as exc:
            self.dna_view.set_model([],[],tr('Janela inválida'))
            if not quiet:
                self.error(exc)
            return
        pts,links=dna_geometry(seq,start-1,size,self.baseline)
        self.dna_view.set_model(pts,links,tr('DNA ESQUEMÁTICO  /  posições {0}–{1}  /  projeção ortográfica').format(start, min(len(seq), start + size - 1)))

    def reverse(self):
        try:
            seq=reverse_complement(self.get_sequence())
            self.set_editor(seq)
            self.mark_dirty()
            self.update_sequence()
        except ValueError as exc:
            self.error(exc)

    def set_baseline(self):
        try:
            seq=self.get_sequence()
            if not messagebox.askyesno(tr('Fixar referência'),tr('Usar a sequência atual como referência de comparação?'),parent=self):
                return
            self.baseline=seq
            self.mark_dirty()
            self.update_sequence()
        except ValueError as exc:
            self.error(exc)

    def confirm_discard(self):
        if not self.dirty:
            return True
        choice=messagebox.askyesnocancel(tr('Projeto alterado'),tr('Salvar o projeto antes de continuar?'),parent=self)
        if choice is None:
            return False
        return self.save_project() if choice else True

    def choose_record(self,records):
        if len(records)==1:
            return records[0]
        dialog=tk.Toplevel(self)
        dialog.title(tr('Escolha a sequência'))
        dialog.geometry('620x350')
        dialog.transient(self)
        lb=tk.Listbox(dialog,bg=PANEL,fg=FG,selectbackground='#35656c',font=(UI_FONT,11))
        lb.pack(fill='both',expand=True,padx=12,pady=12)
        for name,seq in records:
            lb.insert('end',tr('{0}  —  {1:,} bases').format(name[:75], len(seq)))
        lb.selection_set(0)
        selected=[]
        def accept():
            if lb.curselection():
                selected.append(records[lb.curselection()[0]])
                dialog.destroy()
        ttk.Button(dialog,text=tr('Abrir sequência selecionada'),command=accept).pack(pady=10)
        dialog.grab_set()
        self.wait_window(dialog)
        return selected[0] if selected else None

    def import_sequence(self):
        path=filedialog.askopenfilename(filetypes=[(tr('DNA (FASTA / GenBank)'),'*.fasta *.fa *.fna *.gb *.gbk *.genbank *.txt'),(tr('Todos'),'*.*')])
        if not path:
            return
        try:
            content=read_small(path)
            genbank=content.lstrip().startswith('LOCUS')
            records=parse_genbank(content) if genbank else parse_fasta(content)
            selected=self.choose_record(records)
            if not selected or not self.confirm_discard():
                return
            self.name,seq=selected
            self.sequence_source=local_source(Path(path).read_bytes(),Path(path).name,seq)
            self.seq_name.set(self.name)
            self.baseline=seq
            self.set_editor(seq)
            self.window_start.set('1')
            self.project_path=None
            self.mark_dirty()
            self.update_sequence()
            if genbank:
                self.notify(tr('GenBank importado: somente sequência ORIGIN; anotações FEATURES não foram importadas.'))
        except (OSError,UnicodeError,ValueError) as exc:
            self.error(exc)

    def export_fasta(self):
        try:
            output=fasta_text(self.name,self.get_sequence())
            path=filedialog.asksaveasfilename(defaultextension='.fasta',initialfile='sequencia.fasta',filetypes=[('FASTA','*.fasta')])
            if path:
                atomic_write(path,output)
                self.notify(tr('FASTA exportado: {0}').format(path))
        except (ValueError,OSError) as exc:
            self.error(exc)

    def import_pdb(self):
        path=filedialog.askopenfilename(filetypes=[('Protein Data Bank','*.pdb *.ent'),(tr('Todos'),'*.*')])
        if not path:
            return
        try:
            text=read_small(path)
            atoms,_=parse_pdb(text)
            self.pdb_text,self.atoms=text,atoms
            self.pdb_source=local_source(Path(path).read_bytes(),Path(path).name,text=text)
            self.refresh_pdb(reset=True)
            self.mark_dirty()
        except (OSError,UnicodeError,ValueError) as exc:
            self.error(exc)

    def load_pdb_demo(self):
        from .example import demo_pdb
        self.pdb_text=demo_pdb()
        self.pdb_source=None
        self.atoms,_=parse_pdb(self.pdb_text)
        self.pdb_mode.set(tr('Traço Cα'))
        self.refresh_pdb(reset=True)
        self.mark_dirty()

    def refresh_pdb(self,reset=False):
        source=self.pdb_source
        self.pdb_source_caption.set(tr('Origem: {0}').format(source.get('record_url') or source.get('label','')) if source else '')
        mode='trace' if self.pdb_mode.get()==tr('Traço Cα') else 'atoms'
        pts,links,total=pdb_geometry(self.atoms,mode)
        illustrative='BIOFORMA GEOMETRIC DEMO' in self.pdb_text
        label=tr('EXEMPLO GEOMÉTRICO — COORDENADAS ARTIFICIAIS') if illustrative else tr('COORDENADAS IMPORTADAS — ORIGEM A CONFERIR NO PDB')
        self.pdb_view.set_model(pts,links,label,reset=reset)
        extra=tr(' • limite de exibição atingido; apenas o prefixo é mostrado') if total>len(pts) else ''
        self.pdb_summary.set(tr('{0:,} átomos carregados • {1:,} de {2:,} pontos visíveis no modo {3}{4}. ').format(len(self.atoms), len(pts), total, self.pdb_mode.get(), extra)+
                             (tr('Não há átomos Cα compatíveis; selecione Átomos.') if self.atoms and not pts else ''))

    def run_circuit(self,mark=True):
        try:
            data=json.loads(self.circuit_editor.get('1.0','end-1c'))
            result=simulate_circuit(data)
            self.sim_result=result
            self.set_circuit_summary(result)
            self.draw_circuit()
            if mark:
                self.notify(tr('Simulação calculada por solução analítica • unidades arbitrárias • parâmetros não calibrados'))
        except (ValueError,TypeError) as exc:
            self.sim_result=None
            self.circuit_summary.set(tr('Circuito inválido. Corrija o JSON e execute novamente.'))
            self.draw_circuit()
            self.error(exc)

    def draw_circuit(self):
        c=self.chart
        c.delete('all')
        w,h=max(300,c.winfo_width()),max(300,c.winfo_height())
        if not self.sim_result:
            c.create_text(w/2,h/2,text=tr('Execute o circuito para atualizar o resultado.'),fill=MUTED,font=(UI_FONT,11))
            return
        result=self.sim_result
        points=result['points']
        left,top,right,bottom=58,45,w-26,h*.60
        ymax=max(1,max(max(m,p) for _,m,p in points))*1.1
        c.create_text(left,18,anchor='w',text=tr('EXPRESSÃO AO LONGO DO TEMPO'),fill=MUTED,font=(UI_FONT,10,'bold'))
        for i in range(5):
            y=bottom-(bottom-top)*i/4
            c.create_line(left,y,right,y,fill='#26374a')
            c.create_text(left-8,y,anchor='e',text=f'{ymax*i/4:.1f}',fill=MUTED,font=(MONO_FONT,9))
        for col,series in (('#65b5ff',1),(ACCENT,2)):
            coords=[]
            for row in points:
                coords.extend((left+(right-left)*row[0]/points[-1][0],bottom-(bottom-top)*row[series]/ymax))
            c.create_line(*coords,fill=col,width=2)
        c.create_text(left,bottom+18,anchor='w',text='0',fill=MUTED)
        c.create_text(right,bottom+18,anchor='e',text=tr('{0:g} tempo (u.a.)').format(points[-1][0]),fill=MUTED)
        c.create_text(w/2,bottom+40,text=tr('mRNA  (azul)     proteína  (verde)  •  concentração em u.a.'),fill=MUTED)
        # Illustration driven by final protein relative to this model's equilibrium.
        fraction=points[-1][2]/result['p_equilibrium'] if result['p_equilibrium'] else 0
        cy=h*.83
        green=int(50+150*min(1,max(0,fraction)))
        fill=f'#1c{green:02x}70'
        c.create_oval(left,cy-36,left+155,cy+36,outline=ACCENT,width=2,fill=fill)
        c.create_line(left+40,cy,left+60,cy-12,left+80,cy+10,left+100,cy-8,fill='#bbf8de',width=3,smooth=True)
        c.create_text(left+178,cy,anchor='w',text=tr('Célula ilustrativa\n{0:.1f}% do equilíbrio deste modelo\nCor relativa; não é previsão de fluorescência.').format(fraction * 100),fill=MUTED,font=(UI_FONT,10))

    def set_circuit_summary(self,result):
        self.circuit_summary.set(tr('Entrada efetiva: {0:.3f}  •  proteína final: {1:.3f} u.a.\nEquilíbrio teórico: m = {2:.3f}; p = {3:.3f}').format(result['input'],result['points'][-1][2],result['m_equilibrium'],result['p_equilibrium']))

    def export_record(self):
        from .reproducibility import make_record
        try:
            record=make_record(self.project_data(),get_language())
            path=filedialog.asksaveasfilename(title=tr('Exportar registro de reprodução'),defaultextension='.json',initialfile='bioforma_reproducibility.json',filetypes=[('JSON','*.json')])
            if path:
                atomic_write(path,json.dumps(record,ensure_ascii=False,indent=2)+'\n')
                self.notify(tr('Registro de reprodução exportado: {0}').format(path))
        except (OSError,ValueError,TypeError) as exc:
            self.error(exc)

    def export_circuit(self):
        if self.sim_result is None:
            self.error(ValueError(tr('Execute um circuito válido antes de exportar.')))
            return
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='simulacao.csv',filetypes=[('CSV','*.csv')])
        if not path:
            return
        buffer=io.StringIO()
        writer=csv.writer(buffer)
        writer.writerow(['time_au','mrna_au','protein_au'])
        writer.writerows(self.sim_result['points'])
        try:
            atomic_write(path,buffer.getvalue())
            self.notify(tr('Simulação exportada: {0}').format(path))
        except OSError as exc:
            self.error(exc)

    def export_view(self,view):
        path=filedialog.asksaveasfilename(defaultextension='.svg',initialfile='bioforma_vista.svg',filetypes=[('SVG','*.svg')])
        if path:
            try:
                view.export_svg(path)
                self.notify(tr('Vista exportada: {0}').format(path))
            except OSError as exc:
                self.error(exc)

    def project_data(self):
        return validate_project({'format':'bioforma','version':1,'name':self.name,
                                 'sequence':self.get_sequence(),'baseline':self.baseline,
                                 'frame':int(self.reading_frame.get()[1:])-1,
                                 'pdb_text':self.pdb_text,
                                 'sequence_source':self.sequence_source,'pdb_source':self.pdb_source,
                                 'circuit':json.loads(self.circuit_editor.get('1.0','end-1c'))})

    def save_project(self):
        try:
            data=self.project_data()
            serialized=json.dumps(data,ensure_ascii=False,indent=2)
            if len(serialized.encode('utf-8')) > MAX_FILE_BYTES:
                raise ValueError(tr('O projeto excede 12 MB. Use um PDB menor para poder salvar e reabrir nesta versão.'))
            path=self.project_path or filedialog.asksaveasfilename(defaultextension='.bioforma.json',initialfile='meu_projeto.bioforma.json',filetypes=[(tr('Projeto BioForma'),'*.bioforma.json')])
            if not path:
                return False
            atomic_write(path,serialized)
            self.project_path=path
            self.dirty=False
            self.update_title()
            self.notify(tr('Projeto salvo: {0}').format(path))
            return True
        except (OSError,ValueError,TypeError) as exc:
            self.error(exc)
            return False

    def save_as(self):
        previous=self.project_path
        self.project_path=None
        if not self.save_project():
            self.project_path=previous

    def open_project(self):
        path=filedialog.askopenfilename(filetypes=[(tr('Projeto BioForma'),'*.bioforma.json *.json')])
        if not path:
            return
        try:
            data=validate_project(json.loads(read_small(path)))
            if not self.confirm_discard():
                return
            self.apply_project(data)
            self.project_path=path
            self.notify(tr('Projeto aberto: {0}').format(path))
        except (OSError,UnicodeError,ValueError,TypeError) as exc:
            self.error(exc)

    def apply_project(self,data):
        self.loading=True
        try:
            self.name=data['name']
            self.sequence_source=data.get('sequence_source')
            self.pdb_source=data.get('pdb_source')
            self.seq_name.set(self.name)
            self.baseline=data['baseline']
            self.reading_frame.set('+'+str(data.get('frame',0)+1))
            self.set_editor(data['sequence'])
            self.window_start.set('1')
            self.pdb_text=data['pdb_text']
            self.atoms=parse_pdb(self.pdb_text)[0] if self.pdb_text else []
            self.circuit_editor.delete('1.0','end')
            self.circuit_editor.insert('1.0',json.dumps(data['circuit'],indent=2))
            self.circuit_editor.edit_reset()
            self.circuit_editor.edit_modified(False)
            self.update_sequence()
            self.refresh_pdb(reset=True)
            self.run_circuit(mark=False)
            self.dirty=False
            self.update_title()
        finally:
            self.loading=False

    def reset_demo(self):
        if not self.confirm_discard():
            return
        self.apply_project({'name':'BioForma demo','sequence':DEMO_DNA,'baseline':DEMO_DNA,
                            'pdb_text':'','circuit':DEFAULT_CIRCUIT,'frame':0})
        self.project_path=None

    def close(self):
        if self.confirm_discard():
            self.destroy()

    def destroy(self):
        for callback in (self.pending,self.download_poll):
            if callback is not None:
                try:
                    self.after_cancel(callback)
                except tk.TclError:
                    pass
        self.pending=self.download_poll=None
        super().destroy()



def main(language=None):
    BioForma(language=language).mainloop()
