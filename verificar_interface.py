"""Smoke test of the actual native UI. Run with an available graphical display."""
import tempfile
from pathlib import Path
from unittest.mock import patch
from bioforma.app import BioForma
from bioforma.core import DEMO_DNA
from bioforma.i18n import tr,get_language
from bioforma.reproducibility import make_record
from bioforma.references import load_reference
import time


def check_language(language):
    temp_preferences=tempfile.TemporaryDirectory()
    preferences=Path(temp_preferences.name)/'settings.json'
    app=BioForma(language=language,preferences_path=preferences)
    errors=[]
    app.report_callback_exception=lambda *e: errors.append(str(e))
    try:
        app.update()
        assert app.current_seq==DEMO_DNA
        assert len(app.dna_view.points)==60
        assert app.sim_result is not None
        assert app.tabs.tab(app.dna_tab,'text')==tr('01  Sequência + DNA 3D')
        assert app.reference_list.size()==3
        # Actual reference callbacks, both scientific interpretation and source retention.
        with patch.object(app,'confirm_discard',return_value=True):
            app.open_reference()
            app.update()
            assert len(app.current_seq)==1517
            assert app.sequence_source['accession']=='NR_027552.1'
            assert make_record(app.project_data())['results']['sequence_source_match']
            assert tr('igual à sequência importada') in app.source_caption.get()
            reference_project=app.project_data()
            app.change_language('en' if language=='pt' else 'pt')
            app.update()
            assert app.project_data()==reference_project
            assert tr('igual à sequência importada') in app.source_caption.get()
            app.change_language(language)
            app.apply_project(reference_project)
            assert app.project_data()==reference_project
            app.reference_list.selection_clear(0,'end')
            app.reference_list.selection_set(1)
            app.open_reference()
            app.update()
            assert len(app.current_seq)==5386
            assert app.sequence_source['accession']=='NC_001422.1'
            assert tr('DNA de fita simples: o visor mostra um duplex idealizado, não sua conformação nativa.') in app.source_caption.get()
            app.reference_list.selection_clear(0,'end')
            app.reference_list.selection_set(2)
            app.open_reference()
            app.update()
            assert len(app.atoms)==327
            assert app.pdb_source['accession']=='1CRN'
            assert make_record(app.project_data())['results']['pdb_source_match']
            # Exercise queue/thread/main-thread handoff without depending on the network.
            with patch('bioforma.app.fetch_ncbi',return_value=load_reference(0)):
                app.download_reference()
                deadline=time.monotonic()+5
                while app.download_poll is not None and time.monotonic()<deadline:
                    app.update();time.sleep(.01)
            assert app.download_poll is None
            assert app.sequence_source['accession']=='NR_027552.1'
            before_failure=app.project_data()
            with patch('bioforma.app.fetch_ncbi',side_effect=OSError('offline')),patch('bioforma.app.messagebox.showerror') as msg:
                app.download_reference()
                deadline=time.monotonic()+5
                while app.download_poll is not None and time.monotonic()<deadline:
                    app.update();time.sleep(.01)
                assert msg.called
            assert app.project_data()==before_failure
        app.set_editor('ATGGCTTGGTAA')
        app.mark_dirty()
        app.update_sequence()
        app.update()
        assert app.protein.get('1.0','end-1c')=='MAW*'
        app.load_pdb_demo()
        app.tabs.select(app.pdb_tab)
        app.update()
        assert len(app.pdb_view.points)==32
        app.tabs.select(app.circuit_tab)
        app.update()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'roundtrip.bioforma.json'
            with patch('bioforma.app.filedialog.asksaveasfilename',return_value=str(path)):
                assert app.save_project()
            saved=app.project_data()
            app.set_editor('ATG')
            app.update_sequence()
            with patch('bioforma.app.filedialog.askopenfilename',return_value=str(path)):
                app.open_project()
            assert app.project_data()==saved
            before=app.project_data()
            numerical=make_record(before,language)['sha256']
            draft=app.editor.get('1.0','end-1c')
            code=app.circuit_editor.get('1.0','end-1c')
            app.editor.mark_set('insert','1.3')
            cursor=app.editor.index('insert')
            other='en' if language=='pt' else 'pt'
            app.change_language(other)
            app.update()
            assert get_language()==other
            assert app.tabs.tab(app.dna_tab,'text')==tr('01  Sequência + DNA 3D')
            assert app.editor.get('1.0','end-1c')==draft
            assert app.circuit_editor.get('1.0','end-1c')==code
            assert app.editor.index('insert')==cursor
            assert app.project_data()==before
            assert make_record(app.project_data(),other)['sha256']==numerical
            # Export through the actual UI callback, including its file dialog route.
            record_path=Path(folder)/'record.json'
            with patch('bioforma.app.filedialog.asksaveasfilename',return_value=str(record_path)):
                app.export_record()
            import json
            assert json.loads(record_path.read_text(encoding='utf-8'))['sha256']==numerical
            app.dna_view.export_svg(Path(folder)/'view.svg')
            assert '<svg' in (Path(folder)/'view.svg').read_text(encoding='utf-8')
            app.circuit_editor.delete('1.0','end')
            app.circuit_editor.insert('1.0','{}')
            app.update()
            assert app.sim_result is None
            with patch('bioforma.app.messagebox.showerror') as msg:
                app.run_circuit()
                assert msg.called and app.sim_result is None
            app.set_editor('INVALID!')
            assert app.update_sequence(quiet=True) is False
            assert app.dna_view.points==[]
            assert app.protein.get('1.0','end-1c')==''
            invalid_draft=app.editor.get('1.0','end-1c')
            app.change_language(language)
            app.update()
            assert app.editor.get('1.0','end-1c')==invalid_draft
            assert app.dna_view.points==[]
            assert app.sim_result is None
            # A real insertion must remain undoable after another language change.
            app.editor.edit_separator()
            app.editor.insert('end-1c','A')
            app.editor.edit_separator()
            app.change_language(other)
            app.editor.edit_undo()
            assert app.editor.get('1.0','end-1c')==invalid_draft
        assert not errors,errors
        print('GUI OK:',language,'references, provenance, async success/error, startup, data, save/open, PT/EN switch, draft/cursor/undo, hashes, SVG, record, invalidation.')
    finally:
        app.destroy()
    app=BioForma(preferences_path=preferences)
    try:
        app.update()
        assert get_language()==other
    finally:
        app.destroy()
        temp_preferences.cleanup()


def main():
    for language in ('pt','en'):
        check_language(language)


if __name__=='__main__':
    main()
