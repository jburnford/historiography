from pathlib import Path
import subprocess,concurrent.futures
P=Path(__file__).resolve().parent/'raw'
def ocr(job):
 name,page=job;stem=P/f'{name}-p{page}'
 subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','2200','-png','-singlefile',str(P/(name+'.pdf')),str(stem)],check=True,stderr=subprocess.DEVNULL)
 subprocess.run(['tesseract',str(stem)+'.png',str(stem)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 return str(stem)+'.txt'
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:res=list(pool.map(ocr,[(name,i) for name in ['goffman_presentation','williams_ordinary'] for i in range(1,11)]))
for name in ['goffman_presentation','williams_ordinary']:(P/(name+'.txt')).write_text('\n\n'.join('PDF PAGE '+str(i)+'\n'+(P/f'{name}-p{i}.txt').read_text() for i in range(1,11)))
print('OCR complete',len(res),'pages; cache is not reading extent.')
