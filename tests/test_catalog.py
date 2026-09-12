import contextlib,io,json,shutil,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from catalog import ROOT,local_asset,published_books,validate_book
from build import build

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'web',self.root/'web')
    def tearDown(self):self.temp.cleanup()
    def fixture(self,slug,status='published'):
        folder=self.root/'books'/slug;folder.mkdir(parents=True)
        for path in ['pages/cover.webp','audio/page.mp3','downloads/book.pdf']:
            p=folder/path;p.parent.mkdir(exist_ok=True);p.write_bytes(b'fixture')
        book={'schemaVersion':1,'slug':slug,'status':status,'title':'A <bright> story','description':'A test book','audience':'Ages 10-12','ageMin':10,'ageMax':12,'level':'Intermediate','genre':'Mystery','cover':'pages/cover.webp','pdf':'downloads/book.pdf','pages':[{'number':1,'title':'First page','section':'CHAPTER 01','note':'Read','tip':'Look','alt':'The first page','image':'pages/cover.webp','thumbnail':'pages/cover.webp','audio':'audio/page.mp3','duration':2,'cues':[{'start':.1,'end':1.5,'text':'Hello.'}]}]}
        (folder/'book.json').write_text(json.dumps(book));return folder,book
    def test_rejects_traversal_and_nonpublic_paths(self):
        folder,_=self.fixture('test')
        for value in ['../../secret.txt','/etc/passwd','source/private.txt','pages/../../private.txt','https://example.com/a.mp3']:
            with self.assertRaises(ValueError):local_asset(folder,value)
    def test_rejects_symlink_escape(self):
        folder,_=self.fixture('test');secret=self.root/'private.txt';secret.write_text('private');(folder/'audio/leak.txt').symlink_to(secret)
        with self.assertRaises(ValueError):local_asset(folder,'audio/leak.txt')
    def test_rejects_symlinks_to_private_source_inside_book(self):
        folder,_=self.fixture('test')
        source=folder/'source';source.mkdir();(source/'private.txt').write_text('private fixture')
        (folder/'audio/leak.txt').symlink_to(source/'private.txt')
        (folder/'audio/alias').symlink_to(source,target_is_directory=True)
        for value in ['audio/leak.txt','audio/alias/private.txt']:
            with self.assertRaises(ValueError):local_asset(folder,value)

    def test_rejects_invalid_audio_cues(self):
        folder,book=self.fixture('test');book['pages'][0]['cues'][0]['end']=3
        with self.assertRaises(ValueError):validate_book(folder,book)
    def test_drafts_are_excluded(self):
        self.fixture('published');self.fixture('draft','draft');self.assertEqual(len(published_books(self.root)),1)
    def test_rebuild_excludes_stale_output_and_private_sources(self):
        folder,_=self.fixture('one')
        source=folder/'source/illustrations';source.mkdir(parents=True)
        (source/'illustration-prompts.txt').write_text('private source fixture')
        with contextlib.redirect_stdout(io.StringIO()):build(self.root)
        (self.root/'dist/private-operator-note.txt').write_text('private fixture')
        (self.root/'dist/assets/stale.txt').write_text('private fixture')
        with contextlib.redirect_stdout(io.StringIO()):build(self.root)
        self.assertFalse((self.root/'dist/private-operator-note.txt').exists())
        self.assertFalse((self.root/'dist/assets/stale.txt').exists())
        with zipfile.ZipFile(self.root/'dist/books/one/downloads/one-ebook.zip') as z:
            self.assertNotIn('assets/stale.txt',z.namelist())
        with zipfile.ZipFile(self.root/'dist/books/one/downloads/one-book-pack.zip') as z:
            self.assertNotIn('Illustration Prompts.txt',z.namelist())

    def test_build_rejects_symlinked_output(self):
        self.fixture('one');private=self.root/'private';private.mkdir()
        (private/'keep.txt').write_text('private fixture')
        (self.root/'dist').symlink_to(private,target_is_directory=True)
        with self.assertRaises(ValueError):build(self.root)
        self.assertEqual((private/'keep.txt').read_text(),'private fixture')

    def test_multiple_books_offline_links_and_unpublishing(self):
        self.fixture('one');folder,book=self.fixture('two')
        with contextlib.redirect_stdout(io.StringIO()):build(self.root)
        html=(self.root/'dist/index.html').read_text();self.assertIn('books/one/',html);self.assertIn('books/two/',html);self.assertIn('A &lt;bright&gt; story',html)
        with zipfile.ZipFile(self.root/'dist/books/one/downloads/one-ebook.zip') as z:
            self.assertIn('assets/reader.js',z.namelist());self.assertIn('audio/page.mp3',z.namelist());self.assertNotIn('source/private.txt',z.namelist());self.assertNotIn('one-ebook.zip',z.read('index.html').decode())
        book['status']='draft';(folder/'book.json').write_text(json.dumps(book))
        with contextlib.redirect_stdout(io.StringIO()):build(self.root)
        self.assertFalse((self.root/'dist/books/two').exists())

if __name__=='__main__':unittest.main()
